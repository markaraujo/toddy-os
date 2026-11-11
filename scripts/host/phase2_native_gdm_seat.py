#!/usr/bin/env python3
"""Observe installed GDM on one cold disposable native virtual DRM/input seat, no NIC."""
from datetime import datetime,timezone
import fcntl,hashlib,json,os,shutil,subprocess,sys,uuid,socket,threading,time
from pathlib import Path
import boot_test as boot
from phase2_native_report import decode
from phase2_native_glycin import compressed_payload
import phase2_vm
import vm
ROOT=phase2_vm.ROOT;WORK=phase2_vm.WORK
CONTEXT=ROOT/'.local/phase2/native-gdm-seat-runtime-1'
CAPTURE_STOP=threading.Event()
def run(args,**kwargs):return subprocess.run(args,check=True,text=True,**kwargs)
def capture_scanout():
    records=[]
    try:
        deadline=time.monotonic()+120
        while not (CONTEXT/'q').exists():
            if time.monotonic()>deadline:raise TimeoutError('QMP socket not available')
            time.sleep(.5)
        connection=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
        connection.settimeout(15);connection.connect(str(CONTEXT/'q'))
        stream=connection.makefile('rwb',buffering=0)
        assert 'QMP' in json.loads(stream.readline())
        def call(name,arguments=None):
            stream.write((json.dumps({'execute':name,**({'arguments':arguments} if arguments else {})})+'\n').encode())
            while True:
                result=json.loads(stream.readline())
                if 'event' in result:continue
                assert 'return' in result,result
                return result['return']
        call('qmp_capabilities')
        for index in range(12):
            if CAPTURE_STOP.wait(10):break
            status=call('query-status')
            if status.get('status')!='running':break
            filename='scanout-%02d.ppm'%index
            call('screendump',{'filename':'/work/'+filename})
            row={'frame':filename,'status':status,'monotonic':time.monotonic()}
            if index==5:
                row['real_virtual_pointer_event']=call('input-send-event',{'events':[{'type':'abs','data':{'axis':'x','value':18000}},{'type':'abs','data':{'axis':'y','value':16000}}]})
            records.append(row)
        stream.close();connection.close()
    except Exception as error:
        records.append({'error':type(error).__name__,'message':str(error)})
    finally:
        (CONTEXT/'scanout-observation.json').write_text(json.dumps(records,indent=2)+'\n')

def main():
    assert len(sys.argv)==1
    custody=ROOT/'.local/phase2/settings-scratch-custody-1'
    retained=json.loads((custody/'result.json').read_text());assert retained['state']=='complete'
    assert (custody/'restore-validation.exit').read_text().strip()=='0'
    assert hashlib.file_digest((custody/'scratch.tar.gz').open('rb'),'sha256').hexdigest()==retained['archive_sha256']
    cold=json.loads((ROOT/'.local/phase2/cold-math-chunk-custody-1/result.json').read_text());assert cold['state']=='complete'
    assert not CONTEXT.exists(),'Reconcile native operation before any repeat'
    assert not subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip(),'Commit reviewed inputs before native boot'
    assert shutil.disk_usage(ROOT).free>=100*1024**3+512*1024**2
    lock=open(vm.VM/'native-boot-test.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);boot.refuse_running_tests()
    probe=(ROOT/'scripts/host/phase2-native-shell-probe.py').read_bytes()
    code="from pathlib import Path\nimport fcntl,hashlib,json,subprocess\nsubprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)\nlock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)\nassert not list(Path('/var/log/toddy/build').glob('*.running.json'))\nversions={'gnome-shell':'50.4-1+toddy1','gtk':'4.22.4-1+toddy10','gdm':'50.2-1+toddy1','mutter':'50.4-1+toddy1','gstreamer':'1.28.6-1+toddy1','gst-plugins-base':'1.28.6-1+toddy1'}\nfiles=0\nfor name,version in versions.items():\n assert subprocess.check_output(['chroot','/mnt/lfs','dpkg-query','-W','-f=${Version}',name],text=True)==version\n r=json.loads(Path('/var/log/toddy/packages',name+'_'+version+'_amd64.json').read_text());assert r['installed']\n for n,row in r['payload'].items():\n  if 'sha256' in row:\n   p=Path('/mnt/lfs')/n.lstrip('/');assert hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256'];files+=1\nfor step in ['b02-gnome-shell-install','b02-settings-schema-union-install','b02-gstreamer-install','b02-gst-plugins-base-install']:\n r=json.loads(Path('/var/log/toddy/build',step+'.success.json').read_text());assert r['recipe_exit']==r['postcheck_exit']==0\nprint(json.dumps({'versions':versions,'verified_native_files':files,'builder_boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'target_serial':'TODDY-LFS-TARGET','native_kernel_expected':'7.1.8-toddy'}))\n"
    accepted=subprocess.run(phase2_vm.ssh_args()+['python3 -'],input=code.encode(),capture_output=True,check=True)
    accepted_record=json.loads(accepted.stdout)
    CONTEXT.mkdir()
    state={'scope':'Normal installed GDM on actual virtual DRM/input seat with QEMU scanout; greeter observation only, no authenticated login/basic-app/B02/G2/physical acceptance',
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
              'toddy.boot-probe':compressed_payload(probe)}
    qemu=boot.qemu_arguments('bios',payloads)
    qemu+=['-serial','file:/work/native-evidence.log','-vga','virtio','-device','qemu-xhci,id=usb','-device','usb-tablet,bus=usb.0','-device','usb-kbd,bus=usb.0','-qmp','unix:/work/q,server=on,wait=off']
    qemu[qemu.index('-cpu')+1]='host';qemu[qemu.index('-smp')+1]='4';qemu[qemu.index('-m')+1]='4096'
    name='toddy-b02-native-'+run_id[:12]
    command=['docker','create','--name',name,'--label','toddy.boot-test='+run_id,*common,
             '--device','/dev/kvm','--group-add',str(Path('/dev/kvm').stat().st_gid),'--memory','5g','--cpus','4',image,*qemu]
    cid=subprocess.check_output(command,text=True).strip()
    state.update(phase='native-running',container_id=cid,container_name=name,run_id=run_id,command=command);save()
    with (CONTEXT/'qemu.log').open('x') as log:run(['docker','start',cid],stdout=log,stderr=subprocess.STDOUT)
    capture=threading.Thread(target=capture_scanout,daemon=True);capture.start()
    try:
        waited=subprocess.run(['docker','wait',cid],capture_output=True,text=True,timeout=600)
        (CONTEXT/'docker-wait.json').write_text(json.dumps({'exit':waited.returncode,'stdout':waited.stdout,'stderr':waited.stderr},indent=2)+'\n')
        waited.check_returncode();assert waited.stdout.strip()=='0','QEMU runtime exit nonzero'
    finally:
        CAPTURE_STOP.set();capture.join(timeout=20)
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
