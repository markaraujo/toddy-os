#!/usr/bin/env python3
"""Cold native image/sandbox test using only disposable target overlays."""
from datetime import datetime,timezone
import base64
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import uuid
import zlib

import boot_test as boot
from phase2_native_report import decode
import phase2_vm
import vm

ROOT=phase2_vm.ROOT
WORK=phase2_vm.WORK


def run(args,**kwargs):
    return subprocess.run(args,check=True,text=True,**kwargs)


def compressed_payload(probe):
    assert isinstance(probe,bytes) and len(probe)<=65536
    packed=base64.b64encode(zlib.compress(probe,9)).decode()
    bootstrap=('import base64,zlib,hashlib\n'
               'd=zlib.decompressobj()\n'
               f'raw=d.decompress(base64.b64decode({packed!r},validate=True),65537)\n'
               'assert len(raw)<=65536 and d.eof and not d.unused_data\n'
               f'assert hashlib.sha256(raw).hexdigest()=={hashlib.sha256(probe).hexdigest()!r}\n'
               'exec(compile(raw,"toddy-native-glycin","exec"))\n').encode()
    assert len(base64.b64encode(bootstrap))<=16384
    return bootstrap


def main():
    assert sys.argv[1:] in [[],['--dds-followup'],['--dds-transport-followup'],['--dds-rebuild-followup']]
    followup=bool(sys.argv[1:]);previous=None;reused=None
    transport_followup=sys.argv[1:]==['--dds-transport-followup']
    rebuild_followup=sys.argv[1:]==['--dds-rebuild-followup']
    context=ROOT/'.local/phase2'/('native-glycin-runtime-4' if rebuild_followup else 'native-glycin-runtime-3' if transport_followup else 'native-glycin-runtime-2' if followup else 'native-glycin-runtime-1')
    if followup:
        old=context.parent/'native-glycin-runtime-1'
        previous=json.loads((old/'result.json').read_text());report=json.loads((old/'native-report.json').read_text())
        assert previous['phase']=='native-report-recorded' and previous['backing_unchanged'] and not previous['native_selected_passed']
        assert hashlib.sha256(json.dumps(report,sort_keys=True).encode()).hexdigest()==previous['summary']['report_sha256']
        container=json.loads(subprocess.check_output(['docker','inspect',previous['container_id']],text=True))[0]
        assert not container['State']['Running'] and container['State']['ExitCode']==0
        assert (container['Config'].get('Labels') or {}).get('toddy.boot-test')==previous['run_id']
        if not rebuild_followup:assert phase2_vm.backing_identity(WORK/'lfs-target.qcow2')==previous['source_identity']
        failed=[r for r in report['runs'] if r['exit']!=0];assert len(failed)==1 and failed[0]['name']=='tests'
        assert 'UnknownImageFormat("image/vnd.ms-dds"' in failed[0]['stderr']
        assert '10 passed; 1 failed;' in failed[0]['stdout']
        if not rebuild_followup:assert not subprocess.check_output(['docker','ps','-q','--filter','name=^/'+phase2_vm.NAME+'$'],text=True).strip()
        reused={'kernel':report['kernel'],'test_artifacts':report['test_artifacts'],
                'report_sha256':previous['summary']['report_sha256'],
                'runs':[{k:r[k] for k in ['name','exit']} for r in report['runs'] if r['exit']==0],
                'original_image_driver_passed_cases':10,'original_image_driver_failed_case':'color',
                'original_driver_failure_retained':True}
        if transport_followup:
            partial=context.parent/'native-glycin-runtime-2'
            partial_state=json.loads((partial/'result.json').read_text())
            assert partial_state['phase']=='builder-stopped' and 'container_id' not in partial_state
            assert not (partial/'serial.log').exists()
            assert 'Unexpectedly large SMBIOS test payload' in (ROOT/'.local/phase2/glycin-native-runtime-2-controller.log').read_text()
            # The previous attempt created only an unused disposable overlay.
            # It never created or started a VM; retain it, create a new context.
            ids=subprocess.check_output(['docker','ps','-aq','--filter','label=toddy.boot-test'],text=True).split()
            containers=json.loads(subprocess.check_output(['docker','inspect',*ids],text=True)) if ids else []
            assert all(all(m['Source']!=str(partial) for m in c['Mounts']) for c in containers)
    assert not context.exists(),'Reconcile existing native operation; never replay'
    assert not subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip()
    assert shutil.disk_usage(ROOT).free>=100*1024**3+512*1024**2
    lock=open(vm.VM/'native-boot-test.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    boot.refuse_running_tests()
    consumer=(ROOT/'scripts/build/phase2/glycin-native-consumer.py').read_text()
    body=(ROOT/'scripts/host/phase2-native-glycin-probe.py').read_text()
    assert body.count('CONSUMER_SOURCE = None')==1
    body=body.replace('CONSUMER_SOURCE = None','CONSUMER_SOURCE = '+repr(consumer))
    compat=(ROOT/'scripts/build/phase2/glycin_mime_compat.py').read_text()
    assert body.count('MIME_COMPAT_SOURCE = None')==1 and body.count('REUSED_NATIVE_PROOF = None')==1
    body=body.replace('MIME_COMPAT_SOURCE = None','MIME_COMPAT_SOURCE = '+repr(compat))
    body=body.replace('REUSED_NATIVE_PROOF = None','REUSED_NATIVE_PROOF = '+repr(reused))
    if rebuild_followup:
        assert body.count("FIXTURE_NAME = 'glycin-1'")==1
        body=body.replace("FIXTURE_NAME = 'glycin-1'","FIXTURE_NAME = 'glycin-2'")
    probe=body.encode()
    bootstrap=compressed_payload(probe)
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
    if followup and not rebuild_followup:accepted_record=previous['accepted']
    else:
        if rebuild_followup:
            code=code.replace('glycin-native-fixture.json','glycin-native-fixture-dds.json')
            code+="\nassert Path('/var/log/toddy/phase2/glycin-dds-1.exit').read_text().strip()=='0'\n"
        accepted=subprocess.run(phase2_vm.ssh_args()+['python3 -'],input=code.encode(),capture_output=True,check=True)
        accepted_record=json.loads(accepted.stdout)
    context.mkdir()
    state={'scope':'Native Glycin selected image tests only; GNOME/B02/G2 remain pending',
           'commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
           'started_utc':datetime.now(timezone.utc).isoformat(),'controller_pid':os.getpid(),
           'controller_boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
           'controller_start_ticks':Path('/proc/self/stat').read_text().split()[21],
           'accepted':accepted_record,'probe_sha256':hashlib.sha256(probe).hexdigest(),
           'payload_sha256':hashlib.sha256(bootstrap).hexdigest(),'phase':'prepared'}
    if followup:state['cold_followup_of']='native-glycin-runtime-1'
    def save():
        part=context/'result.json.part';assert not part.exists()
        part.write_text(json.dumps(state,indent=2)+'\n');part.replace(context/'result.json')
        print(json.dumps({'phase':state['phase'],'context':str(context)}),flush=True)
    save()
    if not followup or rebuild_followup:
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
              'toddy.boot-probe':bootstrap}
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
