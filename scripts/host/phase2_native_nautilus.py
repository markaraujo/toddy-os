#!/usr/bin/env python3
"""Run focused original Nautilus tests on a normal native GDM/PAM user seat."""
from datetime import datetime,timezone
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import threading
import uuid

import boot_test as boot
import phase2_gdm_owner_control
from phase2_native_glycin import compressed_payload
from phase2_native_report import decode
import phase2_vm
import vm

ROOT=phase2_vm.ROOT
CONTEXT=ROOT/'.local/phase2/native-nautilus-runtime-1'
INPUT=ROOT/'.local/phase2/native-nautilus-inputs-1'


def run(args,**kwargs):return subprocess.run(args,check=True,text=True,**kwargs)


def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def main():
    global CONTEXT
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--preflight-only',action='store_true')
    parser.add_argument('--collector-followup',action='store_true')
    parser.add_argument('--files-view-followup',action='store_true')
    args=parser.parse_args();preflight_only=args.preflight_only
    assert not (args.collector_followup and args.files_view_followup)
    followup=args.collector_followup or args.files_view_followup
    CONTEXT=ROOT/'.local/phase2'/('native-nautilus-runtime-3' if args.files_view_followup else 'native-nautilus-runtime-2' if args.collector_followup else 'native-nautilus-runtime-1')
    assert not CONTEXT.exists(),'Inspect existing native operation; never replay'
    if not preflight_only:assert not subprocess.check_output(['git','status','--porcelain'],text=True).strip(),'Commit reviewed inputs before native boot'
    assert shutil.disk_usage(ROOT).free>=100*1024**3+512*1024**2
    lock=open(vm.VM/'native-boot-test.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);boot.refuse_running_tests()
    custody=ROOT/'.local/phase2/settings-scratch-custody-2'
    retained=json.loads((custody/'result.json').read_text());assert retained['state']=='complete' and retained['prior_generation_files_metadata_and_hardlinks_unchanged']
    assert (custody/'restore-validation.exit').read_text().strip()=='0'
    assert sha(custody/'scratch.tar.gz')==retained['archive_sha256']
    inputs=json.loads((INPUT/'result.json').read_text());assert inputs['state']=='complete' and inputs['custody_generation']==2
    image=INPUT/'cache.raw';assert image.is_file() and not image.is_symlink()
    assert image.stat().st_size==inputs['transport']['raw_bytes'] and sha(image)==inputs['transport']['raw_sha256']
    probe=(ROOT/'scripts/host/phase2-native-nautilus-probe.py').read_bytes()
    assert probe.count(b'NAUTILUS_FIXTURE = None')==1
    probe=probe.replace(b'NAUTILUS_FIXTURE = None',('NAUTILUS_FIXTURE = '+repr({'fixture_sha256':inputs['fixture_sha256']})).encode())
    prefix=None
    if followup:
        prefix=json.loads((ROOT/'.local/phase2'/('nautilus-native-prefix-qualified-2.json' if args.files_view_followup else 'nautilus-native-prefix-qualified-1.json')).read_text())
        assert prefix['state']=='qualified' and prefix['reused_programs']==(11 if args.files_view_followup else 9) and prefix['reused_GLib_cases']==(64 if args.files_view_followup else 59)
    assert probe.count(b'REUSED_NAUTILUS = None')==1
    probe=probe.replace(b'REUSED_NAUTILUS = None',('REUSED_NAUTILUS = '+repr(prefix)).encode())
    bootstrap=compressed_payload(probe)
    code=r'''
from pathlib import Path
import fcntl,hashlib,json,subprocess
subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
assert not list(Path('/var/log/toddy/build').glob('*.running.json')) and not Path('/var/log/toddy/build/input-sync.running').exists()
versions={'gnome-shell':'50.4-1+toddy1','gtk':'4.22.4-1+toddy11','mutter':'50.4-1+toddy1','gdm':'50.2-1+toddy1','localsearch':'3.11.1-1+toddy1'}
for name,version in versions.items():assert subprocess.check_output(['chroot','/mnt/lfs','dpkg-query','-W','-f=${Version}',name],text=True)==version
l=Path('/var/log/toddy/phase2');p=Path('/mnt/lfs/sources/phase2/native-fixtures/nautilus-1.json');record=json.loads(p.read_text())
assert record['state']=='complete' and p.read_bytes()==(l/'nautilus-native-fixture-1.json').read_bytes()
for base,key in [(Path('/mnt/lfs')/record['source_path'].lstrip('/'),'source_files'),(Path('/mnt/lfs')/record['work_path'].lstrip('/')/'compile','compile_files'),(Path('/mnt/lfs')/record['work_path'].lstrip('/')/'stage','stage_files')]:
 for name,digest in record[key].items():
  with (base/name).open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==digest
native=json.loads((l/'settings-scratch-custody-2.json').read_text());assert native['state']=='archive-stream-complete-source-unchanged' and native['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip()
print(json.dumps({'fixture_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'versions':versions,'source_compiler_stage_unchanged':True,'builder_boot_id':native['boot_id'],'selected_programs':len(record['selected_tests'])}))
'''
    if followup:
        previous=ROOT/'.local/phase2'/('native-nautilus-runtime-2' if args.files_view_followup else 'native-nautilus-runtime-1')
        prior=json.loads((previous/'result.json').read_text());raw=json.loads((previous/'native-report.json').read_text())
        assert prior['phase']=='native-report-recorded' and prior['backing_unchanged'] and not prior['native_selected_passed']
        assert hashlib.sha256(json.dumps(raw,sort_keys=True).encode()).hexdigest()==prior['summary']['report_sha256']==prefix['source_report_sha256']
        original=json.loads(subprocess.check_output(['docker','inspect',prior['container_id']],text=True))[0]
        assert not original['State']['Running'] and original['State']['ExitCode']==0
        assert original['Config']['Labels']['toddy.boot-test']==prior['run_id']
        assert phase2_vm.backing_identity(phase2_vm.WORK/'lfs-target.qcow2')==prior['source_identity']
        assert raw['original_tests']['readonly_inputs_unchanged']
        if args.files_view_followup:
            previous_runs=raw['original_tests']['runs'];assert len(previous_runs)==3 and all(r['passed'] and r['exit']==0 for r in previous_runs[:2])
            failed=previous_runs[-1];assert failed['name']=='test-files-view' and failed['exit']==1 and not failed['timed_out']
            assert 'Read-only file system' in failed['stderr'] and 'dir=os.getcwd()' in failed['stderr']
        else:assert len(raw['original_tests']['runs'])==9 and all(r['exit']==0 and not r['timed_out'] for r in raw['original_tests']['runs'])
        assert not subprocess.check_output(['docker','ps','-q','--filter','name=^/'+phase2_vm.NAME+'$'],text=True).strip()
        accepted=prior['accepted']
    else:
        accepted=subprocess.run(phase2_vm.ssh_args()+['python3 -'],input=code.encode(),capture_output=True,check=True)
        accepted=json.loads(accepted.stdout)
    assert accepted['fixture_sha256']==inputs['fixture_sha256']
    if preflight_only:
        print(json.dumps({'state':'preflight-only-passed','accepted':accepted,'probe_bytes':len(probe),'credential_bytes':len(bootstrap),'native_input_raw_bytes':inputs['transport']['raw_bytes'],'no_VM_started':True}));return
    CONTEXT.mkdir(mode=0o700)
    state={'phase':'prepared','scope':'Focused original Nautilus programs on actual normal GDM/PAM Wayland user seat with exact readonly cache data attachment; not installed Nautilus/full-suite/B02/physical acceptance',
           'commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
           'started_utc':datetime.now(timezone.utc).isoformat(),'controller_pid':os.getpid(),
           'controller_boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'controller_start_ticks':Path('/proc/self/stat').read_text().split()[21],
           'accepted':accepted,'collector_followup':args.collector_followup,'files_view_followup':args.files_view_followup,'qualified_prefix_source_report_sha256':prefix['source_report_sha256'] if prefix else None,'probe_sha256':hashlib.sha256(probe).hexdigest(),'native_input_transport':inputs['transport']}
    def save():
        part=CONTEXT/'result.json.part';assert not part.exists();part.write_text(json.dumps(state,indent=2)+'\n');part.replace(CONTEXT/'result.json');print(json.dumps({'phase':state['phase'],'context':str(CONTEXT)}),flush=True)
    save()
    if not followup:
        with (CONTEXT/'builder-stop.log').open('x') as log:
            state['phase']='stopping-builder';save();run([sys.executable,str(ROOT/'scripts/host/phase2_vm.py'),'stop'],stdout=log,stderr=subprocess.STDOUT)
    assert not subprocess.check_output(['docker','ps','-q','--filter','name=^/'+phase2_vm.NAME+'$'],text=True).strip()
    source=phase2_vm.WORK/'lfs-target.qcow2';identity=phase2_vm.backing_identity(source);state.update(phase='builder-stopped',source_identity=identity);save()
    image_id=subprocess.check_output(['docker','image','inspect','--format','{{.Id}}',vm.IMAGE],text=True).strip()
    common=['--user',f'{os.getuid()}:{os.getgid()}','--cap-drop=ALL','--security-opt=no-new-privileges','--network=none','--read-only','-v',str(vm.VM)+':/vm:ro','-v',str(CONTEXT)+':/work','-v',str(INPUT)+':/input:ro']
    with (CONTEXT/'prepare.log').open('x') as log:
        run(['docker','run','--rm',*common,image_id,'qemu-img','check','/vm/phase2/lfs-target.qcow2'],stdout=log,stderr=subprocess.STDOUT)
        run(['docker','run','--rm',*common,image_id,'qemu-img','create','-f','qcow2','-F','qcow2','-b','/vm/phase2/lfs-target.qcow2','/work/target.qcow2'],stdout=log,stderr=subprocess.STDOUT)
    service=(ROOT/'scripts/host/boot-probe.service').read_bytes().replace(b'TimeoutStartSec=180',b'TimeoutStartSec=720')
    payloads={'systemd.extra-unit.toddy-boot-probe.service':service,'systemd.unit-dropin.multi-user.target':(ROOT/'scripts/host/boot-probe.target.conf').read_bytes(),'toddy.boot-probe':bootstrap}
    qemu=boot.qemu_arguments('bios',payloads);qemu[qemu.index('-cpu')+1]='host';qemu[qemu.index('-smp')+1]='4';qemu[qemu.index('-m')+1]='4096'
    qemu+=['-serial','file:/work/native-evidence.log','-vga','virtio','-device','qemu-xhci,id=usb','-device','usb-tablet,bus=usb.0','-device','usb-kbd,bus=usb.0','-qmp','unix:/work/q,server=on,wait=off','-chardev','socket,id=fixture,path=/work/auth,server=on,wait=off','-device','isa-serial,chardev=fixture,index=2','-drive','file=/input/cache.raw,if=none,id=nativeinput,format=raw,readonly=on','-device','virtio-blk-pci,drive=nativeinput,serial=TODDY-NAUTILUS-INPUT']
    run_id=uuid.uuid4().hex;name='toddy-b02-native-'+run_id[:12]
    command=['docker','create','--name',name,'--label','toddy.boot-test='+run_id,*common,'--device','/dev/kvm','--group-add',str(Path('/dev/kvm').stat().st_gid),'--memory','5g','--cpus','4',image_id,*qemu]
    cid=subprocess.check_output(command,text=True).strip();state.update(phase='native-running',container_id=cid,container_name=name,run_id=run_id,command=command);save()
    with (CONTEXT/'qemu.log').open('x') as log:run(['docker','start',cid],stdout=log,stderr=subprocess.STDOUT)
    stop=threading.Event();worker=threading.Thread(target=phase2_gdm_owner_control.run,args=(CONTEXT,stop),daemon=True);worker.start()
    try:
        waited=subprocess.run(['docker','wait',cid],capture_output=True,text=True,timeout=900)
        (CONTEXT/'docker-wait.json').write_text(json.dumps({'exit':waited.returncode,'stdout':waited.stdout,'stderr':waited.stderr},indent=2)+'\n');waited.check_returncode();assert waited.stdout.strip()=='0'
    finally:
        stop.set();worker.join(timeout=20);state['container_final_state']=boot.stop_owned_container(cid,run_id);state['phase']='native-stopped';save()
    assert phase2_vm.backing_identity(source)==identity;state['backing_unchanged']=True;save()
    report,summary,recovered=decode((CONTEXT/'native-evidence.log').read_text(errors='strict'))
    (CONTEXT/'native-report.json').write_text(json.dumps(report,indent=2)+'\n')
    state.update(phase='native-report-recorded',summary=summary,recovered_protocol_markers=recovered,native_selected_passed=summary['all_selected_exits_zero']);save()
    assert summary['all_selected_exits_zero'],'Native failure retained; do not repeat blindly or mark accepted'


if __name__=='__main__':main()
