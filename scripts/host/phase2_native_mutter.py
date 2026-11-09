#!/usr/bin/env python3
"""Cold native headless compositor validation on a fresh disposable overlay only."""
import argparse
from datetime import datetime,timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import uuid

import boot_test as boot
from phase2_native_glycin import compressed_payload
from phase2_native_report import decode
import phase2_vm
import vm
ROOT=phase2_vm.ROOT;WORK=phase2_vm.WORK

def run(args,**kwargs):return subprocess.run(args,check=True,text=True,**kwargs)
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--context',default='native-mutter-runtime-1');args=parser.parse_args()
    assert re.fullmatch(r'native-mutter-runtime-[1-9][0-9]?',args.context)
    context=ROOT/'.local/phase2'/args.context;assert not context.exists(),'Reconcile existing operation; never replay'
    assert not subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip()
    assert shutil.disk_usage(ROOT).free>=100*1024**3+512*1024**2
    lock=open(vm.VM/'native-boot-test.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);boot.refuse_running_tests()
    code=r'''from pathlib import Path
import fcntl,hashlib,json,subprocess
subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
l=Path('/var/log/toddy/phase2');assert (l/'native-window-fixture-1.exit').read_text().strip()=='0'
r=json.loads(Path('/var/log/toddy/build/b02-mutter-resources-install.success.json').read_text());assert r['recipe_exit']==r['postcheck_exit']==0
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
w=Path('/mnt/lfs/sources/phase2/work/libadwaita-1');s=Path('/mnt/lfs/sources/phase2/inputs/libadwaita-1.9.3');stage=json.loads((w/'stage-results.json').read_text())
assert stage['native_build_exit']==stage['stage_exit']==stage['c_version_exit']==stage['gi_version_exit']==0
registered=json.loads((w/'compile/meson-info/intro-tests.json').read_text());assert len(registered)==67
artifacts={};tests=[]
for t in registered:
 assert t['cmd'][0].startswith('/build/compile/tests/')
 p=w/Path(t['cmd'][0]).relative_to('/build');assert p.is_file() and not p.is_symlink()
 digest=sha(p);artifacts[str(p).removeprefix('/mnt/lfs')]=digest
 assert t['env']==registered[0]['env']
 tests.append({**{k:t[k] for k in ['name','cmd','workdir','timeout'] if k in t},'sha256':digest})
libs=[p for p in (w/'compile/src').glob('libadwaita-1.so.*') if p.is_file() and not p.is_symlink()];assert len(libs)==1
artifacts[str(libs[0]).removeprefix('/mnt/lfs')]=sha(libs[0])
f=Path('/mnt/lfs/sources/phase2/work/native-window-fixture-1');fixture=json.loads((f/'fixture.json').read_text());assert fixture['compile_exit']==0
assert sha(f/'window-fixture')==fixture['binary_sha256'];artifacts[str(f/'window-fixture').removeprefix('/mnt/lfs')]=fixture['binary_sha256']
assets={str(p.relative_to(s/'tests')):sha(p) for p in (s/'tests').rglob('*') if p.is_file() and not p.is_symlink()}
assert s.stat().st_uid==0 and not s.stat().st_mode&0o022
record={'scope':'Frozen native compositor/GTK fixture and unchanged pending67Libadwaita artifacts, no graphical acceptance yet','builder_boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'fixture_source_sha256':fixture['source_sha256'],'fixture':str(f/'window-fixture').removeprefix('/mnt/lfs'),'tests':tests,'test_env':registered[0]['env'],'artifacts':artifacts,'source_test_assets_sha256':hashlib.sha256(json.dumps(assets,sort_keys=True).encode()).hexdigest(),'source_test_files':len(assets),'schema_cache_sha256':sha(Path('/mnt/lfs/usr/share/glib-2.0/schemas/gschemas.compiled'))}
data=json.dumps(record,sort_keys=True).encode()+bytes([10])
folder=Path('/mnt/lfs/sources/phase2/native-fixtures/mutter-1');folder.mkdir(mode=0o755,exist_ok=True)
assert folder.stat().st_uid==0 and not folder.is_symlink()
manifest=folder/'accepted.json'
if manifest.exists():
 assert manifest.is_file() and not manifest.is_symlink() and manifest.stat().st_uid==0
 assert manifest.read_bytes()==data,'Changed or partial manifest: reconcile before repeat'
else:
 with manifest.open('xb') as f:f.write(data);f.flush();__import__('os').fsync(f.fileno())
manifest.chmod(0o444)
print(json.dumps({'manifest':str(manifest).removeprefix('/mnt/lfs'),'manifest_sha256':hashlib.sha256(data).hexdigest(),'fixture_source_sha256':record['fixture_source_sha256'],'builder_boot_id':record['builder_boot_id'],'tests':len(record['tests']),'artifacts':len(record['artifacts']),'source_test_files':record['source_test_files']}))
'''
    accepted=json.loads(subprocess.run(phase2_vm.ssh_args()+['python3 -'],input=code.encode(),capture_output=True,check=True).stdout)
    assert hashlib.sha256((ROOT/'scripts/build/phase2/native-gtk-window.c').read_bytes()).hexdigest()==accepted['fixture_source_sha256']
    body=(ROOT/'scripts/host/phase2-native-mutter-probe.py').read_text();suite=(ROOT/'scripts/build/phase2/native_mutter_suite.py').read_text()
    assert body.count('ACCEPTED = None')==body.count('SUITE_SOURCE = None')==1
    probe=body.replace('ACCEPTED = None','ACCEPTED = '+repr(accepted)).replace('SUITE_SOURCE = None','SUITE_SOURCE = '+repr(suite)).encode();bootstrap=compressed_payload(probe);assert bootstrap.count(b'toddy-native-glycin')==1;bootstrap=bootstrap.replace(b'toddy-native-glycin',b'toddy-native-mutter')
    context.mkdir();state={'scope':'Native7.1.8 headless Mutter/GTK/Libadwaita only, B02 integrated desktop/G2 pending','commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'started_utc':datetime.now(timezone.utc).isoformat(),'controller_pid':os.getpid(),'controller_boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'controller_start_ticks':Path('/proc/self/stat').read_text().split()[21],'probe_sha256':hashlib.sha256(probe).hexdigest(),'payload_sha256':hashlib.sha256(bootstrap).hexdigest(),'accepted':accepted,'phase':'prepared'}
    def save():
        part=context/'result.json.part';assert not part.exists();part.write_text(json.dumps(state,indent=2)+'\n');part.replace(context/'result.json');print(json.dumps({'phase':state['phase'],'context':str(context)}),flush=True)
    save()
    with (context/'builder-stop.log').open('x') as log:
        state['phase']='stopping-builder';save();run([sys.executable,str(ROOT/'scripts/host/phase2_vm.py'),'stop'],stdout=log,stderr=subprocess.STDOUT)
    assert not subprocess.check_output(['docker','ps','-q','--filter','name=^/'+phase2_vm.NAME+'$'],text=True).strip()
    state['phase']='builder-stopped';save();source=WORK/'lfs-target.qcow2';assert source.is_file() and not source.is_symlink();identity=phase2_vm.backing_identity(source);state['source_identity']=identity;state['phase']='overlay-preparing';save()
    image=subprocess.check_output(['docker','image','inspect','--format','{{.Id}}',vm.IMAGE],text=True).strip();run_id=uuid.uuid4().hex
    common=['--user',f'{os.getuid()}:{os.getgid()}','--cap-drop=ALL','--security-opt=no-new-privileges','--network=none','--read-only','-v',f'{vm.VM}:/vm:ro','-v',f'{context}:/work']
    with (context/'prepare.log').open('x') as log:
        run(['docker','run','--rm',*common,image,'qemu-img','check','/vm/phase2/lfs-target.qcow2'],stdout=log,stderr=subprocess.STDOUT)
        run(['docker','run','--rm',*common,image,'qemu-img','create','-f','qcow2','-F','qcow2','-b','/vm/phase2/lfs-target.qcow2','/work/target.qcow2'],stdout=log,stderr=subprocess.STDOUT)
    unit=(ROOT/'scripts/host/boot-probe.service').read_bytes().replace(b'TimeoutStartSec=180',b'TimeoutStartSec=540')
    payloads={'systemd.extra-unit.toddy-boot-probe.service':unit,'systemd.unit-dropin.multi-user.target':(ROOT/'scripts/host/boot-probe.target.conf').read_bytes(),'toddy.boot-probe':bootstrap}
    qemu=boot.qemu_arguments('bios',payloads);qemu[qemu.index('-cpu')+1]='host';qemu[qemu.index('-smp')+1]='12';qemu[qemu.index('-m')+1]='12288'
    name='toddy-b02-mutter-'+run_id[:12];command=['docker','create','--name',name,'--label','toddy.boot-test='+run_id,*common,'--device','/dev/kvm','--group-add',str(Path('/dev/kvm').stat().st_gid),'--memory','13g','--cpus','12',image,*qemu]
    cid=subprocess.check_output(command,text=True).strip();state.update(phase='native-running',container_id=cid,container_name=name,run_id=run_id,command=command);save()
    with (context/'qemu.log').open('x') as log:run(['docker','start',cid],stdout=log,stderr=subprocess.STDOUT)
    try:
        waited=subprocess.run(['docker','wait',cid],capture_output=True,text=True,timeout=600);(context/'docker-wait.json').write_text(json.dumps({'exit':waited.returncode,'stdout':waited.stdout,'stderr':waited.stderr},indent=2)+'\n');waited.check_returncode();assert waited.stdout.strip()=='0'
    finally:state['container_final_state']=boot.stop_owned_container(cid,run_id);state['phase']='native-stopped';save()
    assert phase2_vm.backing_identity(source)==identity
    report,summary,recovered=decode((context/'serial.log').read_text(errors='replace'));(context/'native-report.json').write_text(json.dumps(report,indent=2)+'\n')
    for entry in report.get('native_client_images',[]):
        assert re.fullmatch(r'gtk-[a-z]+[.]png',entry['name']);data=__import__('base64').b64decode(entry['png_base64'],validate=True);assert hashlib.sha256(data).hexdigest()==entry['sha256'];(context/entry['name']).write_bytes(data)
    state.update(phase='native-report-recorded',summary=summary,recovered_protocol_markers=recovered,backing_unchanged=True,native_selected_passed=summary['all_selected_exits_zero']);save();assert summary['all_selected_exits_zero'],'Actual native failures retained'
if __name__=='__main__':main()
