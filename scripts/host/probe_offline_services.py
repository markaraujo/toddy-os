#!/usr/bin/env python3
"""Check real native Systemd offline policy on copied source-owned units."""
from pathlib import Path
import base64
import hashlib
import json
import os
import runpy
import subprocess
import sys

os.chdir(Path(__file__).resolve().parents[2])
sys.path.insert(0, 'scripts/build/h10')
from image_attribution import SERVICE_LINKS, UNIT_PREFIX
declared_links = {'/etc/systemd/system/' + name: UNIT_PREFIX + target if target else '/dev/null'
                  for name, target in SERVICE_LINKS.items()}
source = base64.b64encode(Path('scripts/build/h08/offline_services.py').read_bytes()).decode()
auditor_code = base64.b64encode(Path('scripts/build/audit_unowned_files.py').read_bytes()).decode()
policy = runpy.run_path('scripts/build/h08/stage_config.py')['FILES']['usr/lib/systemd/system-preset/50-toddy-base.preset']
script = r'''from pathlib import Path
import base64,hashlib,json,os,shutil,subprocess,sys,tempfile,types
sys.path.insert(0,'/opt/toddy-build/scripts/build')
from package_backend import PackageBackend
root=Path('/mnt/lfs');backend=PackageBackend(root)
base=Path(tempfile.mkdtemp(prefix='toddy-offline-services-',dir=root/'tmp'))
print('OFFLINE_SERVICES_FIXTURE '+str(base),flush=True)
module=types.ModuleType('offline_services');module.__file__='/opt/toddy-build/scripts/build/h08/offline_services.py'
exec(compile(base64.b64decode(SOURCE),module.__file__,'exec'),module.__dict__)
def configuration_snapshot(directory):
 return {str(path.relative_to(directory)):(path.readlink().as_posix() if path.is_symlink() else module.digest(path))
         for path in directory.rglob('*') if path.is_symlink() or path.is_file()}
before=configuration_snapshot(root/'etc/systemd/system');status_before=module.digest(root/'var/lib/dpkg/status')
try:
 image=base/'image';image.mkdir();(image/'etc/systemd/system').mkdir(parents=True)
 for name in ('systemd','dbus'):
  identity=backend.run('dpkg-query','-W','-f=${Package}_${Version}_${Architecture}',name,capture_output=True,text=True).stdout
  record=json.loads((Path('/var/log/toddy/packages')/(identity+'.json')).read_text())
  for virtual,row in sorted(record['payload'].items()):
   if not (virtual.startswith('/usr/lib/systemd/system/') or virtual=='/usr/lib/systemd/system-preset/90-systemd.preset'):continue
   original=root/virtual[1:];destination=image/virtual[1:]
   destination.parent.mkdir(parents=True,exist_ok=True)
   if row.get('directory'):
    destination.mkdir(exist_ok=True);destination.chmod(row['mode']&0o7777)
   else:
    if 'sha256' in row:assert module.digest(original)==row['sha256']
    else:assert original.readlink().as_posix()==row['symlink']
    shutil.copy2(original,destination,follow_symlinks=False)
   os.chown(destination,row['uid'],row['gid'],follow_symlinks=False)
 (image/'usr/lib/systemd/system-preset/50-toddy-base.preset').write_text(PRESET_POLICY)
 old=backend.run('systemctl','--root=/'+str(image.relative_to(root)),'is-enabled','dbus.socket',capture_output=True,text=True)
 assert old.stdout.strip()=='static' and old.stdout.strip()!='enabled'
 report=module.configure_services(backend,image,Path('/var/log/toddy/packages'))
 assert {name:row['symlink'] for name,row in report['generated_links'].items()}==DECLARED_LINKS
 after=configuration_snapshot(image/'etc/systemd/system')
 repeat=module.configure_services(backend,image,Path('/var/log/toddy/packages'))
 checked=module.configure_services(backend,image,Path('/var/log/toddy/packages'),check_only=True)
 assert report['states']==repeat['states']==checked['states']
 assert configuration_snapshot(image/'etc/systemd/system')==after
 assert report['generated_links']==repeat['generated_links']==checked['generated_links']
 assert not (image/'etc/systemd/system/sockets.target.wants/dbus.socket').is_symlink()
 preset=backend.run('systemctl','--root=/'+str(image.relative_to(root)),'--no-reload','preset-all',capture_output=True,text=True)
 (base/'native-preset-all.log').write_text(preset.stdout+preset.stderr)
 preset_checked=module.configure_services(backend,image,Path('/var/log/toddy/packages'),check_only=True)
 assert preset_checked['states']==report['states']
 auditor=types.ModuleType('audit_unowned_files');auditor.__file__='/opt/toddy-build/scripts/build/audit_unowned_files.py'
 exec(compile(base64.b64decode(AUDITOR_CODE),auditor.__file__,'exec'),auditor.__dict__)
 audit_root=base/'mask-audit';audit_root.mkdir()
 unit='/usr/lib/systemd/system/'+module.WAIT_ONLINE;mask='/etc/systemd/system/'+module.WAIT_ONLINE
 owned=audit_root/unit[1:];owned.parent.mkdir(parents=True);shutil.copy2(image/unit[1:],owned)
 link=audit_root/mask[1:];link.parent.mkdir(parents=True);link.symlink_to('/dev/null')
 owners={unit:{'systemd'}}
 assert auditor.generated_configuration_link(audit_root,mask,link,owners)['owned_unit']==unit
 assert auditor.generated_configuration_link(audit_root,mask,link,{}) is None
 other=link.parent/'unreviewed.service';other.symlink_to('/dev/null')
 assert auditor.generated_configuration_link(audit_root,'/etc/systemd/system/unreviewed.service',other,owners) is None
 link.unlink();link.symlink_to('/not-a-null-mask')
 assert auditor.generated_configuration_link(audit_root,mask,link,owners) is None
 link.unlink();link.symlink_to('/dev/null');os.chown(link,101,101,follow_symlinks=False)
 assert auditor.generated_configuration_link(audit_root,mask,link,owners) is None
 os.chown(link,0,0,follow_symlinks=False);owned.unlink();owned.symlink_to(image/unit[1:])
 assert auditor.generated_configuration_link(audit_root,mask,link,owners) is None
 refused=[]
 for case in ('missing-vendor-link','changed-vendor-link','changed-native-unit','unowned-generated-link','disabled-required-service','redirected-config-directory'):
  negative=base/case;shutil.copytree(image,negative,symlinks=True)
  path=negative/module.VENDOR_DBUS[1:]
  if case=='missing-vendor-link':path.unlink()
  elif case=='changed-vendor-link':path.unlink();path.symlink_to('../unknown.socket')
  elif case=='changed-native-unit':
   path=negative/'usr/lib/systemd/system/dbus.socket';path.write_text(path.read_text()+'\n# unexpected input\n')
  elif case=='unowned-generated-link':
   path=negative/'etc/systemd/system/unknown.service';path.symlink_to('/usr/lib/systemd/system/unknown.service')
   (negative/'etc/systemd/system/multi-user.target.wants/systemd-networkd.service').unlink()
  elif case=='disabled-required-service':
   backend.run('systemctl','--root=/'+str(negative.relative_to(root)),'--no-reload','disable','systemd-resolved.service',capture_output=True,text=True)
  else:
   path=negative/'etc/systemd/system';path.rename(negative/'preserved');path.symlink_to(negative/'preserved')
  saved=configuration_snapshot(negative)
  try:module.configure_services(backend,negative,Path('/var/log/toddy/packages'),check_only=case!='unowned-generated-link')
  except (ValueError,FileNotFoundError,subprocess.CalledProcessError) as error:
   refused.append({'case':case,'reason':str(error)})
  else:raise AssertionError('Unreviewed offline service state accepted: '+case)
  assert configuration_snapshot(negative)==saved
 assert configuration_snapshot(root/'etc/systemd/system')==before
 assert module.digest(root/'var/lib/dpkg/status')==status_before
 print(json.dumps({'original_expected_enabled_would_fail':{'native_state':old.stdout.strip(),'expected_by_old_check':'enabled'},
  'configured':report,'declared_image_links_match_native_enablement':True,
  'repeat_configure_same_links':True,'check_only_same_links':True,
  'native_preset_all':{'exit':preset.returncode,'stdout':preset.stdout,'stderr':preset.stderr},
  'preset_policy_sha256':hashlib.sha256(PRESET_POLICY.encode()).hexdigest(),
  'native_vendor_preset_sha256':module.digest(image/'usr/lib/systemd/system-preset/90-systemd.preset'),
  'after_preset_all':preset_checked,
  'mask_audit':{'exact_owned_mask_accepted':True,'negative_boundaries':5,
   'auditor_sha256':hashlib.sha256(base64.b64decode(AUDITOR_CODE)).hexdigest()},
  'negative_cases':refused,'installed_configuration_and_database_unchanged':True,
  'source_sha256':hashlib.sha256(base64.b64decode(SOURCE)).hexdigest(),
  'fixture_removed_after_checks':True,'native_services_started':False,'boot_dhcp_dns_verified':False},indent=2))
except BaseException:
 print('Preserved offline services fixture: '+str(base),flush=True)
 raise
else:shutil.rmtree(base)
'''.replace('SOURCE', repr(source)).replace('PRESET_POLICY', repr(policy)).replace('AUDITOR_CODE', repr(auditor_code)).replace('DECLARED_LINKS', repr(declared_links))
result = subprocess.run(['python3', 'scripts/host/vm.py', 'ssh',
    'source /opt/toddy-build/scripts/build/target.sh; guard_target && python3 -'],
    input=script, text=True, capture_output=True)
path = Path('.local/logs/h08-offline-services-probe.json')
data = (json.dumps({'exit': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr}, indent=2) + '\n').encode()
sha = hashlib.sha256(data).hexdigest()
path.with_name(path.stem + '.' + sha + '.json').write_bytes(data)
path.write_bytes(data)
print(result.stdout, result.stderr)
print('exit', result.returncode, 'SHA256', sha)
result.check_returncode()
