#!/usr/bin/env python3
"""Validate fresh image account data with actual native Shadow in a private root."""
from pathlib import Path
import base64
import hashlib
import json
import os
import subprocess

os.chdir(Path(__file__).resolve().parents[2])
source = base64.b64encode(Path('scripts/build/h10/live_accounts.py').read_bytes()).decode()
runtime_source = base64.b64encode(Path('scripts/build/h10/initramfs_runtime.py').read_bytes()).decode()
baseline = json.loads(Path('config/live-account-baseline.json').read_text())
script = r'''from pathlib import Path
import base64,hashlib,json,os,shutil,stat,subprocess,sys,tempfile,types
sys.path.insert(0,'/opt/toddy-build/scripts/build')
root=Path('/mnt/lfs')
base=Path(tempfile.mkdtemp(prefix='toddy-live-accounts-',dir=root/'tmp'))
print('LIVE_ACCOUNTS_FIXTURE '+str(base),flush=True)
module=types.ModuleType('live_accounts');module.__file__='/opt/toddy-build/scripts/build/h10/live_accounts.py'
exec(compile(base64.b64decode(SOURCE),module.__file__,'exec'),module.__dict__)
baseline=BASELINE
runtime=types.ModuleType('initramfs_runtime');runtime.__file__='/opt/toddy-build/scripts/build/h10/initramfs_runtime.py'
exec(compile(base64.b64decode(RUNTIME),runtime.__file__,'exec'),runtime.__dict__)
prefix=['chroot',str(root),'/usr/bin/env','-i','PATH=/usr/bin:/usr/sbin','LC_ALL=C']
def native(program,*args):return subprocess.run(prefix+[program,*args],capture_output=True,text=True)
def digest(path):
 with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
before=digest(root/'var/lib/dpkg/status')
account_before={name:digest(root/'etc'/name) for name in ('passwd','group','shadow','gshadow','machine-id')}
try:
 target=base/'image'
 runtime.PROGRAMS=('/usr/bin/bash','/usr/bin/false','/usr/bin/getent','/usr/bin/id','/usr/sbin/chroot')
 runtime_report=runtime.stage_runtime(root,target,Path('/var/log/toddy/packages'))
 for directory in ('usr/bin','etc','dev','run/dbus'):(target/directory).mkdir(parents=True,exist_ok=True)
 for name,virtual in (('bash','/usr/bin/bash'),('coreutils','/usr/bin/false'),('shadow','/etc/login.defs')):
  identity=native('/usr/bin/dpkg-query','-W','-f=${Package}_${Version}_${Architecture}',name);identity.check_returncode()
  record=json.loads((Path('/var/log/toddy/packages')/(identity.stdout+'.json')).read_text())
  current=root/virtual.lstrip('/');assert digest(current)==record['payload'][virtual]['sha256']
  shutil.copy2(current,target/virtual.lstrip('/'))
 identity=native('/usr/bin/dpkg-query','-W','-f=${Package}_${Version}_${Architecture}','dbus');identity.check_returncode()
 dbus_record=json.loads((Path('/var/log/toddy/packages')/(identity.stdout+'.json')).read_text())
 dbus_source=root/'var/lib/dbus/machine-id';dbus_alias=target/'var/lib/dbus/machine-id'
 assert dbus_record['payload']['/var/lib/dbus/machine-id']['symlink']==dbus_source.readlink().as_posix()=='/etc/machine-id'
 dbus_alias.parent.mkdir(parents=True);shutil.copy2(dbus_source,dbus_alias,follow_symlinks=False)
 report=module.stage_accounts(target,baseline)
 assert report['canonical_dbus_alias_retained']
 checked=[]
 for program in ('pwck','grpck'):
  result=native('/usr/sbin/'+program,'--read-only','--root=/'+str(target.relative_to(root)))
  checked.append({'tool':program,'exit':result.returncode,'stdout':result.stdout,'stderr':result.stderr})
  (base/'native-shadow-checks.json').write_text(json.dumps(checked,indent=2)+'\n')
  result.check_returncode()
 assert report['users']==15 and report['groups']==35
 sandbox_environment={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C','HOME':'/nonexistent'}
 identity=subprocess.run(['chroot',str(target),'/usr/bin/getent','passwd','_apt'],
  env=sandbox_environment,text=True,capture_output=True,check=True)
 assert identity.stdout=='_apt:x:100:100:APT Package Acquisition:/nonexistent:/usr/bin/false\n'
 sandbox=prefix+['/usr/sbin/chroot','--userspec=_apt:_apt','--groups=_apt','/'+str(target.relative_to(root))]
 identity=subprocess.run(sandbox+['/usr/bin/id'],env=sandbox_environment,text=True,capture_output=True,check=True)
 assert identity.stdout.strip()=='uid=100(_apt) gid=100(_apt) groups=100(_apt)',identity.stdout
 partial=target/'var/cache/apt/archives/partial';partial.mkdir(parents=True);partial.chmod(0o700);os.chown(partial,100,100)
 protected=target/'etc/toddy-private-probe';protected.write_text('public protected fixture\n');protected.chmod(0o600)
 write=subprocess.run(sandbox+['/usr/bin/bash','--noprofile','--norc','-c',
  'printf "sandbox write\\n" > /var/cache/apt/archives/partial/probe'],env=sandbox_environment,capture_output=True,check=True)
 assert (partial/'probe').stat().st_uid==(partial/'probe').stat().st_gid==100
 read=subprocess.run(sandbox+['/usr/bin/bash','--noprofile','--norc','-c',
  'test -r /etc/toddy-private-probe'],env=sandbox_environment,capture_output=True)
 assert read.returncode==1
 assert (target/'etc/machine-id').read_bytes()==b''
 assert dbus_alias.is_symlink() and dbus_alias.readlink().as_posix()=='/etc/machine-id'
 for name,fields in (('shadow',9),('gshadow',4)):
  path=target/'etc'/name;assert path.stat().st_mode&0o777==0o600
  assert path.stat().st_uid==path.stat().st_gid==0
  rows=[line.split(':') for line in path.read_text().splitlines()]
  assert all(len(row)==fields and row[1]=='!' for row in rows)
  assert all(row[0]!='tester' for row in rows)
 rejected=[]
 for kind in ('existing-shadow','redirected-etc','nonempty-root-home','dbus-id-regular','dbus-id-other-link'):
  negative=base/kind;negative.mkdir()
  if kind=='existing-shadow':
   (negative/'etc').mkdir();sentinel=negative/'etc/shadow';sentinel.write_text('harmless preservation sentinel\n')
  elif kind=='redirected-etc':
   outside=base/'outside';outside.mkdir();sentinel=outside/'untouched';sentinel.write_text('harmless preservation sentinel\n');(negative/'etc').symlink_to(outside)
  elif kind=='nonempty-root-home':
   (negative/'root').mkdir();sentinel=negative/'root/keep';sentinel.write_text('harmless preservation sentinel\n')
  else:
   alias=negative/'var/lib/dbus/machine-id';alias.parent.mkdir(parents=True)
   sentinel=alias if kind=='dbus-id-regular' else alias.parent/'keep'
   sentinel.write_text('harmless preservation sentinel\n')
   if kind=='dbus-id-other-link':alias.symlink_to('keep')
  preserved=digest(sentinel)
  try:module.stage_accounts(negative,baseline)
  except ValueError as error:rejected.append({'case':kind,'reason':str(error)})
  else:raise AssertionError('Unexpected existing image state accepted')
  assert digest(sentinel)==preserved and not (negative/'etc/passwd').exists()
 assert digest(root/'var/lib/dpkg/status')==before
 assert {name:digest(root/'etc'/name) for name in account_before}==account_before
 print(json.dumps({'generated':report,'native_shadow_checks':checked,'negative_cases':rejected,
  'native_apt_account':{'identity':identity.stdout.strip(),'partial_download_write_exit':write.returncode,
   'protected_file_read_test_exit':read.returncode,'actual_apt_acquisition_tested':False},'native_runtime':runtime_report,
  'native_installed_status_and_accounts_unchanged':True,'fixture_removed_after_checks':True,
  'source_sha256':hashlib.sha256(base64.b64decode(SOURCE)).hexdigest(),
  'live_login_or_first_boot_claimed':False},indent=2))
except BaseException:
 print('Preserved live account fixture:',base,flush=True)
 raise
else:shutil.rmtree(base)
'''.replace('SOURCE', repr(source)).replace('BASELINE', repr(baseline)).replace('RUNTIME',repr(runtime_source))
result = subprocess.run(['python3', 'scripts/host/vm.py', 'ssh',
    'source /opt/toddy-build/scripts/build/target.sh; guard_target && python3 -'],
    input=script, text=True, capture_output=True)
path = Path('.local/logs/h10-live-accounts-probe.json')
data = (json.dumps({'exit': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr}, indent=2) + '\n').encode()
sha = hashlib.sha256(data).hexdigest()
path.with_name(path.stem + '.' + sha + '.json').write_bytes(data)
path.write_bytes(data)
print(result.stdout, result.stderr)
print('exit', result.returncode, 'SHA256', sha)
result.check_returncode()
