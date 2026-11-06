#!/usr/bin/env python3
"""Validate a private copy of actual native package metadata and lock behavior."""
from pathlib import Path
import base64
import hashlib
import json
import os
import subprocess

os.chdir(Path(__file__).resolve().parents[2])
source = base64.b64encode(Path('scripts/build/h10/package_database.py').read_bytes()).decode()
script = r'''from pathlib import Path
import base64,hashlib,json,os,shutil,subprocess,sys,tempfile,types
sys.path.insert(0,'/opt/toddy-build/scripts/build')
from package_backend import PackageBackend
root=Path('/mnt/lfs');backend=PackageBackend(root)
base=Path(tempfile.mkdtemp(prefix='toddy-package-database-',dir=root/'tmp'))
print('PACKAGE_DATABASE_FIXTURE '+str(base),flush=True)
module=types.ModuleType('package_database');module.__file__='/opt/toddy-build/scripts/build/h10/package_database.py'
exec(compile(base64.b64decode(SOURCE),module.__file__,'exec'),module.__dict__)
source_before=module.snapshot(root/'var/lib/dpkg')
try:
 destination=base/'database'
 report=module.stage_database(backend,destination,Path('/var/log/toddy/packages'))
 records={}
 identities=backend.run('dpkg-query','-W','-f='+module.QUERY,capture_output=True,text=True).stdout
 for line in identities.splitlines():
  name,version,architecture,status=line.split('\t')
  assert status=='install ok installed'
  records[name]=json.loads((Path('/var/log/toddy/packages')/f'{name}_{version}_{architecture}.json').read_text())
 # Real root-image payload includes Dpkg's owned empty directory tree. Repeat
 # against exactly those recorded directories instead of deleting owned paths.
 owned=base/'owned-layout';owned.mkdir(mode=0o755)
 for name,row in records['dpkg']['payload'].items():
  if name.startswith('/var/lib/dpkg/'):
   assert row=={'mode':16877,'uid':0,'gid':0,'directory':True}
   path=owned/name.removeprefix('/var/lib/dpkg/');path.mkdir(parents=True,exist_ok=True);path.chmod(0o755)
 owned_report=module.stage_database(backend,owned,Path('/var/log/toddy/packages'))
 assert owned_report['files']==report['files'] and len(owned_report['retained_empty_directories'])==10
 virtual='/'+str(destination.relative_to(root))
 ownership=backend.run('dpkg-query','--admindir='+virtual,'--search',
  '/usr/bin/bash','/usr/bin/dpkg','/usr/bin/python3.14','/usr/lib/systemd/systemd',capture_output=True,text=True)
 assert set(ownership.stdout.splitlines())=={'bash: /usr/bin/bash','dpkg: /usr/bin/dpkg',
  'python: /usr/bin/python3.14','systemd: /usr/lib/systemd/systemd'}
 rejected=[]
 for case in ('pending-update','pending-trigger','unknown-maintainer-program','redirected-info','file-list-conflict','checksum-namespace-conflict'):
  negative=base/case;shutil.copytree(destination,negative)
  if case=='pending-update':
   path=negative/'updates/0000';path.write_text('public interrupted transaction fixture\n')
  elif case=='pending-trigger':
   path=negative/'triggers/Unincorp';path.write_text('public pending trigger fixture\n')
  elif case=='unknown-maintainer-program':
   path=negative/'info/bash.postinst';path.write_text('public unexpected program fixture\n')
  elif case=='redirected-info':
   path=negative/'info/bash.list';path.unlink();path.symlink_to(destination/'info/bash.list')
  elif case=='file-list-conflict':
   path=negative/'info/bash.list';path.write_text(path.read_text()+'/unexpected-native-owner\n')
  else:
   path=negative/'info/bash.md5sums';path.write_text(path.read_text()+'0'*32+'  unexpected-native-file\n')
  saved=path.readlink().as_posix() if path.is_symlink() else module.digest(path)
  try:module.validate_info(negative,records,module.snapshot(negative))
  except ValueError as error:rejected.append({'case':case,'reason':str(error)})
  else:raise AssertionError('Unexpected database state accepted: '+case)
  assert (path.readlink().as_posix() if path.is_symlink() else module.digest(path))==saved
 for case,path in (('existing-destination',destination),('redirected-destination',base/'alias/new'),('outside-destination',root/'var/lib/new-database')):
  if case=='redirected-destination':(base/'alias').symlink_to(destination)
  try:module.stage_database(backend,path,Path('/var/log/toddy/packages'))
  except ValueError as error:rejected.append({'case':case,'reason':str(error)})
  else:raise AssertionError('Unsafe database destination accepted')
 # Exercise the real Dpkg writer against a disposable root, never /mnt/lfs's
 # installed database. No package action may pass its lock acquisition.
 lockroot=base/'lock-root';private=lockroot/'var/lib/dpkg';private.parent.mkdir(parents=True)
 shutil.copytree(destination,private)
 for name in module.LOCKS:(private/name).touch(mode=0o640)
 with module.database_lock(private):
  # Snapshot must not accidentally release POSIX locks by reopening/closing a
  # lock inode. The subsequent real writer proves exclusion still holds.
  locked_snapshot=module.snapshot(private)
  result=subprocess.run(['chroot',str(root),'/usr/bin/env','-i','PATH=/usr/bin:/usr/sbin','LC_ALL=C',
   '/usr/bin/dpkg','--root=/'+str(lockroot.relative_to(root)),'--configure','--pending'],
   stdin=subprocess.DEVNULL,text=True,capture_output=True,timeout=10)
  (base/'native-lock-refusal.log').write_text(result.stdout+result.stderr)
  assert result.returncode!=0 and 'lock' in result.stderr.lower(),(result.returncode,result.stdout,result.stderr)
  assert module.snapshot(private)==locked_snapshot
 # A separately held POSIX write lock must also refuse the copy's read lock.
 locker=subprocess.Popen(['python3','-u','-c',
  'import fcntl,sys; f=open(sys.argv[1],"r+"); fcntl.lockf(f,fcntl.LOCK_EX); print("LOCKED",flush=True); sys.stdin.read()',
  str(private/'lock-frontend')],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
 try:
  assert locker.stdout.readline().strip()=='LOCKED'
  try:
   with module.database_lock(private):raise AssertionError('Active writer was not excluded')
  except ValueError as error:writer_refusal=str(error)
 finally:
  locker.stdin.close();locker.wait(timeout=5)
 assert locker.returncode==0
 assert module.snapshot(root/'var/lib/dpkg')==source_before
 full=(json.dumps(report,indent=2)+'\n').encode();(base/'database-report.json').write_bytes(full)
 print(json.dumps({'database':{k:v for k,v in report.items() if k not in ('files','record_sha256')},
  'owned_empty_layout_retained':owned_report['retained_empty_directories'],
  'complete_database_report_sha256':hashlib.sha256(full).hexdigest(),
  'native_ownership_query':ownership.stdout,'native_writer_refusal':{'exit':result.returncode,'stdout':result.stdout,'stderr':result.stderr},
  'active_writer_read_lock_refusal':writer_refusal,'negative_cases':rejected,
  'source_sha256':hashlib.sha256(base64.b64decode(SOURCE)).hexdigest(),
  'installed_database_unchanged':True,'fixture_removed_after_checks':True,
  'full_report':report},indent=2))
except BaseException:
 print('Preserved package database fixture: '+str(base),flush=True)
 raise
else:shutil.rmtree(base)
'''.replace('SOURCE', repr(source))
result = subprocess.run(['python3', 'scripts/host/vm.py', 'ssh',
    'source /opt/toddy-build/scripts/build/target.sh; guard_target && python3 -'],
    input=script, text=True, capture_output=True)
path = Path('.local/logs/h10-package-database-probe.json')
data = (json.dumps({'exit': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr}, indent=2) + '\n').encode()
sha = hashlib.sha256(data).hexdigest()
path.with_name(path.stem + '.' + sha + '.json').write_bytes(data)
path.write_bytes(data)
print(result.stdout, result.stderr)
print('exit', result.returncode, 'SHA256', sha)
result.check_returncode()
