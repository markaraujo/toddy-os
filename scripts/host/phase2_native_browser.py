#!/usr/bin/env python3
"""Disposable default graphical boot and installed browser acceptance."""
from datetime import datetime,timezone
import fcntl,hashlib,json,os,shutil,subprocess,sys,threading,uuid
from pathlib import Path
import boot_test as boot
from phase2_native_report import decode
from phase2_native_glycin import compressed_payload
import phase2_vm
import phase2_gdm_owner_control
import vm

ROOT=phase2_vm.ROOT;WORK=phase2_vm.WORK
CONTEXT=ROOT/'.local/phase2/native-browser-runtime-1'
STOP=threading.Event()


def run(args,**kwargs):return subprocess.run(args,check=True,text=True,**kwargs)


def main():
    assert len(sys.argv)==1
    assert not CONTEXT.exists(),'Inspect actual native job/image/report; never replay'
    assert not subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip(),'Commit reviewed native inputs first'
    assert shutil.disk_usage(ROOT).free>=100*1024**3+512*1024**2
    custody=ROOT/'.local/phase2/settings-scratch-custody-4'
    retained=json.loads((custody/'result.json').read_text());assert retained['state']=='complete'
    with (custody/'scratch.tar.gz').open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==retained['archive_sha256']
    assert (custody/'restore-validation.exit').read_text().strip()=='0'
    for name in ['cold-math-chunk-custody-1','cold-firefox-chunk-custody-1','cold-native-chunk-custody-1']:
        assert json.loads((ROOT/'.local/phase2'/name/'result.json').read_text())['state']=='complete'
    lock=open(vm.VM/'native-boot-test.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    boot.refuse_running_tests()
    code=r'''from pathlib import Path
import fcntl,json,hashlib,subprocess,sys
subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
versions={'gdm':('50.2-1+toddy1','amd64'),'gtk':('4.22.4-1+toddy13','amd64'),'gnome-shell':('50.4-1+toddy1','amd64'),'mutter':('50.4-1+toddy1','amd64'),'gnome-control-center':('50.4-1+toddy1','amd64'),'networkmanager':('1.58.1-1+toddy1','amd64'),'polkit':('127-1+toddy1','amd64'),'toddy-desktop-network':('0.2.0-1+toddy2','all'),'firefox':('153.7.0esr-1+toddy1','amd64')}
files=0
for name,(version,architecture) in versions.items():
 assert subprocess.check_output(['chroot','/mnt/lfs','dpkg-query','-W','-f=${Version}',name],text=True)==version
 r=json.loads(Path('/var/log/toddy/packages',name+'_'+version+'_'+architecture+'.json').read_text());assert r['installed']
 for n,row in r['payload'].items():
  if 'sha256' in row:
   p=Path('/mnt/lfs')/n.lstrip('/');assert hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256'];files+=1
sys.path.insert(0,'/opt/toddy-build/scripts/build/phase2')
from verify_settings_scratch_restore import verify
saved=json.loads(Path('/var/log/toddy/phase2/settings-scratch-custody-4.json').read_text())
verify(Path('/run/toddy-samba-client-1'),saved)
import restore_browser_work as browser
inspected=browser.inspect(json.loads(browser.RECORD.read_text()))
assert json.loads(Path('/var/log/toddy/phase2/browser-private-restore-qualified-1.json').read_text())['state']=='complete'
import restore_firefox_security_source as security
candidate=security.inspect(json.loads(security.RECEIPT.read_text()))
import firefox_archive_storage as archive
archive.inspect()
for step in ['b02-firefox-runtime-verify-3','b02-desktop-graphical-boot']:
 r=json.loads(Path('/var/log/toddy/build',step+'.success.json').read_text());assert r['recipe_exit']==r['postcheck_exit']==0
assert Path('/mnt/lfs/etc/systemd/system/default.target').readlink()==Path('/usr/lib/systemd/system/graphical.target')
assert Path('/mnt/lfs/etc/systemd/system/display-manager.service').readlink()==Path('/usr/lib/systemd/system/gdm.service')
print(json.dumps({'versions':versions,'verified_native_files':files,'browser_recovery':inspected,'builder_boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'native_kernel_expected':'7.1.8-toddy'}))
'''
    checked=subprocess.run(phase2_vm.ssh_args()+['python3 -'],input=code.encode(),capture_output=True,check=True)
    accepted=json.loads(checked.stdout)
    fixtures={name:(ROOT/'tests/fixtures/browser-smoke'/name).read_text() for name in ['index.html','second.html']}
    probe=(ROOT/'scripts/host/phase2-native-browser-probe.py').read_bytes().replace(b'FIXTURES = None',('FIXTURES = '+repr(fixtures)).encode())
    CONTEXT.mkdir(mode=0o700)
    state={'scope':'Native default graphical boot and normal owner browser interaction/restart/content sandbox; no physical/whole B02 acceptance',
           'commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
           'started_utc':datetime.now(timezone.utc).isoformat(),'controller_pid':os.getpid(),
           'controller_boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
           'controller_start_ticks':Path('/proc/self/stat').read_text().split()[21],
           'accepted':accepted,'probe_sha256':hashlib.sha256(probe).hexdigest(),'phase':'prepared'}
    def save():
        part=CONTEXT/'result.json.part';assert not part.exists()
        part.write_text(json.dumps(state,indent=2)+'\n');part.replace(CONTEXT/'result.json')
        print(json.dumps({'phase':state['phase'],'context':str(CONTEXT)}),flush=True)
    save()
    with (CONTEXT/'builder-stop.log').open('x') as log:
        state['phase']='stopping-builder';save()
        run([sys.executable,str(ROOT/'scripts/host/phase2_vm.py'),'stop'],stdout=log,stderr=subprocess.STDOUT)
    assert not subprocess.check_output(['docker','ps','-q','--filter','name=^/'+phase2_vm.NAME+'$'],text=True).strip()
    state['phase']='builder-stopped';save()
    source=WORK/'lfs-target.qcow2'
    assert source.is_file() and not source.is_symlink()
    identity=phase2_vm.backing_identity(source);state['source_identity']=identity
    image=subprocess.check_output(['docker','image','inspect','--format','{{.Id}}',vm.IMAGE],text=True).strip()
    run_id=uuid.uuid4().hex
    common=['--user',f'{os.getuid()}:{os.getgid()}','--cap-drop=ALL','--security-opt=no-new-privileges','--network=none','--read-only',
            '-v',f'{vm.VM}:/vm:ro','-v',f'{CONTEXT}:/work']
    backing='/vm/phase2/lfs-target.qcow2'
    with (CONTEXT/'prepare.log').open('x') as log:
        run(['docker','run','--rm',*common,image,'qemu-img','check',backing],stdout=log,stderr=subprocess.STDOUT)
        run(['docker','run','--rm',*common,image,'qemu-img','create','-f','qcow2','-F','qcow2','-b',backing,'/work/target.qcow2'],stdout=log,stderr=subprocess.STDOUT)
    unit=(ROOT/'scripts/host/desktop-boot-probe.service').read_bytes()
    payloads={'systemd.extra-unit.toddy-boot-probe.service':unit,
              'systemd.unit-dropin.multi-user.target':(ROOT/'scripts/host/boot-probe.target.conf').read_bytes(),
              'toddy.boot-probe':compressed_payload(probe)}
    qemu=boot.qemu_arguments('bios',payloads)
    index=qemu.index('-nic');assert qemu[index+1]=='none';del qemu[index:index+2]
    qemu+=['-netdev','user,id=desktopnet','-device','virtio-net-pci,netdev=desktopnet']
    qemu+=['-serial','file:/work/native-evidence.log','-vga','virtio','-device','qemu-xhci,id=usb','-device','usb-tablet,bus=usb.0','-device','usb-kbd,bus=usb.0','-qmp','unix:/work/q,server=on,wait=off']
    qemu+=['-chardev','socket,id=fixture,path=/work/auth,server=on,wait=off','-device','isa-serial,chardev=fixture,index=2']
    qemu[qemu.index('-cpu')+1]='host';qemu[qemu.index('-smp')+1]='4';qemu[qemu.index('-m')+1]='4096'
    # Only this declared network test gets ordinary Docker egress + QEMU user NAT.
    # No host networking/TAP, inbound forwarded port, credential or privileged cap.
    runtime=[v if v!='--network=none' else '--network=bridge' for v in common]
    name='toddy-b02-native-'+run_id[:12]
    command=['docker','create','--name',name,'--label','toddy.boot-test='+run_id,*runtime,
             '--device','/dev/kvm','--group-add',str(Path('/dev/kvm').stat().st_gid),'--memory','5g','--cpus','4',image,*qemu]
    cid=subprocess.check_output(command,text=True).strip()
    state.update(phase='native-running',container_id=cid,container_name=name,run_id=run_id,command=command);save()
    with (CONTEXT/'qemu.log').open('x') as log:run(['docker','start',cid],stdout=log,stderr=subprocess.STDOUT)
    capture=threading.Thread(target=phase2_gdm_owner_control.run,args=(CONTEXT,STOP),daemon=True);capture.start()
    try:
        waited=subprocess.run(['docker','wait',cid],capture_output=True,text=True,timeout=1080)
        (CONTEXT/'docker-wait.json').write_text(json.dumps({'exit':waited.returncode,'stdout':waited.stdout,'stderr':waited.stderr},indent=2)+'\n')
        waited.check_returncode();assert waited.stdout.strip()=='0','Actual QEMU exit nonzero'
    finally:
        STOP.set()
        if capture:capture.join(timeout=20)
        state['container_final_state']=boot.stop_owned_container(cid,run_id)
        state['phase']='native-stopped';save()
    assert phase2_vm.backing_identity(source)==identity,'Backing changed; preserve overlay and stop'
    evidence=(CONTEXT/'native-evidence.log').read_text(errors='strict')
    report,summary,recovered=decode(evidence)
    state['dedicated_evidence_sha256']=hashlib.sha256(evidence.encode()).hexdigest()
    (CONTEXT/'native-report.json').write_text(json.dumps(report,indent=2)+'\n')
    state.update(phase='native-report-recorded',summary=summary,recovered_protocol_markers=recovered,
                 backing_unchanged=True,native_selected_passed=summary['all_selected_exits_zero'],
                 builder_restart='Pending actual container/image/cache/mount reconciliation, new recovery receipts')
    save();assert summary['all_selected_exits_zero'],'Native failures retained; no acceptance'


if __name__=='__main__':main()
