#!/usr/bin/env python3
"""Exercise real native Dpkg ownership transfer in two private package roots.

Uses actual own CPython payloads. Unpack states are deliberate: this proves
ownership handoff, not configured dependency closure or installed runtime use.
"""
from pathlib import Path
import base64
import hashlib
import json
import os
import subprocess

os.chdir(Path(__file__).resolve().parents[2])
partition_source = base64.b64encode(Path('scripts/build/h11/python_qa.py').read_bytes()).decode()
script = r'''from pathlib import Path
import base64,hashlib,json,os,re,shutil,stat,subprocess,tempfile,types
root=Path('/mnt/lfs')
prefix=['chroot',str(root),'/usr/bin/env','-i','PATH=/usr/bin:/usr/sbin','LC_ALL=C','DPKG_DEB_THREADS_MAX=2']
def native(program,*args,check=True):
 return subprocess.run(prefix+['/usr/bin/'+program,*args],check=check,capture_output=True,text=True)
def virtual(path):
 assert path.is_relative_to(root/'tmp')
 return '/'+str(path.relative_to(root))
def digest(path):
 with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
identity=native('dpkg-query','-W','-f=${Package}_${Version}_${Architecture}\t${Version}\t${Architecture}\t${Status}','python').stdout
stem,version,arch,status=identity.split('\t');assert status=='install ok installed'
record=json.loads((Path('/var/log/toddy/packages')/(stem+'.json')).read_text())
source=Path('/var/cache/toddy/packages')/(stem+'.deb')
assert digest(source)==record['archive_sha256']
installed_status_sha=digest(root/'var/lib/dpkg/status')
base=Path(tempfile.mkdtemp(prefix='toddy-python-qa-ownership-',dir=root/'tmp'))
print('PYTHON_QA_OWNERSHIP_FIXTURE '+str(base),flush=True)
module=types.ModuleType('python_qa');module.__file__='/opt/toddy-build/scripts/build/h11/python_qa.py'
exec(compile(base64.b64decode(PARTITION),module.__file__,'exec'),module.__dict__)
try:
 original=base/'original.deb';shutil.copyfile(source,original)
 runtime=base/'runtime';qa=base/'qa'
 native('dpkg-deb','--raw-extract',virtual(original),virtual(runtime))
 controls=runtime/'DEBIAN'
 assert {p.name for p in controls.iterdir()}<={'control','md5sums','conffiles'}
 old_control=(controls/'control').read_text()
 old_dependencies=native('dpkg-deb','-f',virtual(original),'Depends').stdout.strip()
 revision=re.search(r'\+toddy([1-9][0-9]*)$',version)
 new_version=(version[:revision.start()]+'+toddy'+str(int(revision[1])+1)) if revision else version+'+toddy1'
 native('dpkg','--compare-versions',new_version,'gt',version)
 partition=module.partition(runtime,qa)
 expected=module.manifest(qa)
 qa_files={name:entry for name,entry in expected.items() if 'sha256' in entry or 'link' in entry}
 assert qa_files
 # Preserve the original runtime dependency and conffile contracts. Stale
 # optional md5sums are removed from these private rebuilt package controls.
 for item in (controls/'md5sums',):
  if item.exists():item.unlink()
 rewritten,count=re.subn(r'^Version: .+$','Version: '+new_version,old_control,flags=re.M);assert count==1
 (controls/'control').write_text(rewritten)
 (qa/'DEBIAN').mkdir()
 (qa/'DEBIAN/control').write_text('Package: python-test-support\nVersion: '+new_version+'\nArchitecture: '+arch+'\nMaintainer: Toddy OS Development <noreply@example.invalid>\nDepends: python (= '+new_version+')\nDescription: Private native CPython QA ownership experiment\n')
 notice=qa/'usr/share/doc/python-test-support/copyright';notice.parent.mkdir(parents=True)
 shutil.copy2(runtime/'usr/share/doc/python/copyright',notice)
 core_deb=base/'runtime.deb';qa_deb=base/'qa.deb'
 native('dpkg-deb','--build',virtual(runtime),virtual(core_deb))
 native('dpkg-deb','--build',virtual(qa),virtual(qa_deb))
 assert native('dpkg-deb','-f',virtual(core_deb),'Depends').stdout.strip()==old_dependencies
 logs=[]
 def unpack(destination,package,check=True):
  assert destination.parent==base and destination.name in ('wrong-order','correct-order')
  db=destination/'var/lib/dpkg';db.mkdir(parents=True,exist_ok=True);(db/'status').touch(exist_ok=True)
  result=native('dpkg','--root='+virtual(destination),'--unpack',virtual(package),check=False)
  logs.append({'root':destination.name,'archive':package.name,'exit':result.returncode,'stdout':result.stdout,'stderr':result.stderr})
  if check:result.check_returncode()
  return result
 def listing(destination,package):
  p=destination/'var/lib/dpkg/info'/(package+'.list')
  return set(p.read_text().splitlines()) if p.exists() else set()
 wrong=base/'wrong-order';unpack(wrong,original)
 rejected=unpack(wrong,qa_deb,check=False)
 assert rejected.returncode!=0 and 'trying to overwrite' in rejected.stderr
 for name,entry in qa_files.items():
  p=wrong/name.lstrip('/')
  if 'sha256' in entry:assert digest(p)==entry['sha256'],name
  else:assert p.readlink().as_posix()==entry['link'],name
 correct=base/'correct-order';unpack(correct,original)
 assert set(qa_files)<=listing(correct,'python')
 unpack(correct,core_deb)
 assert not (set(qa_files)&listing(correct,'python'))
 assert not any((correct/name.lstrip('/')).exists() or (correct/name.lstrip('/')).is_symlink() for name in qa_files)
 # This is the recoverable interruption boundary. Both new archives and the
 # original source-built archive still exist outside the temporary package DB.
 assert digest(original)==record['archive_sha256'] and qa_deb.is_file()
 unpack(correct,qa_deb)
 assert set(qa_files)<=listing(correct,'python-test-support')
 assert not (set(qa_files)&listing(correct,'python'))
 for name,entry in qa_files.items():
  p=correct/name.lstrip('/');info=p.lstat()
  assert (info.st_mode,info.st_uid,info.st_gid)==(entry['mode'],entry['uid'],entry['gid']),name
  assert info.st_mtime_ns==entry['mtime_ns'],name
  if 'sha256' in entry:assert digest(p)==entry['sha256'],name
  else:assert p.readlink().as_posix()==entry['link'],name
 states=native('dpkg-query','--admindir='+virtual(correct/'var/lib/dpkg'),'-W','-f=${Package}\t${Version}\t${Status}\n').stdout
 assert len(states.splitlines())==2 and all(line.endswith('install ok unpacked') for line in states.splitlines()),states
 assert digest(root/'var/lib/dpkg/status')==installed_status_sha
 print(json.dumps({'source_package':stem,'source_archive_sha256':record['archive_sha256'],
  'new_version':new_version,'partition':partition,'transferred_file_count':len(qa_files),
  'runtime_dependencies_preserved':True,'compressor_thread_limit':2,
  'wrong_order_rejected_without_overwriting_original_qa':True,
  'core_relinquished_before_qa_received':True,'recovery_archives_present_at_intermediate_boundary':True,
  'new_archive_sha256':{'runtime':digest(core_deb),'qa':digest(qa_deb)},'private_package_states':states,
  'native_installed_status_unchanged':True,'configured_runtime_acceptance':False,
  'logs':logs,'fixture_removed_after_checks':True},indent=2))
except BaseException:
 print('Preserved Python QA ownership fixture:',base,flush=True)
 raise
else:shutil.rmtree(base)
'''.replace('PARTITION', repr(partition_source))
r = subprocess.run(['python3', 'scripts/host/vm.py', 'ssh',
                    'source /opt/toddy-build/scripts/build/target.sh; guard_target && python3 -'],
                   input=script, text=True, capture_output=True)
p = Path('.local/logs/h11-python-qa-ownership-probe.json')
data = (json.dumps({'exit': r.returncode, 'stdout': r.stdout, 'stderr': r.stderr}, indent=2) + '\n').encode()
sha = hashlib.sha256(data).hexdigest()
p.with_name(p.stem + '.' + sha + '.json').write_bytes(data)
p.write_bytes(data)
print(r.stdout, r.stderr)
print('exit', r.returncode, 'SHA256', sha)
r.check_returncode()
