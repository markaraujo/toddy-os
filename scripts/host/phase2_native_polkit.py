#!/usr/bin/env python3
"""Qualify five original Polkit drivers on one cold disposable native overlay, no NIC."""
from datetime import datetime,timezone
import fcntl,hashlib,json,os,shutil,subprocess,sys,uuid
from pathlib import Path
import boot_test as boot
from phase2_native_report import decode
import phase2_vm
import vm
ROOT=phase2_vm.ROOT;WORK=phase2_vm.WORK
CONTEXT=ROOT/'.local/phase2/native-polkit-suite-runtime-1'
def run(args,**kwargs):return subprocess.run(args,check=True,text=True,**kwargs)
def main():
    assert len(sys.argv)==1
    assert not CONTEXT.exists(),'Reconcile native operation before any repeat'
    assert not subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip(),'Commit reviewed inputs before native boot'
    assert shutil.disk_usage(ROOT).free>=100*1024**3+512*1024**2
    lock=open(vm.VM/'native-boot-test.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);boot.refuse_running_tests()
    probe=(ROOT/'scripts/host/phase2-native-polkit-probe.py').read_bytes()
    code="""from pathlib import Path
import fcntl,hashlib,json,subprocess
subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
r=json.loads(Path('/var/log/toddy/phase2/polkit-native-prepare-1.json').read_text());assert r['state']=='complete'
fixture=Path(r['fixture']);manifest=fixture/'accepted.json';assert hashlib.sha256(manifest.read_bytes()).hexdigest()==r['manifest_sha256']
for p,row in json.loads(manifest.read_text())['files'].items():
 if 'sha256' in row:assert hashlib.sha256((Path('/mnt/lfs')/p).read_bytes()).hexdigest()==row['sha256']
 else:assert str((Path('/mnt/lfs')/p).readlink())==row['symlink']
assert (Path('/var/log/toddy/phase2/polkit-full-1.exit').read_text().strip())=='0'
print(json.dumps({'fixture_manifest_sha256':r['manifest_sha256'],'fixture_files':r['artifact_files'],'builder_boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'target_serial':'TODDY-LFS-TARGET','native_kernel_expected':'7.1.8-toddy'}))
"""
    accepted=subprocess.run(phase2_vm.ssh_args()+['python3 -'],input=code.encode(),capture_output=True,check=True)
    accepted_record=json.loads(accepted.stdout)
    CONTEXT.mkdir()
    state={'scope':'Disposable native Phase2 Polkit original-suite probe only; no B02/G2 completion or physical/graphical acceptance',
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
    with (CONTEXT/'builder-stop.log').open('x') as log:
        state['phase']='stopping-builder';save()
        run([sys.executable,str(ROOT/'scripts/host/phase2_vm.py'),'stop'],stdout=log,stderr=subprocess.STDOUT)
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
    report,summary,recovered=decode(serial)
    (CONTEXT/'native-report.json').write_text(json.dumps(report,indent=2)+'\n')
    state['recovered_protocol_markers']=recovered
    state.update(phase='native-report-recorded',summary=summary,backing_unchanged=True,
                 native_selected_passed=summary['all_selected_exits_zero'],builder_restart='pending explicit reconciliation of real container/image/cache state')
    save()
    assert summary['all_selected_exits_zero'],'Native selected failures retained; do not mark qualified'


if __name__=='__main__':main()
