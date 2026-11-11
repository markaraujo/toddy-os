#!/usr/bin/env python3
"""Disposable native installed FUSE and GNOME portal acceptance."""
from datetime import datetime,timezone
import fcntl,hashlib,json,os,shutil,subprocess,sys,threading,uuid
from pathlib import Path
import boot_test as boot
from phase2_native_report import decode
from phase2_native_glycin import compressed_payload
import phase2_vm
import phase2_portal_owner_control
import vm

ROOT=phase2_vm.ROOT;WORK=phase2_vm.WORK
CONTEXT=ROOT/'.local/phase2/native-fuse-portal-runtime-3'
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
    predecessor=ROOT/'.local/phase2/native-fuse-portal-runtime-2'
    previous=json.loads((predecessor/'result.json').read_text())
    assert previous['phase']=='native-report-recorded' and previous['backing_unchanged'] is True
    assert previous['native_selected_passed'] is False and previous['container_final_state']['Running'] is False
    assert phase2_vm.backing_identity(WORK/'lfs-target.qcow2')==previous['source_identity']
    actual=json.loads(subprocess.check_output(['docker','inspect','--format','{{json .State}}',previous['container_id']],text=True))
    assert actual['Running'] is False and actual['ExitCode']==0
    failed=json.loads((predecessor/'native-report.json').read_text())
    assert failed['owner_session']['properties']['Name']=='toddy-preview' and failed['fuse']['owner_unmount']['exit']==0 and not failed['portal_settings']
    assert failed['fuse']['allow_other_refused']['exit']==4 and failed['fuse']['other_uid_read_denied']['exit']==1
    assert failed['fuse']['running_config_sha256']=='952e7d9d6e5c8e523ebf128c220481bc29280424e0686e4b0903b518234bf77b'
    accepted=previous['accepted']
    fuse=(ROOT/'scripts/host/phase2-native-fuse-proof.py').read_bytes()
    client=(ROOT/'scripts/host/phase2-native-portal-client.py').read_text()
    probe=fuse+b'\nFUSE_PREVIOUS='+repr(failed['fuse']).encode()+b'\nPORTAL_CLIENT_SOURCE='+repr(client).encode()+b'\n'+(ROOT/'scripts/host/phase2-native-portal-probe.py').read_bytes()
    CONTEXT.mkdir(mode=0o700)
    state={'scope':'Native installed-kernel FUSE helper/privilege/refusal/recovery and portal appearance/filechooser/cancel/Close; no physical/whole B02 acceptance',
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
    assert not subprocess.check_output(['docker','ps','-q','--filter','name=^/'+phase2_vm.NAME+'$'],text=True).strip()
    state['phase']='builder-stopped-unchanged-predecessor';save()
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
    qemu+=['-audiodev','wav,id=desktopaudio,path=/work/audio.wav','-device','ich9-intel-hda','-device','hda-duplex,audiodev=desktopaudio']
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
    capture=threading.Thread(target=phase2_portal_owner_control.run,args=(CONTEXT,STOP),daemon=True);capture.start()
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
    state.update(phase='native-fuse-portal-verified');save()


if __name__=='__main__':main()
