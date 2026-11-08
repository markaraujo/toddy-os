#!/usr/bin/env python3
"""One cold Phase2 overlay boot with ephemeral credentials and no networking."""
import base64
from datetime import datetime,timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import uuid
import zlib

import boot_test as boot
import phase2_vm
import vm

ROOT=phase2_vm.ROOT
WORK=phase2_vm.WORK
CONTEXT=ROOT/'.local/phase2/native-bwrap-runtime-1'


def run(args,**kwargs):
    return subprocess.run(args,check=True,text=True,**kwargs)


def main():
    global CONTEXT
    assert sys.argv[1:] in [[],['--cold-followup'],['--cold-layout-followup']]
    layout_followup=sys.argv[1:]==['--cold-layout-followup']
    followup=bool(sys.argv[1:])
    previous=None
    if followup:
        if layout_followup:CONTEXT=ROOT/'.local/phase2/native-bwrap-runtime-2'
        previous=json.loads((CONTEXT/'result.json').read_text())
        previous_context=CONTEXT
        CONTEXT=ROOT/'.local/phase2'/('native-bwrap-runtime-3' if layout_followup else 'native-bwrap-runtime-2')
        assert previous['phase'] in ['native-stopped','native-report-recorded'] and not previous['container_final_state']['Running']
        assert previous['container_final_state']['ExitCode']==0
        info=json.loads(subprocess.check_output(['docker','inspect',previous['container_id']],text=True))[0]
        assert (info['Config'].get('Labels') or {}).get('toddy.boot-test')==previous['run_id'] and not info['State']['Running']
        assert phase2_vm.backing_identity(WORK/'lfs-target.qcow2')==previous['source_identity']
        assert not subprocess.check_output(['docker','ps','-q','--filter','name=^/'+phase2_vm.NAME+'$'],text=True).strip()
    assert not CONTEXT.exists(),'Reconcile prior native runtime receipt; never replay'
    assert not subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip(),'Commit reviewed inputs before native boot'
    assert shutil.disk_usage(ROOT).free>=100*1024**3+512*1024**2
    lock=open(vm.VM/'native-boot-test.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    boot.refuse_running_tests()
    probe_text=(ROOT/'scripts/host/phase2-native-bwrap-probe.py').read_text()
    consumer=(ROOT/'scripts/build/phase2/bubblewrap-probe.py').read_text()
    assert probe_text.count('CONSUMER_SOURCE = None')==1
    probe_text=probe_text.replace('CONSUMER_SOURCE = None','CONSUMER_SOURCE = '+repr(consumer))
    if layout_followup:
        report=json.loads((previous_context/'native-report.json').read_text())
        reused=[{k:r[k] for k in ['name','exit']} for r in report['runs'] if r['name'] in ['test-specifying-pidns.sh','test-specifying-userns.sh']]
        assert len(reused)==2 and all(r['exit']==0 for r in reused)
        proof={'kernel':report['kernel'],'binary_sha256':report['binary_sha256'],'runs':reused,'report_sha256':previous['summary']['report_sha256']}
        assert probe_text.count('REUSED_NATIVE_PROOF = None')==1
        probe_text=probe_text.replace('REUSED_NATIVE_PROOF = None','REUSED_NATIVE_PROOF = '+repr(proof))
    probe=probe_text.encode()
    code='''from pathlib import Path
import json,hashlib,subprocess
subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
assert Path('/var/log/toddy/phase2/bubblewrap-native-probe-5.exit').read_text().strip()=='1'
assert json.loads(Path('/var/log/toddy/phase2/builder-bwrap-userns-profile.json').read_text())['state']=='removed-after-bounded-failure'
r=json.loads(Path('/var/log/toddy/build/b02-hwdata-install.success.json').read_text());assert r['recipe_exit']==r['postcheck_exit']==0
p=Path('/mnt/lfs/sources/phase2/work/bubblewrap-1/compile/bwrap');assert hashlib.sha256(p.read_bytes()).hexdigest()=='f36c7341c009446dc7b79417d6baaa9ec583eccb9690553dd53e4d22ac19869f'
print(json.dumps({'builder_boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'bwrap_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'target_serial':'TODDY-LFS-TARGET','native_kernel_expected':'7.1.8-toddy'}))
'''
    if followup:
        accepted_record=previous['accepted']
    else:
        accepted=subprocess.run(phase2_vm.ssh_args()+['python3 -'],input=code.encode(),capture_output=True,check=True)
        accepted_record=json.loads(accepted.stdout)
    CONTEXT.mkdir()
    state={'scope':'Disposable native Phase2 runtime namespace probe only; no B02/G2 completion or physical/graphical acceptance',
           'commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
           'started_utc':datetime.now(timezone.utc).isoformat(),
           'controller_pid':os.getpid(),'controller_boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
           'controller_start_ticks':Path('/proc/self/stat').read_text().split()[21],
           'accepted':accepted_record,'probe_sha256':hashlib.sha256(probe).hexdigest(),'phase':'prepared'}
    def save():
        part=CONTEXT/'result.json.part';assert not part.exists()
        part.write_text(json.dumps(state,indent=2)+'\n');part.replace(CONTEXT/'result.json')
        print(json.dumps({'phase':state['phase'],'context':str(CONTEXT)}),flush=True)
    save()
    if not followup:
        with (CONTEXT/'builder-stop.log').open('x') as log:
            state['phase']='stopping-builder';save()
            run([sys.executable,str(ROOT/'scripts/host/phase2_vm.py'),'stop'],stdout=log,stderr=subprocess.STDOUT)
    else:
        state['cold_followup_of']=previous_context.name
    assert subprocess.check_output(['docker','ps','-q','--filter','name=^/'+phase2_vm.NAME+'$'],text=True).strip()==''
    state['phase']='builder-stopped';save()
    source=WORK/'lfs-target.qcow2';assert source.is_file() and not source.is_symlink()
    identity=phase2_vm.backing_identity(source);state['source_identity']=identity
    image=subprocess.check_output(['docker','image','inspect','--format','{{.Id}}',vm.IMAGE],text=True).strip()
    run_id=uuid.uuid4().hex
    common=['--user',f'{os.getuid()}:{os.getgid()}','--cap-drop=ALL','--security-opt=no-new-privileges','--network=none','--read-only',
            '-v',f'{vm.VM}:/vm:ro','-v',f'{CONTEXT}:/work']
    with (CONTEXT/'prepare.log').open('x') as log:
        run(['docker','run','--rm',*common,image,'qemu-img','check','/vm/phase2/lfs-target.qcow2'],stdout=log,stderr=subprocess.STDOUT)
        run(['docker','run','--rm',*common,image,'qemu-img','create','-f','qcow2','-F','qcow2','-b','/vm/phase2/lfs-target.qcow2','/work/target.qcow2'],stdout=log,stderr=subprocess.STDOUT)
    unit=(ROOT/'scripts/host/boot-probe.service').read_bytes().replace(b'TimeoutStartSec=180',b'TimeoutStartSec=360')
    payloads={'systemd.extra-unit.toddy-boot-probe.service':unit,
              'systemd.unit-dropin.multi-user.target':(ROOT/'scripts/host/boot-probe.target.conf').read_bytes(),
              'toddy.boot-probe':probe}
    qemu=boot.qemu_arguments('bios',payloads)
    qemu[qemu.index('-cpu')+1]='host';qemu[qemu.index('-smp')+1]='4';qemu[qemu.index('-m')+1]='4096'
    name='toddy-b02-native-'+run_id[:12]
    command=['docker','create','--name',name,'--label','toddy.boot-test='+run_id,*common,
             '--device','/dev/kvm','--group-add',str(Path('/dev/kvm').stat().st_gid),'--memory','5g','--cpus','4',image,*qemu]
    cid=subprocess.check_output(command,text=True).strip()
    state.update(phase='native-running',container_id=cid,container_name=name,run_id=run_id,command=command);save()
    with (CONTEXT/'qemu.log').open('x') as log:run(['docker','start',cid],stdout=log,stderr=subprocess.STDOUT)
    try:
        waited=subprocess.run(['docker','wait',cid],capture_output=True,text=True,timeout=600)
        (CONTEXT/'docker-wait.json').write_text(json.dumps({'exit':waited.returncode,'stdout':waited.stdout,'stderr':waited.stderr},indent=2)+'\n')
        waited.check_returncode();assert waited.stdout.strip()=='0','QEMU runtime exit nonzero'
    finally:
        state['container_final_state']=boot.stop_owned_container(cid,run_id)
        state['phase']='native-stopped';save()
    assert phase2_vm.backing_identity(source)==identity,'Read-only backing identity changed; do not restart builder'
    serial=(CONTEXT/'serial.log').read_text(errors='replace')
    summaries=[];chunks={}
    for line in serial.splitlines():
        if 'TODDY_B02_RUNTIME_DATA ' in line:
            i,data=line.split('TODDY_B02_RUNTIME_DATA ',1)[1].split(' ',1);i=int(i)
            assert i not in chunks or chunks[i]==data;chunks[i]=data
        if 'TODDY_B02_RUNTIME_RESULT ' in line:summaries.append(json.loads(line.split('TODDY_B02_RUNTIME_RESULT ',1)[1]))
    assert summaries and all(r==summaries[0] for r in summaries),'No consistent actual native report; no success inference'
    summary=summaries[0];assert set(chunks)==set(range(summary['chunks']))
    raw=zlib.decompress(base64.b64decode(''.join(chunks[i] for i in range(len(chunks))),validate=True))
    assert len(raw)<4*1024**2 and hashlib.sha256(raw).hexdigest()==summary['report_sha256']
    report=json.loads(raw);(CONTEXT/'native-report.json').write_text(json.dumps(report,indent=2)+'\n')
    state.update(phase='native-report-recorded',summary=summary,backing_unchanged=True,
                 native_selected_passed=summary['all_selected_exits_zero'],builder_restart='pending explicit reconciliation of real container/image/cache state')
    save()
    assert summary['all_selected_exits_zero'],'Native selected failures retained; do not mark qualified'


if __name__=='__main__':main()
