#!/usr/bin/env python3
"""Exercise native image ACL capture and restore in disposable guest fixtures."""
from pathlib import Path
import base64
import hashlib
import json
import os
import subprocess

os.chdir(Path(__file__).resolve().parents[2])
source = base64.b64encode(Path('scripts/build/h10/acl_sidecar.py').read_bytes()).decode()
script = r'''from pathlib import Path
import base64,hashlib,json,os,shutil,stat,subprocess,sys,tempfile,types
sys.path.insert(0,'/opt/toddy-build/scripts/build')
from package_backend import PackageBackend
root=Path('/mnt/lfs');backend=PackageBackend(root)
base=Path(tempfile.mkdtemp(prefix='toddy-acl-capture-',dir=root/'tmp'));base.chmod(0o755)
print('ACL_CAPTURE_FIXTURE '+str(base),flush=True)
module=types.ModuleType('acl_sidecar');module.__file__='/opt/toddy-build/scripts/build/h10/acl_sidecar.py'
exec(compile(base64.b64decode(SOURCE),module.__file__,'exec'),module.__dict__)
mounted=[]
def virtual(path):return '/'+str(path.relative_to(root))
def dump(image):
 return backend.run('bash','--noprofile','--norc','-c',
  'cd -- "$1" && exec /usr/bin/getfacl -R -P -p -n --skip-base --one-file-system .',
  'probe',virtual(image),capture_output=True).stdout
def blocks(data):
 return {module.decode_name(block.split(b'\n')[0][8:]):block
  for block in data.split(b'\n\n') if block}
def reader(path,operation='-r'):
 return subprocess.run(['chroot',str(root),'/usr/sbin/chroot','--userspec=101:101','--groups=101','/',
  '/usr/bin/test',operation,virtual(path)],capture_output=True).returncode
try:
 image=base/'image';(image/'usr/share/toddy').mkdir(parents=True)
 image.chmod(0o755)
 filename='payload ação\ncarriage\rslash\\012'
 payload=image/filename;payload.write_text('public ACL fixture\n');os.chown(payload,18,18)
 backend.run('setfacl','-m','u:101:r--',virtual(payload));payload.chmod(0o4750)
 os.link(payload,image/'linked')
 default=image/'default';default.mkdir(mode=0o750);os.chown(default,18,18)
 backend.run('setfacl','-m','u:101:r-x,d:u:101:r-x',virtual(default))
 backend.run('setfacl','-m','d:u:101:r-x',virtual(image/'usr/share/toddy'))
 outside=base/'outside';outside.mkdir();external=outside/'outside-only';external.write_text('public outside fixture\n')
 backend.run('setfacl','-m','u:101:r--',virtual(external))
 (image/'outside-link').symlink_to(outside)
 outside_before=module.metadata(outside)
 expected=dump(image);first=module.stage_acl(backend,image)
 assert (image/module.SIDECAR).read_bytes()==expected
 assert module.metadata(outside)==outside_before and 'outside-only' not in first['acl_paths']
 assert len(first['acl_paths'])==4,first
 assert not os.listxattr(image/module.SIDECAR)
 restored=base/'restored';shutil.copytree(image,restored,symlinks=True)
 (restored/'linked').unlink();os.link(restored/filename,restored/'linked')
 for path in [restored,*restored.rglob('*')]:
  if path.is_symlink():continue
  for attr in ('system.posix_acl_access','system.posix_acl_default'):
   if attr in os.listxattr(path):os.removexattr(path,attr)
  original=image/path.relative_to(restored)
  os.chown(path,0,0);path.chmod(stat.S_IMODE(original.stat().st_mode))
 assert reader(restored/filename)==1
 result=backend.run('bash','--noprofile','--norc','-c',
  'cd -- "$1" && exec /usr/bin/setfacl -P --restore=usr/share/toddy/live-root.acl',
  'probe',virtual(restored),capture_output=True)
 assert not result.stdout and not result.stderr
 assert blocks(dump(restored))==blocks(expected)
 assert reader(restored/filename)==0 and reader(restored/filename,'-x')==1
 info=(restored/filename).stat();assert (info.st_uid,info.st_gid,stat.S_IMODE(info.st_mode))==(18,18,0o4750)
 assert info.st_ino==(restored/'linked').stat().st_ino
 assert (restored/filename).read_bytes()==payload.read_bytes()
 assert module.metadata(outside)==outside_before
 blank=base/'blank';(blank/'usr/share/toddy').mkdir(parents=True)
 empty=module.stage_acl(backend,blank);assert empty['bytes']==0 and empty['acl_paths']==[]
 result=backend.run('bash','--noprofile','--norc','-c',
  'cd -- "$1" && exec /usr/bin/setfacl -P --restore=usr/share/toddy/live-root.acl',
  'probe',virtual(blank),capture_output=True)
 assert not result.stdout and not result.stderr
 refused=[]
 for case in ('existing-sidecar','partial-sidecar','redirected-parent','special-node','filesystem-boundary'):
  target=base/case;(target/'usr/share/toddy').mkdir(parents=True)
  destination=target/module.SIDECAR
  if case=='existing-sidecar':destination.write_text('public existing metadata\n')
  elif case=='partial-sidecar':destination.with_name('.live-root.acl.part').write_text('public partial metadata\n')
  elif case=='redirected-parent':
   destination.parent.rmdir();destination.parent.symlink_to(outside)
  elif case=='special-node':os.mkfifo(target/'fixture-fifo')
  else:
   mountpoint=target/'mounted';mountpoint.mkdir()
   subprocess.run(['mount','-t','tmpfs','-o','size=1m','tmpfs',str(mountpoint)],check=True);mounted.append(mountpoint)
  previous=destination.read_bytes() if destination.exists() else None
  try:module.stage_acl(backend,target)
  except ValueError as error:refused.append({'case':case,'reason':str(error)})
  else:raise AssertionError('Unreviewed ACL stage accepted: '+case)
  assert (destination.read_bytes() if destination.exists() else None)==previous
  if mounted:subprocess.run(['umount',str(mounted.pop())],check=True)
 malformed=[]
 for name in (b'/etc/shadow',b'../escape',b'./../escape',b'a//b',b'\\057escape',b'bad\\q',b'',b'././file'):
  try:module.decode_name(name)
  except ValueError:malformed.append(name.decode())
  else:raise AssertionError('Unsafe/non-native ACL header accepted')
 expected_metadata=module.metadata(image)
 stream_refusals=[]
 for case,data in (('wrong-owner',expected.replace(b'# owner: 18',b'# owner: 0',1)),
                   ('duplicate-record',expected+expected),('missing-record',b'')):
  try:module.validate_stream(data,expected_metadata)
  except ValueError as error:stream_refusals.append({'case':case,'reason':str(error)})
  else:raise AssertionError('Changed ACL stream accepted: '+case)
 print(json.dumps({'capture':first,'empty_capture':empty,'native_restore_exit':result.returncode,
  'named_user_read_before':1,'named_user_read_after':0,'named_user_execute_after':1,
  'restored_uid_gid_mode':[info.st_uid,info.st_gid,oct(stat.S_IMODE(info.st_mode))],
  'hardlink_identity_preserved':True,'payload_unchanged':True,'outside_symlink_target_unchanged':True,
  'default_acl_and_escaped_filename_roundtrip':True,'generated_sidecar_has_no_inherited_acl':True,
  'negative_cases':refused,'malformed_header_refusals':malformed,'altered_stream_refusals':stream_refusals,
  'source_sha256':hashlib.sha256(base64.b64decode(SOURCE)).hexdigest(),
  'fixture_removed_after_checks':True,'squashfs_or_overlay_tested':False,'native_kernel_boot_verified':False},indent=2))
except BaseException:
 print('Preserved ACL capture fixture: '+str(base),flush=True)
 raise
finally:
 for path in reversed(mounted):subprocess.run(['umount',str(path)],check=True)
shutil.rmtree(base)
'''.replace('SOURCE', repr(source))
result = subprocess.run(['python3', 'scripts/host/vm.py', 'ssh',
    'source /opt/toddy-build/scripts/build/target.sh; guard_target && unshare --mount --propagation private python3 -'],
    input=script, text=True, capture_output=True)
path = Path('.local/logs/h10-acl-capture-probe.json')
data = (json.dumps({'exit': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr}, indent=2) + '\n').encode()
sha = hashlib.sha256(data).hexdigest()
path.with_name(path.stem + '.' + sha + '.json').write_bytes(data)
path.write_bytes(data)
print(result.stdout, result.stderr)
print('exit', result.returncode, 'SHA256', sha)
result.check_returncode()
