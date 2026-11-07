#!/usr/bin/env python3
"""Check live profile transformation with native Findmnt/Systemd/Glibc tools."""
from pathlib import Path
import base64
import hashlib
import json
import os
import subprocess

os.chdir(Path(__file__).resolve().parents[2])
paths = {'live_configuration.py': 'scripts/build/h10/live_configuration.py',
         'initramfs_runtime.py': 'scripts/build/h10/initramfs_runtime.py',
         'stage_config.py': 'scripts/build/h08/stage_config.py',
         'LICENSES/LFS-MIT.txt': 'LICENSES/LFS-MIT.txt',
         'config/books.lock.json': 'config/books.lock.json'}
sources = {name: base64.b64encode(Path(path).read_bytes()).decode() for name, path in paths.items()}
script = r'''from pathlib import Path
import base64,hashlib,json,os,shutil,stat,subprocess,sys,tempfile,types
sys.path.insert(0,'/opt/toddy-build/scripts/build')
from package_backend import PackageBackend
root=Path('/mnt/lfs');backend=PackageBackend(root)
base=Path(tempfile.mkdtemp(prefix='toddy-live-configuration-',dir=root/'tmp'))
print('LIVE_CONFIGURATION_FIXTURE '+str(base),flush=True)
project=base/'project';project.mkdir()
for name,content in SOURCES.items():
 path=project/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(base64.b64decode(content))
for name in ('live_configuration','initramfs_runtime','stage_config'):
 module=types.ModuleType(name);module.__file__='/opt/toddy-build/scripts/build/'+('h08/' if name=='stage_config' else 'h10/')+name+'.py'
 sys.modules[name]=module
 exec(compile((project/(name+'.py')).read_bytes(),module.__file__,'exec'),module.__dict__)
live=sys.modules['live_configuration'];runtime=sys.modules['initramfs_runtime'];config=sys.modules['stage_config']
config.ROOT=project
def state(path):
 if path.is_symlink():return {'symlink':path.readlink().as_posix()}
 if path.is_file():return {'sha256':live.digest(path)}
 return {'absent':not path.exists()}
originals=('etc/fstab','etc/resolv.conf','etc/localtime','var/lib/dpkg/status')
before={name:state(root/name) for name in originals}
try:
 config_stage=base/'base-config';config.stage_configuration(config_stage)
 expected=live.digest(config_stage/'etc/fstab')
 links=json.loads((config_stage/'usr/share/toddy/base-config/default-links.json').read_text())
 runtime.PROGRAMS=('/usr/bin/bash','/usr/bin/findmnt','/usr/bin/date',
  '/usr/lib/systemd/system-generators/systemd-fstab-generator')
 image=base/'image';runtime_report=runtime.stage_runtime(root,image,Path('/var/log/toddy/packages'))
 shutil.copytree(config_stage,image,dirs_exist_ok=True)
 owners=runtime.installed_records(root,Path('/var/log/toddy/packages'))
 def add_timezone(destination):
  path=destination/'usr/share/zoneinfo/UTC';path.parent.mkdir(parents=True,exist_ok=True)
  original=root/'usr/share/zoneinfo/UTC'
  assert live.digest(original)==owners['/usr/share/zoneinfo/UTC'][3]['sha256']
  shutil.copy2(original,path)
 add_timezone(image)
 unit='/usr/lib/systemd/system/systemd-remount-fs.service'
 assert live.digest(root/unit[1:])==owners[unit][3]['sha256']
 path=image/unit[1:];path.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(root/unit[1:],path)
 report=live.stage_live_configuration(backend,image,expected,links)
 assert (image/'etc/fstab').read_text()==live.LIVE_FSTAB
 assert not any(line.strip() and not line.lstrip().startswith('#') for line in (image/'etc/fstab').read_text().splitlines())
 assert (image/'etc/resolv.conf').readlink().as_posix()=='/run/systemd/resolve/stub-resolv.conf'
 assert not (image/'run/systemd/resolve/stub-resolv.conf').exists()
 environment={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C','HOME':'/root',
  'SYSTEMD_PROC_CMDLINE':'toddy.live console=ttyS0,115200','SYSTEMD_IN_INITRD':'0'}
 def native(name,args):
  result=subprocess.run(['chroot',str(image),*args],env=environment,text=True,capture_output=True,timeout=20)
  (base/(name+'.log')).write_text(result.stdout+result.stderr)
  assert result.returncode==0,(name,result.returncode,result.stdout,result.stderr)
  return {'exit':result.returncode,'stdout':result.stdout,'stderr':result.stderr}
 findmnt=native('findmnt',['/usr/bin/findmnt','--verify','--verbose','--tab-file','/etc/fstab'])
 timezone=native('date',['/usr/bin/date','+%z'])
 assert timezone['stdout'].strip()=='+0000'
 for name in ('generator','generator.early','generator.late'):(image/'run'/name).mkdir()
 generator=native('fstab-generator',['/usr/lib/systemd/system-generators/systemd-fstab-generator',
  '/run/generator','/run/generator.early','/run/generator.late'])
 generated={str(path.relative_to(image/'run')):path.readlink().as_posix()
  for path in (image/'run').rglob('*') if path.is_symlink()}
 assert generated=={'generator/local-fs.target.wants/systemd-remount-fs.service':unit},generated
 assert not any(path.is_file() and not path.is_symlink() for path in (image/'run').rglob('*'))
 assert (image/'etc/fstab').read_text()==live.LIVE_FSTAB
 refused=[]
 for case in ('changed-fstab','existing-resolver','existing-timezone-link','redirected-etc','runtime-data',
              'redirected-runtime','changed-timezone','interrupted-partial','wrong-base-hash','unreviewed-links','hardlinked-fstab'):
  negative=base/case;shutil.copytree(config_stage,negative);(negative/'run').mkdir();add_timezone(negative)
  expected_input=expected;selected_links=dict(links)
  if case=='changed-fstab':
   path=negative/'etc/fstab';path.write_text(path.read_text()+'# public changed input\n')
  elif case=='existing-resolver':(negative/'etc/resolv.conf').write_text('nameserver 192.0.2.53\n')
  elif case=='existing-timezone-link':(negative/'etc/localtime').symlink_to('../usr/share/zoneinfo/UTC')
  elif case=='redirected-etc':
   outside=base/'outside-etc';(negative/'etc').rename(outside);(negative/'etc').symlink_to(outside)
  elif case=='runtime-data':
   path=negative/'run/systemd/resolve/stub-resolv.conf';path.parent.mkdir(parents=True);path.write_text('nameserver 192.0.2.53\n')
  elif case=='redirected-runtime':
   outside=base/'outside-run';outside.mkdir();(negative/'run').rmdir();(negative/'run').symlink_to(outside)
  elif case=='changed-timezone':(negative/'usr/share/zoneinfo/UTC').write_bytes(b'public changed timezone fixture')
  elif case=='interrupted-partial':(negative/'etc/.toddy-live-fstab.part').write_text('public interrupted fixture\n')
  elif case=='wrong-base-hash':expected_input='0'*64
  elif case=='unreviewed-links':selected_links['etc/resolv.conf']='../unreviewed-resolver'
  else:os.link(negative/'etc/fstab',negative/'other-fstab')
  fstab_before=live.digest(negative/'etc/fstab')
  link_before={name:state(negative/name) for name in links}
  try:live.stage_live_configuration(backend,negative,expected_input,selected_links)
  except ValueError as error:refused.append({'case':case,'reason':str(error)})
  else:raise AssertionError('Unreviewed live configuration accepted: '+case)
  assert live.digest(negative/'etc/fstab')==fstab_before
  assert {name:state(negative/name) for name in links}==link_before
 assert {name:state(root/name) for name in originals}==before
 print(json.dumps({'live_profile':report,'native_findmnt':findmnt,'native_timezone':timezone,
  'native_fstab_generator':generator,'generator_links':generated,'generator_environment':environment,
  'negative_cases':refused,'native_runtime':runtime_report,
  'source_sha256':{name:hashlib.sha256(base64.b64decode(content)).hexdigest() for name,content in SOURCES.items()},
  'base_configuration_candidate_packaged_or_installed':False,
  'installed_configuration_and_dpkg_unchanged':True,'fixture_removed_after_checks':True,
  'actual_boot_mounts_or_dns_verified':False},indent=2))
except BaseException:
 print('Preserved live configuration fixture: '+str(base),flush=True)
 raise
else:shutil.rmtree(base)
'''.replace('SOURCES', repr(sources))
result = subprocess.run(['python3', 'scripts/host/vm.py', 'ssh',
    'source /opt/toddy-build/scripts/build/target.sh; guard_target && python3 -'],
    input=script, text=True, capture_output=True)
path = Path('.local/logs/h10-live-configuration-probe.json')
data = (json.dumps({'exit': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr}, indent=2) + '\n').encode()
sha = hashlib.sha256(data).hexdigest()
path.with_name(path.stem + '.' + sha + '.json').write_bytes(data)
path.write_bytes(data)
print(result.stdout, result.stderr)
print('exit', result.returncode, 'SHA256', sha)
result.check_returncode()
