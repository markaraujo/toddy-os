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
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--context',default='native-mutter-runtime-1');parser.add_argument('--component',choices=['libadwaita','gtksourceview'],default='libadwaita');parser.add_argument('--only-syntax',action='store_true');parser.add_argument('--remaining-syntax',action='store_true');args=parser.parse_args();assert not args.only_syntax or args.component=='gtksourceview';assert not args.remaining_syntax or args.only_syntax
    assert re.fullmatch(r'native-mutter-runtime-[1-9][0-9]?',args.context)
    context=ROOT/'.local/phase2'/args.context;assert not context.exists(),'Reconcile existing operation; never replay'
    assert not subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip()
    assert shutil.disk_usage(ROOT).free>=100*1024**3+512*1024**2
    lock=open(vm.VM/'native-boot-test.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);boot.refuse_running_tests()
    code='component='+repr(args.component)+'\nsyntax_only='+repr(args.only_syntax)+'\nremaining_syntax='+repr(args.remaining_syntax)+'\n'+r'''from pathlib import Path
import fcntl,hashlib,json,re,subprocess
subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
l=Path('/var/log/toddy/phase2')
if component=='libadwaita':assert (l/'native-window-fixture-1.exit').read_text().strip()=='0'
else:assert (l/'gtksourceview-probe-2.exit').read_text().strip()=='0'
r=json.loads(Path('/var/log/toddy/build/b02-mutter-resources-install.success.json').read_text());assert r['recipe_exit']==r['postcheck_exit']==0
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
version='1.9.3' if component=='libadwaita' else '5.20.0'
w=Path('/mnt/lfs/sources/phase2/work')/(component+'-1');s=Path('/mnt/lfs/sources/phase2/inputs')/(component+'-'+version);stage=json.loads((w/'stage-results.json').read_text())
assert stage['native_build_exit']==stage['stage_exit']==stage['gi_version_exit']==0
assert stage['c_version_exit' if component=='libadwaita' else 'c_version_data_exit']==0
registered=json.loads((w/'compile/meson-info/intro-tests.json').read_text());assert len(registered)==(67 if component=='libadwaita' else 26)
reused=None
if syntax_only:
 raw=(l/'native-gtksource-2-report.json').read_bytes();expected='a865921bc8aaa2af2d4dff7f86068f1e4bcc3b6f49ddec56b27aac914c67475c';assert hashlib.sha256(raw).hexdigest()==expected
 previous=json.loads(raw);assert previous['all_selected_exits_zero'] and previous['suite']['passed_case_executions']==273 and previous['suite']['skipped_case_executions']==116
 old=json.loads(Path('/mnt/lfs/sources/phase2/native-fixtures/gtksourceview-1/accepted.json').read_text());assert previous['manifest_sha256']==sha(Path('/mnt/lfs/sources/phase2/native-fixtures/gtksourceview-1/accepted.json'))
 for path,digest in old['artifacts'].items():assert sha(Path('/mnt/lfs')/path.lstrip('/'))==digest
 reused={'report_sha256':expected,'manifest_sha256':previous['manifest_sha256'],'drivers_reused':25,'passed_case_executions':273,'upstream_known_skips':18,'syntax_skips_pending':98,'all_previous_artifacts_unchanged':len(old['artifacts'])}
 registered=[t for t in registered if t['name']=='test-syntax'];assert len(registered)==1
syntax_cases=None;partial=None
if remaining_syntax:
 raw=(l/'native-gtksource-3-report.json').read_bytes();expected='d261eb42007e84d42552e1afcfc0ed982ea0043c9d0958525c66c580e6486943';assert hashlib.sha256(raw).hexdigest()==expected
 prior=json.loads(raw);assert prior['syntax_only'] is True and prior['suite']['passed_case_executions']==9 and prior['compositor_exit']==1
 assert len(prior['runs'])==1 and prior['runs'][0]['exit']==-6 and "g_utf8_validate (text, len, NULL)" in prior['runs'][0]['stdout']
 old=Path('/mnt/lfs/sources/phase2/native-fixtures/gtksourceview-syntax-1/accepted.json');assert sha(old)==prior['manifest_sha256']
 for path,digest in json.loads(old.read_text())['artifacts'].items():assert sha(Path('/mnt/lfs')/path.lstrip('/'))==digest
 completed=re.findall(r'^ok\s+[0-9]+ (/syntax-highlighting/file[.][^\s]+)$',prior['runs'][0]['stdout'],re.M);assert len(completed)==9
 fixtures={p.name:p for p in (s/'tests/syntax-highlighting').glob('file.*')};assert len(fixtures)==98
 invalid=fixtures['file.cir'];assert sha(invalid)=='723dc8e309adae5b278371ffa43585cf55be329d721a87f11861144ad11f8fc4'
 try:invalid.read_bytes().decode('utf-8')
 except UnicodeDecodeError:pass
 else:raise AssertionError('Expected original invalid UTF8 fixture')
 for name,p in fixtures.items():
  if name!='file.cir':p.read_bytes().decode('utf-8')
 syntax_cases=sorted('/syntax-highlighting/'+name for name in fixtures if name!='file.cir' and '/syntax-highlighting/'+name not in completed);assert len(syntax_cases)==88
 partial={'report_sha256':expected,'passed_cases_reused':completed,'expected_refusal':{'case':'/syntax-highlighting/file.cir','fixture_sha256':sha(invalid),'reason':'Original fixture invalid UTF8; original GTK validation abort retained, not a passed full driver'}}
binary_prefix='/build/compile/'+('tests/' if component=='libadwaita' else 'testsuite/')
artifacts={};tests=[]
for t in registered:
 assert t['cmd'][0].startswith(binary_prefix)
 p=w/Path(t['cmd'][0]).relative_to('/build');assert p.is_file() and not p.is_symlink()
 digest=sha(p);artifacts[str(p).removeprefix('/mnt/lfs')]=digest
 assert t['env']==registered[0]['env']
 tests.append({**{k:t[k] for k in ['name','cmd','workdir','timeout'] if k in t},'sha256':digest})
libdir='src' if component=='libadwaita' else 'gtksourceview'
libpattern='libadwaita-1.so.*' if component=='libadwaita' else 'libgtksourceview-5.so.*'
libs=[p for p in (w/'compile'/libdir).glob(libpattern) if p.is_file() and not p.is_symlink()];assert len(libs)==1
artifacts[str(libs[0]).removeprefix('/mnt/lfs')]=sha(libs[0])
fixture=None;fixture_source_sha=None
if component=='libadwaita':
 f=Path('/mnt/lfs/sources/phase2/work/native-window-fixture-1');fixture=json.loads((f/'fixture.json').read_text());assert fixture['compile_exit']==0
 assert sha(f/'window-fixture')==fixture['binary_sha256'];artifacts[str(f/'window-fixture').removeprefix('/mnt/lfs')]=fixture['binary_sha256'];fixture_source_sha=fixture['source_sha256'];fixture=str(f/'window-fixture').removeprefix('/mnt/lfs')
asset_dirs=['testsuite','tests','data'] if syntax_only else ['tests' if component=='libadwaita' else 'testsuite']
assets={str(p.relative_to(s)):sha(p) for directory in asset_dirs for p in (s/directory).rglob('*') if p.is_file() and not p.is_symlink()}
assert s.stat().st_uid==0 and not s.stat().st_mode&0o022
record={'scope':'Frozen native '+component+' original display drivers only; no full GNOME/product acceptance','component':component,'syntax_only':syntax_only,'remaining_syntax':remaining_syntax,'syntax_cases':syntax_cases,'reused_partial_syntax':partial,'reused_native_proof':reused,'asset_dirs':asset_dirs,'builder_boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'fixture_source_sha256':fixture_source_sha,'fixture':fixture,'tests':tests,'test_env':registered[0]['env'],'artifacts':artifacts,'source_test_assets_sha256':hashlib.sha256(json.dumps(assets,sort_keys=True).encode()).hexdigest(),'source_test_files':len(assets),'schema_cache_sha256':sha(Path('/mnt/lfs/usr/share/glib-2.0/schemas/gschemas.compiled'))}
data=json.dumps(record,sort_keys=True).encode()+bytes([10])
folder=Path('/mnt/lfs/sources/phase2/native-fixtures')/('gtksourceview-syntax-valid-1' if remaining_syntax else 'gtksourceview-syntax-1' if syntax_only else 'mutter-1' if component=='libadwaita' else 'gtksourceview-1');folder.mkdir(mode=0o755,exist_ok=True)
assert folder.stat().st_uid==0 and not folder.is_symlink()
manifest=folder/'accepted.json'
if manifest.exists():
 assert manifest.is_file() and not manifest.is_symlink() and manifest.stat().st_uid==0
 assert manifest.read_bytes()==data,'Changed or partial manifest: reconcile before repeat'
else:
 with manifest.open('xb') as f:f.write(data);f.flush();__import__('os').fsync(f.fileno())
manifest.chmod(0o444)
print(json.dumps({'component':component,'syntax_only':syntax_only,'remaining_syntax':remaining_syntax,'manifest':str(manifest).removeprefix('/mnt/lfs'),'manifest_sha256':hashlib.sha256(data).hexdigest(),'fixture_source_sha256':record['fixture_source_sha256'],'builder_boot_id':record['builder_boot_id'],'tests':len(record['tests']),'artifacts':len(record['artifacts']),'source_test_files':record['source_test_files']}))
'''
    accepted=json.loads(subprocess.run(phase2_vm.ssh_args()+['python3 -'],input=code.encode(),capture_output=True,check=True).stdout)
    if args.component=='libadwaita':assert hashlib.sha256((ROOT/'scripts/build/phase2/native-gtk-window.c').read_bytes()).hexdigest()==accepted['fixture_source_sha256']
    body=(ROOT/'scripts/host/phase2-native-mutter-probe.py').read_text();suite=(ROOT/'scripts/build/phase2/native_mutter_suite.py').read_text()
    assert body.count('ACCEPTED = None')==body.count('SUITE_SOURCE = None')==1
    probe=body.replace('ACCEPTED = None','ACCEPTED = '+repr(accepted)).replace('SUITE_SOURCE = None','SUITE_SOURCE = '+repr(suite)).encode();bootstrap=compressed_payload(probe);assert bootstrap.count(b'toddy-native-glycin')==1;bootstrap=bootstrap.replace(b'toddy-native-glycin',b'toddy-native-mutter')
    context.mkdir();state={'scope':'Native7.1.8 headless Mutter/'+args.component+' only, B02 integrated desktop/G2 pending','commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'started_utc':datetime.now(timezone.utc).isoformat(),'controller_pid':os.getpid(),'controller_boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'controller_start_ticks':Path('/proc/self/stat').read_text().split()[21],'probe_sha256':hashlib.sha256(probe).hexdigest(),'payload_sha256':hashlib.sha256(bootstrap).hexdigest(),'accepted':accepted,'phase':'prepared'}
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
