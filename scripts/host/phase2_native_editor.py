#!/usr/bin/env python3
"""Validate installed editor on one cold disposable native overlay, no NIC."""
from datetime import datetime,timezone
import argparse,fcntl,hashlib,json,os,re,shutil,subprocess,sys,uuid
from pathlib import Path
import boot_test as boot
from phase2_native_report import decode
from phase2_native_glycin import compressed_payload
import phase2_vm
import vm
ROOT=phase2_vm.ROOT;WORK=phase2_vm.WORK
CONTEXT=ROOT/'.local/phase2/native-editor-runtime-1'
def run(args,**kwargs):return subprocess.run(args,check=True,text=True,**kwargs)
def main():
    global CONTEXT
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--context',default='native-editor-runtime-1');parser.add_argument('--driver-generation',choices=['1','2','3'],default='1');args=parser.parse_args()
    assert re.fullmatch(r'native-editor-runtime-[1-9][0-9]?',args.context)
    CONTEXT=ROOT/'.local/phase2'/args.context
    assert not CONTEXT.exists(),'Reconcile native operation before any repeat'
    assert not subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip(),'Commit reviewed inputs before native boot'
    assert shutil.disk_usage(ROOT).free>=100*1024**3+512*1024**2
    lock=open(vm.VM/'native-boot-test.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);boot.refuse_running_tests()
    probe=(ROOT/'scripts/host/phase2-native-editor-probe.py').read_bytes()
    code="from pathlib import Path\nimport fcntl,hashlib,json,subprocess\nsubprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)\nlock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)\nassert not list(Path('/var/log/toddy/build').glob('*.running.json'))\nversions={'gnome-text-editor':'50.1-1+toddy1','gtk':'4.22.4-1+toddy9','mutter':'50.4-1+toddy1','libspelling':'0.4.11-1+toddy1','editorconfig':'0.12.11-1+toddy1'}\nartifacts={}\ndef sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()\nfor name,version in versions.items():\n assert subprocess.check_output(['chroot','/mnt/lfs','dpkg-query','-W','-f=${Version}',name],text=True)==version\n r=json.loads(Path('/var/log/toddy/packages',name+'_'+version+'_amd64.json').read_text());assert r['installed']\n for n,row in r['payload'].items():\n  if 'sha256' in row:assert sha(Path('/mnt/lfs')/n.lstrip('/'))==row['sha256'];artifacts[n]=row['sha256']\nfor step in ['b02-gnome-text-editor-install','b02-editor-schema-union-install']:\n r=json.loads(Path('/var/log/toddy/build',step+'.success.json').read_text());assert r['recipe_exit']==r['postcheck_exit']==0\nlog=Path('/var/log/toddy/phase2');assert (log/'editor-native-driver-1.exit').read_text().strip()=='0'\nsource=Path('/mnt/lfs/sources/phase2/inputs/editor-native-driver-1');work=Path('/mnt/lfs/sources/phase2/work/editor-native-driver-1');prepared=json.loads((log/'editor-native-driver-prepared-1.json').read_text())\nfor n,digest in prepared['inputs'].items():assert sha(source/n)==digest\nassert sha(source/'native_editor_session.py')==sha(Path('/opt/toddy-build/scripts/build/phase2/native_editor_session.py'))\nassert sha(source/'native-editor-driver.c')==sha(Path('/opt/toddy-build/scripts/build/phase2/native-editor-driver.c'))\ndriver=work/'native-editor-driver.so';proof=json.loads((work/'driver-result.json').read_text());assert proof['compile_exit']==0 and proof['test_only'] and not proof['installed_to_system'] and sha(driver)==proof['sha256']\nrecord={'versions':versions,'artifacts':artifacts,'driver_library':str(driver).removeprefix('/mnt/lfs'),'driver_sha256':sha(driver),'session_script':str(source/'native_editor_session.py').removeprefix('/mnt/lfs'),'session_script_sha256':sha(source/'native_editor_session.py'),'builder_boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'native_kernel_expected':'7.1.8-toddy'}\nfixture=Path('/mnt/lfs/sources/phase2/native-fixtures/editor-1');descriptor=fixture/'accepted.json';part=fixture/'accepted.part'\nraw=(json.dumps(record,sort_keys=True,indent=2)+'\\n').encode()\nassert len(raw)<512*1024 and not part.exists()\nif descriptor.exists():\n assert descriptor.is_file() and not descriptor.is_symlink() and descriptor.stat().st_uid==0 and descriptor.stat().st_nlink==1 and not descriptor.stat().st_mode&0o222\n assert descriptor.read_bytes()==raw\nelse:\n assert not fixture.exists();fixture.mkdir()\n with part.open('xb') as f:f.write(raw);f.flush();__import__('os').fsync(f.fileno())\n part.chmod(0o444);part.rename(descriptor);fixture.chmod(0o555)\nprint(json.dumps({'manifest':str(descriptor).removeprefix('/mnt/lfs'),'manifest_sha256':sha(descriptor),'manifest_bytes':len(raw)}))\n"
    code=code.replace('editor-native-driver-1','editor-native-driver-'+args.driver_generation).replace('editor-native-driver-prepared-1','editor-native-driver-prepared-'+args.driver_generation).replace('native-fixtures/editor-1','native-fixtures/editor-'+args.driver_generation)
    accepted=subprocess.run(phase2_vm.ssh_args()+['python3 -'],input=code.encode(),capture_output=True,check=True)
    accepted_record=json.loads(accepted.stdout)
    assert probe.count(b'ACCEPTED = None')==1
    probe=probe.replace(b'ACCEPTED = None',('ACCEPTED = '+repr(accepted_record)).encode())
    payload_probe=compressed_payload(probe)
    CONTEXT.mkdir()
    state={'scope':'Actual installed editor/private Wayland GTK action/screenshot validation only; no complete GNOME/login/G2/physical acceptance',
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
    identity=phase2_vm.backing_identity(source);state['source_identity']=identity;save()
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
              'toddy.boot-probe':payload_probe}
    qemu=boot.qemu_arguments('bios',payloads)
    qemu+=['-serial','file:/work/native-evidence.log']
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
    evidence=(CONTEXT/'native-evidence.log').read_text(errors='strict')
    report,summary,recovered=decode(evidence)
    state['dedicated_evidence_sha256']=hashlib.sha256(evidence.encode()).hexdigest()
    (CONTEXT/'native-report.json').write_text(json.dumps(report,indent=2)+'\n')
    state['recovered_protocol_markers']=recovered
    state.update(phase='native-report-recorded',summary=summary,backing_unchanged=True,
                 native_selected_passed=summary['all_selected_exits_zero'],builder_restart='pending explicit reconciliation of real container/image/cache state')
    save()
    assert summary['all_selected_exits_zero'],'Native selected failures retained; do not mark qualified'


if __name__=='__main__':main()
