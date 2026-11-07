#!/usr/bin/env python3
"""Exercise explicit native root copying with real metadata and negative cases."""
from pathlib import Path
import base64
import hashlib
import json
import os
import subprocess

os.chdir(Path(__file__).resolve().parents[2])
source = base64.b64encode(Path('scripts/build/h10/copy_selected_root.py').read_bytes()).decode()
script = r'''from pathlib import Path
import base64,hashlib,json,os,shutil,subprocess,sys,tempfile,types
sys.path.insert(0,'/opt/toddy-build/scripts/build')
from package_backend import PackageBackend
root=Path('/mnt/lfs');backend=PackageBackend(root)
base=Path(tempfile.mkdtemp(prefix='toddy-selected-root-copy-',dir=root/'tmp'))
print('SELECTED_ROOT_COPY_FIXTURE '+str(base),flush=True)
module=types.ModuleType('copy_selected_root');module.__file__='/opt/toddy-build/scripts/build/h10/copy_selected_root.py'
exec(compile(base64.b64decode(SOURCE),module.__file__,'exec'),module.__dict__)
def digest(path):
 with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
before=digest(root/'var/lib/dpkg/status')
source=base/'source';source.mkdir()
try:
 for directory in ('usr/bin','usr/share/example','omitted-tree','cross'):(source/directory).mkdir(parents=True)
 native_true=root/'usr/bin/true'
 identity=backend.run('dpkg-query','-W','-f=${Package}_${Version}_${Architecture}','coreutils',capture_output=True,text=True).stdout
 record=json.loads((Path('/var/log/toddy/packages')/(identity+'.json')).read_text())
 assert digest(native_true)==record['payload']['/usr/bin/true']['sha256']
 helper=source/'usr/bin/helper';shutil.copy2(native_true,helper);os.chown(helper,0,18);helper.chmod(0o4750)
 backend.run('setfacl','-m','u:101:r-x','/'+str(helper.relative_to(root)))
 os.link(helper,source/'usr/bin/helper-link')
 capability=source/'usr/bin/capability';shutil.copy2(native_true,capability)
 subprocess.run(['chroot',str(root),'/usr/sbin/setcap','cap_net_bind_service=ep','/'+str(capability.relative_to(root))],check=True)
 text=source/'usr/share/example/space λ\nline';text.write_bytes(b'public metadata fixture\n');os.chown(text,18,18);text.chmod(0o640)
 os.setxattr(text,'user.toddy-copy-test',b'public fixture attribute')
 os.utime(text,ns=(1600000000123456789,1600000000123456789))
 backend.run('setfacl','-m','d:u:101:r-x','/'+str((source/'usr/share/example').relative_to(root)))
 (source/'usr/bin/alias').symlink_to('helper')
 option='--checkpoint-action=exec=touch OPTION_EXECUTED';(source/option).write_text('literal filename only\n')
 sparse=source/'usr/share/example/sparse';sparse.touch()
 with sparse.open('r+b') as stream:stream.seek(16*1024*1024);stream.write(b'end')
 (source/'usr/share/example/omitted.txt').write_text('omitted sentinel\n')
 (source/'omitted-tree/private.txt').write_text('omitted subtree sentinel\n')
 outside=base/'outside';outside.mkdir();(outside/'keep').write_text('outside preservation sentinel\n')
 (source/'redirect').symlink_to(outside)
 fifo=source/'omitted.fifo';os.mkfifo(fifo)
 omitted={'cross','omitted-tree','omitted-tree/private.txt','usr/share/example/omitted.txt','omitted.fifo','redirect'}
 names=[name for name in module.tree_names(source) if name not in omitted]
 rejected=[]
 for label,inventory in [('traversal',['.','../outside']),('redirected-parent',['.','redirect','redirect/keep']),('special-node',['.','omitted.fifo'])]:
  dest=base/('rejected-'+label);work=base/('work-'+label)
  try:module.copy_selected(backend,source,dest,work,inventory)
  except ValueError as error:rejected.append({'case':label,'reason':str(error)})
  else:raise AssertionError('Unsafe source selection accepted')
  assert not dest.exists() and not work.exists()
 # This whole probe is in a private mount namespace. No global mount changes.
 cross=source/'cross'
 subprocess.run(['mount','-t','tmpfs','-o','size=1M','tmpfs',str(cross)],check=True)
 try:
  try:module.copy_selected(backend,source,base/'rejected-cross',base/'work-cross',['.','cross'])
  except ValueError as error:rejected.append({'case':'cross-filesystem','reason':str(error)})
  else:raise AssertionError('Cross-filesystem path accepted')
  assert not (base/'rejected-cross').exists() and not (base/'work-cross').exists()
 finally:subprocess.run(['umount',str(cross)],check=True)
 expected=module.snapshot(source,names)
 destination=base/'image';work=base/'copy-work'
 report=module.copy_selected(backend,source,destination,work,names)
 assert json.loads((work/report['input_manifest']).read_text())==expected
 assert digest(work/report['input_manifest'])==report['input_manifest_sha256']
 assert not (destination/'usr/share/example/omitted.txt').exists()
 assert not (destination/'omitted-tree').exists() and not (destination/'OPTION_EXECUTED').exists()
 assert not (source/'OPTION_EXECUTED').exists()
 assert os.stat(destination/'usr/bin/helper').st_ino==os.stat(destination/'usr/bin/helper-link').st_ino
 assert (destination/'usr/bin/helper').stat().st_mode&0o7777==0o4750
 assert os.getxattr(destination/'usr/bin/capability','security.capability')==os.getxattr(capability,'security.capability')
 acl=backend.run('getfacl','-n','-p','/'+str((destination/'usr/bin/helper').relative_to(root)),capture_output=True,text=True).stdout
 assert 'user:101:r-x' in acl
 assert (destination/'usr/share/example/sparse').stat().st_blocks*512 < (destination/'usr/share/example/sparse').stat().st_size
 assert module.snapshot(source,names)==expected
 try:module.copy_selected(backend,source,destination,base/'unused-work',names)
 except ValueError as error:rejected.append({'case':'existing-stage','reason':str(error)})
 else:raise AssertionError('Existing copied root was overwritten')
 assert module.snapshot(destination,module.tree_names(destination))==expected
 assert (outside/'keep').read_text()=='outside preservation sentinel\n'
 assert digest(root/'var/lib/dpkg/status')==before
 print(json.dumps({'copy':report,'negative_cases':rejected,'sparse_storage_preserved':True,
  'access_acl':acl,'default_acl_and_all_xattrs_equal':True,'capability_xattr_equal':True,
  'unselected_siblings_and_subtree_absent':True,'literal_option_filename_not_executed':True,
  'logs':{name:(work/name).read_text() for name in ('create.log','extract.log')},
  'native_installed_status_unchanged':True,'fixture_removed_after_checks':True,
  'source_sha256':hashlib.sha256(base64.b64decode(SOURCE)).hexdigest()},indent=2))
except BaseException:
 print('Preserved selected-copy fixture:',base,flush=True)
 raise
else:shutil.rmtree(base)
'''.replace('SOURCE', repr(source))
result = subprocess.run(['python3', 'scripts/host/vm.py', 'ssh',
    'source /opt/toddy-build/scripts/build/target.sh; guard_target && unshare --mount --propagation private python3 -'],
    input=script, text=True, capture_output=True)
path = Path('.local/logs/h10-selected-root-copy-probe.json')
data = (json.dumps({'exit': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr}, indent=2) + '\n').encode()
sha = hashlib.sha256(data).hexdigest()
path.with_name(path.stem + '.' + sha + '.json').write_bytes(data)
path.write_bytes(data)
print(result.stdout, result.stderr)
print('exit', result.returncode, 'SHA256', sha)
result.check_returncode()
