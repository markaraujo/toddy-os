#!/usr/bin/env python3
"""Cold native image/sandbox test using only disposable target overlays."""
from datetime import datetime,timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import uuid

import boot_test as boot
from phase2_native_report import decode
import phase2_vm
import vm

ROOT=phase2_vm.ROOT
WORK=phase2_vm.WORK


def run(args,**kwargs):
    return subprocess.run(args,check=True,text=True,**kwargs)


def main():
    assert len(sys.argv)==1
    context=ROOT/'.local/phase2/native-glycin-runtime-1'
    assert not context.exists(),'Reconcile existing native operation; never replay'
    assert not subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip()
    assert shutil.disk_usage(ROOT).free>=100*1024**3+512*1024**2
    lock=open(vm.VM/'native-boot-test.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    boot.refuse_running_tests()
    consumer=(ROOT/'scripts/build/phase2/glycin-native-consumer.py').read_text()
    body=(ROOT/'scripts/host/phase2-native-glycin-probe.py').read_text()
    assert body.count('CONSUMER_SOURCE = None')==1
    probe=body.replace('CONSUMER_SOURCE = None','CONSUMER_SOURCE = '+repr(consumer)).encode()
    code='''from pathlib import Path
import fcntl,hashlib,json,subprocess
subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
f=open('/var/log/toddy/build/build.lock','a');fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
for name in ['glycin-1','glycin-tests-1']:assert Path('/var/log/toddy/phase2',name+'.exit').read_text().strip()=='0'
p=Path('/var/log/toddy/phase2/glycin-native-fixture.json');r=json.loads(p.read_text())
assert r['state']=='complete'
for name,row in r['payload'].items():
 q=Path(r['fixture'])/name
 if 'sha256' in row:assert hashlib.sha256(q.read_bytes()).hexdigest()==row['sha256']
 elif 'link' in row:assert str(q.readlink())==row['link']
print(json.dumps({'builder_boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
 'fixture_receipt_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
 'fixture_payload_sha256':hashlib.sha256(json.dumps(r['payload'],sort_keys=True).encode()).hexdigest()}))
'''
    accepted=subprocess.run(phase2_vm.ssh_args()+['python3 -'],input=code.encode(),capture_output=True,check=True)
    context.mkdir()
    state={'scope':'Native Glycin selected image tests only; GNOME/B02/G2 remain pending',
           'commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
           'started_utc':datetime.now(timezone.utc).isoformat(),'controller_pid':os.getpid(),
           'controller_boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
           'controller_start_ticks':Path('/proc/self/stat').read_text().split()[21],
           'accepted':json.loads(accepted.stdout),'probe_sha256':hashlib.sha256(probe).hexdigest(),'phase':'prepared'}
    def save():
        part=context/'result.json.part';assert not part.exists()
        part.write_text(json.dumps(state,indent=2)+'\n');part.replace(context/'result.json')
        print(json.dumps({'phase':state['phase'],'context':str(context)}),flush=True)
    save()
    with (context/'builder-stop.log').open('x') as log:
        state['phase']='stopping-builder';save()
        run([sys.executable,str(ROOT/'scripts/host/phase2_vm.py'),'stop'],stdout=log,stderr=subprocess.STDOUT)
    assert not subprocess.check_output(['docker','ps','-q','--filter','name=^/'+phase2_vm.NAME+'$'],text=True).strip()
    state['phase']='builder-stopped';save()
    source=WORK/'lfs-target.qcow2';assert source.is_file() and not source.is_symlink()
    identity=phase2_vm.backing_identity(source);state['source_identity']=identity
    image=subprocess.check_output(['docker','image','inspect','--format','{{.Id}}',vm.IMAGE],text=True).strip()
    run_id=uuid.uuid4().hex
    common=['--user',f'{os.getuid()}:{os.getgid()}','--cap-drop=ALL','--security-opt=no-new-privileges',
            '--network=none','--read-only','-v',f'{vm.VM}:/vm:ro','-v',f'{context}:/work']
    with (context/'prepare.log').open('x') as log:
        run(['docker','run','--rm',*common,image,'qemu-img','check','/vm/phase2/lfs-target.qcow2'],stdout=log,stderr=subprocess.STDOUT)
        run(['docker','run','--rm',*common,image,'qemu-img','create','-f','qcow2','-F','qcow2',
             '-b','/vm/phase2/lfs-target.qcow2','/work/target.qcow2'],stdout=log,stderr=subprocess.STDOUT)
    unit=(ROOT/'scripts/host/boot-probe.service').read_bytes().replace(b'TimeoutStartSec=180',b'TimeoutStartSec=540')
    payloads={'systemd.extra-unit.toddy-boot-probe.service':unit,
              'systemd.unit-dropin.multi-user.target':(ROOT/'scripts/host/boot-probe.target.conf').read_bytes(),
              'toddy.boot-probe':probe}
    qemu=boot.qemu_arguments('bios',payloads)
    qemu[qemu.index('-cpu')+1]='host';qemu[qemu.index('-smp')+1]='4';qemu[qemu.index('-m')+1]='4096'
    name='toddy-b02-native-'+run_id[:12]
    command=['docker','create','--name',name,'--label','toddy.boot-test='+run_id,*common,
             '--device','/dev/kvm','--group-add',str(Path('/dev/kvm').stat().st_gid),
             '--memory','5g','--cpus','4',image,*qemu]
    cid=subprocess.check_output(command,text=True).strip()
    state.update(phase='native-running',container_id=cid,container_name=name,run_id=run_id,command=command);save()
    with (context/'qemu.log').open('x') as log:run(['docker','start',cid],stdout=log,stderr=subprocess.STDOUT)
    try:
        waited=subprocess.run(['docker','wait',cid],capture_output=True,text=True,timeout=600)
        (context/'docker-wait.json').write_text(json.dumps({'exit':waited.returncode,'stdout':waited.stdout,'stderr':waited.stderr},indent=2)+'\n')
        waited.check_returncode();assert waited.stdout.strip()=='0'
    finally:
        state['container_final_state']=boot.stop_owned_container(cid,run_id);state['phase']='native-stopped';save()
    assert phase2_vm.backing_identity(source)==identity
    report,summary,recovered=decode((context/'serial.log').read_text(errors='replace'))
    (context/'native-report.json').write_text(json.dumps(report,indent=2)+'\n')
    state.update(phase='native-report-recorded',summary=summary,recovered_protocol_markers=recovered,
                 backing_unchanged=True,native_selected_passed=summary['all_selected_exits_zero'])
    save();assert summary['all_selected_exits_zero'],'Native test failures retained, not qualified'


if __name__=='__main__':main()
