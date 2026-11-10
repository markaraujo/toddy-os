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
CONTEXT=ROOT/'.local/phase2/native-tecla-runtime-1'
def run(args,**kwargs):return subprocess.run(args,check=True,text=True,**kwargs)
def main():
    global CONTEXT
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--context',default='native-tecla-runtime-1');args=parser.parse_args()
    assert re.fullmatch(r'native-tecla-runtime-[1-9][0-9]?',args.context)
    CONTEXT=ROOT/'.local/phase2'/args.context
    assert not CONTEXT.exists(),'Reconcile native operation before any repeat'
    assert not subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip(),'Commit reviewed inputs before native boot'
    assert shutil.disk_usage(ROOT).free>=100*1024**3+512*1024**2
    lock=open(vm.VM/'native-boot-test.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);boot.refuse_running_tests()
    probe=(ROOT/'scripts/host/phase2-native-tecla-probe.py').read_bytes()
    code="from pathlib import Path\nimport fcntl,hashlib,json,subprocess,os\nsubprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)\nlock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);assert not list(Path('/var/log/toddy/build').glob('*.running.json'))\ndef sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()\nartifacts={}\nfor name,version in {'gtk':'4.22.4-1+toddy9','mutter':'50.4-1+toddy1','libadwaita':'1.9.3-1+toddy1'}.items():\n assert subprocess.check_output(['chroot','/mnt/lfs','dpkg-query','-W','-f=${Version}',name],text=True)==version\n r=json.loads(Path('/var/log/toddy/packages',name+'_'+version+'_amd64.json').read_text());assert r['installed']\n for relative,row in r['payload'].items():\n  if 'sha256' in row:assert sha(Path('/mnt/lfs')/relative.lstrip('/'))==row['sha256'];artifacts[relative]=row['sha256']\nl=Path('/var/log/toddy/phase2');assert (l/'tecla-1.exit').read_text().strip()=='1' and (l/'tecla-collect-2.exit').read_text().strip()=='0'\ns=Path('/mnt/lfs/sources/phase2/inputs/tecla-50.0');w=Path('/mnt/lfs/sources/phase2/work/tecla-1');prepared=json.loads((s/'toddy-prepared.json').read_text());assert prepared['source_sha256']=='2542acb24850082e0ccf6aa17af9651db71d22f0e233fdbf5ed0cffe2e45bc06' and not prepared['source_patches']\nimport sys\nsys.path.insert(0,'/opt/toddy-build/scripts/build/phase2')\nfrom qualify_tecla import qualify_stage\nr=qualify_stage(Path('/opt/toddy-build'))\nfor relative,digest in r['stage_sha256'].items():\n p=w/'stage'/relative;assert sha(p)==digest;artifacts[str(p).removeprefix('/mnt/lfs')]=digest\nrecord={'artifacts':artifacts,'binary':'/sources/phase2/work/tecla-1/stage/usr/bin/tecla','source_sha256':prepared['source_sha256']}\np=Path('/mnt/lfs/sources/phase2/native-fixtures/tecla-cli-1');f=p/'accepted.json';raw=(json.dumps(record,sort_keys=True,indent=2)+'\\n').encode();assert len(raw)<512*1024\nif f.exists():assert f.is_file() and not f.is_symlink() and not f.stat().st_mode&0o222 and f.read_bytes()==raw\nelse:\n assert not p.exists();p.mkdir();part=p/'accepted.part'\n with part.open('xb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())\n part.chmod(0o444);part.rename(f);p.chmod(0o555)\nprint(json.dumps({'manifest':str(f).removeprefix('/mnt/lfs'),'manifest_sha256':sha(f),'manifest_bytes':len(raw)}))\n"
    accepted=subprocess.run(phase2_vm.ssh_args()+['python3 -'],input=code.encode(),capture_output=True,check=True)
    accepted_record=json.loads(accepted.stdout)
    assert probe.count(b'ACCEPTED = None')==1
    probe=probe.replace(b'ACCEPTED = None',('ACCEPTED = '+repr(accepted_record)).encode())
    payload_probe=compressed_payload(probe)
    CONTEXT.mkdir()
    state={'scope':'Staged Tecla actual native Wayland CLI only; no graphical viewer/complete GNOME/login/G2/physical acceptance',
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
