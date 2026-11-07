#!/usr/bin/env python3
"""Compare OverlayFS ACL copy-up in a private builder mount namespace.

This uses the builder kernel and an ext4 lower fixture, not a Toddy live image.
The off profile is a negative control; only on preserves hardlink semantics.
An optional verified private native tool build adds a real Squashfs lower image.
"""
from pathlib import Path
import argparse
import base64
import hashlib
import json
import os
import subprocess

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('index', choices=('off', 'on'))
parser.add_argument('--squashfs-probe', type=Path, help='Completed private native Squashfs experiment directory')
parser.add_argument('--copy-up-acls', action='store_true', help='Force unchanged-mode copy-up before restoring ACLs')
options = parser.parse_args()
profile = options.index
fixture = options.squashfs_probe
if fixture and (fixture.parent != Path('/mnt/lfs/sources/recovery') or not fixture.name.startswith('squashfs-native-')):
    parser.error('Require the exact completed private Squashfs experiment directory')
os.chdir(Path(__file__).resolve().parents[2])
script=r'''import base64,hashlib,json,os,pathlib,shutil,stat,subprocess,tempfile
from pathlib import Path
base=Path(tempfile.mkdtemp(prefix='toddy-overlay-acl-',dir='/tmp'))
base.chmod(0o755)
mounted=[]
def command(*args,**kw):
 result=subprocess.run(args,text=True,capture_output=True,**kw)
 if result.returncode:
  print(json.dumps({'failed_command':args,'exit':result.returncode,'stdout':result.stdout,'stderr':result.stderr}),flush=True)
  result.check_returncode()
 return result
def reader(path):
 code='import os,sys;os.setgroups([]);os.setgid(101);os.setuid(101);open(sys.argv[1]).read()'
 return subprocess.run(['/usr/bin/python3','-c',code,str(path)],text=True,capture_output=True).returncode
def identity(path):
 def drop():
  os.setgroups([]);os.setgid(101);os.setuid(101)
 return command(str(path),preexec_fn=drop).stdout.strip()
try:
 squashfs_evidence=None
 if SQUASHFS_PROBE:
  probe=Path(SQUASHFS_PROBE)
  assert probe.resolve()==probe and probe.parent==Path('/sources/recovery') and probe.stat().st_uid==0
  result=json.loads((probe/'result.json').read_text())
  assert result['complete'] and json.loads((probe/'driver.exit.json').read_text())['exit']==0
  assert result['source_sha256']=='547b7b7f4d2e44bf91b6fc554664850c69563701deab9fd9cd7e21f694c88ea6'
  tools=probe/'squashfs-tools-4.7.5/squashfs-tools'
  for name,sha in result['binaries'].items():assert hashlib.sha256((tools/name).read_bytes()).hexdigest()==sha
  squashfs_evidence={'tools':result['binaries'],'source_sha256':result['source_sha256']}
 lower=base/'lower';ram=base/'ram';merged=base/'merged'
 for p in (lower,ram,merged):p.mkdir(mode=0o755)
 code=base/'identity.c'
 code.write_text('#include <stdio.h>\n#include <unistd.h>\nint main(void){printf("%lu %lu\\n",(unsigned long)getuid(),(unsigned long)geteuid());return 0;}\n')
 privileged=lower/'privilege-check'
 command('cc','-O2','-Wall','-Werror',str(code),'-o',str(privileged))
 os.chown(privileged,0,0);privileged.chmod(0o4755)
 original_privileged=hashlib.sha256(privileged.read_bytes()).hexdigest()
 name='acl-ação\nfile\\part';f=lower/name;f.write_text('overlay ACL fixture\n');os.chown(f,18,18);f.chmod(0o4750)
 os.link(f,lower/'linked')
 command('setfacl','-m','u:101:r--',str(f))
 acldir=lower/'acl-directory';acldir.mkdir(mode=0o750);os.chown(acldir,18,18)
 command('setfacl','-m','u:101:r-x,d:u:101:r-x',str(acldir))
 capability=lower/'capability-check';shutil.copy2(privileged,capability);capability.chmod(0o755)
 command('setcap','cap_net_bind_service=ep',str(capability))
 command('setfacl','-m','u:101:r-x',str(capability))
 capability_xattr=os.getxattr(capability,'security.capability')
 acl_names=(name,'linked','acl-directory','capability-check')
 acl=command('getfacl','-n','-P','--skip-base','--',*acl_names,cwd=lower).stdout
 expected_mode=stat.S_IMODE(f.stat().st_mode)
 command('setfacl','-b',str(f))
 command('setfacl','-b','-k',str(acldir))
 command('setfacl','-b',str(capability))
 original={'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'mode':stat.S_IMODE(f.stat().st_mode),'inode':f.stat().st_ino,'acl':command('getfacl','-n','-c',str(f)).stdout}
 if SQUASHFS_PROBE:
  compressed=base/'lower.squashfs'
  created=command(str(tools/'mksquashfs'),str(lower),str(compressed),'-noappend','-comp','xz','-processors','2','-mem','128M','-no-progress','-xattrs','-exports')
  header=command(str(tools/'unsquashfs'),'-s',str(compressed)).stdout
  squashfs_evidence.update(image_sha256=hashlib.sha256(compressed.read_bytes()).hexdigest(),header=header,creation=created.stdout)
  mounted_lower=base/'squashfs';mounted_lower.mkdir()
  command('mount','-t','squashfs','-o','loop,ro',str(compressed),str(mounted_lower));mounted.append(mounted_lower)
  lower=mounted_lower;f=lower/name;privileged=lower/'privilege-check'
  assert command('findmnt','-rn','-M',str(lower),'-o','FSTYPE').stdout.strip()=='squashfs'
  assert 'ro' in command('findmnt','-rn','-M',str(lower),'-o','OPTIONS').stdout.strip().split(',')
  assert hashlib.sha256(f.read_bytes()).hexdigest()==original['sha256']
  original['inode']=f.stat().st_ino
 else:
  command('mount','--bind',str(lower),str(lower));mounted.append(lower)
  command('mount','-o','remount,bind,ro',str(lower))
 command('mount','-t','tmpfs','-o','size=64m,mode=0755,nosuid,nodev','tmpfs',str(ram));mounted.append(ram)
 for d in ('upper','work'):(ram/d).mkdir(mode=0o755)
 command('mount','-t','overlay','overlay','-o',f'lowerdir={lower},upperdir={ram}/upper,workdir={ram}/work,index=PROFILE',str(merged));mounted.append(merged)
 mount_options=command('findmnt','-rn','-M',str(merged),'-o','OPTIONS').stdout.strip()
 if 'PROFILE'=='on':assert 'index=on' in mount_options.split(','),mount_options
 lower_identity=identity(merged/'privilege-check');assert lower_identity=='101 0',lower_identity
 os.chown(merged/'privilege-check',0,0)
 (merged/'privilege-check').chmod(0o4755)
 upper_identity=identity(merged/'privilege-check');assert upper_identity=='101 0',upper_identity
 direct_upper_identity=identity(ram/'upper/privilege-check')
 assert direct_upper_identity=='101 101',direct_upper_identity
 assert hashlib.sha256(privileged.read_bytes()).hexdigest()==original_privileged
 assert stat.S_IMODE(privileged.stat().st_mode)==0o4755
 before=reader(merged/name);assert before!=0
 if COPY_UP_ACLS:
  helper=base/'restore_live_acls.sh';helper.write_bytes(base64.b64decode(RESTORE_HELPER))
  sidecar=base/'live-root.acl';sidecar.write_text(acl)
  command('bash','--noprofile','--norc',str(helper),str(sidecar),cwd=merged)
 else:command('setfacl','-P','--restore=-',input=acl,cwd=merged)
 actual=command('getfacl','-n','-P','--skip-base','--',*acl_names,cwd=merged).stdout
 assert actual==acl,(acl,actual)
 assert os.getxattr(merged/'capability-check','security.capability')==capability_xattr
 assert os.getxattr(lower/'capability-check','security.capability')==capability_xattr
 restore_refusals=[]
 if COPY_UP_ACLS:
  sentinel=base/'outside';sentinel.write_text('Outside fixture must remain unchanged\n');sentinel.chmod(0o600)
  (merged/'redirected').symlink_to(sentinel)
  (merged/'redirected-parent').symlink_to(base)
  for label,header in [('absolute path',str(sentinel)),('parent traversal','../outside'),
                       ('redirected file','redirected'),('redirected parent','redirected-parent/outside'),
                       ('unknown escape',r'bad\040escape'),('missing entry','absent-probe')]:
   sidecar.write_text('# file: '+header+'\n')
   refused=subprocess.run(['bash','--noprofile','--norc',str(helper),str(sidecar)],cwd=merged,text=True,capture_output=True)
   assert refused.returncode!=0,(label,refused.stdout,refused.stderr)
   restore_refusals.append({'case':label,'exit':refused.returncode,'stderr':refused.stderr})
  sidecar.write_text(acl+acl)
  refused=subprocess.run(['bash','--noprofile','--norc',str(helper),str(sidecar)],cwd=merged,text=True,capture_output=True)
  assert refused.returncode!=0 and 'Duplicate ACL path' in refused.stderr
  restore_refusals.append({'case':'duplicate entries','exit':refused.returncode})
  sidecar.write_text('');command('bash','--noprofile','--norc',str(helper),str(sidecar),cwd=merged)
  assert sentinel.read_text()=='Outside fixture must remain unchanged\n' and stat.S_IMODE(sentinel.stat().st_mode)==0o600
  (merged/'redirected').unlink();(merged/'redirected-parent').unlink()
  sidecar.write_text(acl)
  command('bash','--noprofile','--norc',str(helper),str(sidecar),cwd=merged)
  assert command('getfacl','-n','-P','--skip-base','--',*acl_names,cwd=merged).stdout==acl
  assert os.getxattr(merged/'capability-check','security.capability')==capability_xattr
 assert reader(merged/name)==0
 assert stat.S_IMODE((merged/name).stat().st_mode)==expected_mode
 assert (merged/name).stat().st_uid==18 and (merged/name).stat().st_gid==18
 assert f.stat().st_ino==original['inode'] and hashlib.sha256(f.read_bytes()).hexdigest()==original['sha256']
 assert command('getfacl','-n','-c',str(f)).stdout==original['acl']
 assert (ram/'upper'/name).exists()
 child=merged/'acl-directory/inherited';child.write_text('Inherited ACL fixture\n');os.chown(child,18,18)
 assert reader(child)==0
 assert not (lower/'acl-directory/inherited').exists()
 hardlinks=(merged/name).stat().st_ino==(merged/'linked').stat().st_ino
 (merged/name).write_text('changed upper payload\n')
 propagated=(merged/'linked').read_text()=='changed upper payload\n'
 assert hardlinks==('PROFILE'=='on'),hardlinks
 assert propagated==('PROFILE'=='on'),propagated
 assert hashlib.sha256(f.read_bytes()).hexdigest()==original['sha256']
 (merged/'volatile').write_text('not persistent\n')
 assert not (lower/'volatile').exists()
 command('umount',str(merged));mounted.remove(merged)
 command('umount',str(ram));mounted.remove(ram)
 command('mount','-t','tmpfs','-o','size=64m,mode=0755,nosuid,nodev','tmpfs',str(ram));mounted.append(ram)
 assert not (ram/'upper').exists()
 print(json.dumps({'kernel':os.uname().release,'mount_namespace':os.readlink('/proc/self/ns/mnt'),'readonly_lower_unchanged':True,'native_acl_restore_and_uid101_read':True,'default_acl_inheritance_verified':True,'security_capability_xattr_preserved':True,'copy_up_before_acl_restore':COPY_UP_ACLS,'restore_refusals':restore_refusals,'restore_helper_sha256':hashlib.sha256(base64.b64decode(RESTORE_HELPER)).hexdigest() if COPY_UP_ACLS else None,'special_mode_uid_gid_preserved':True,'index':'PROFILE','mount_options':mount_options,'hardlink_identity_after_restore':hardlinks,'hardlink_write_propagates':propagated,'volatile_upper_discarded':True,'identity_before_copyup':lower_identity,'identity_after_copyup':upper_identity,'identity_via_nosuid_upper':direct_upper_identity,'squashfs_tested':bool(SQUASHFS_PROBE),'squashfs_evidence':squashfs_evidence,'toddy_native_kernel_boot':False,'fixture':str(base)},indent=2))
except BaseException:
 print('Failed private fixture retained:',base)
 raise
finally:
 for p in reversed(mounted):command('umount',str(p))
# No mount remains beneath this explicitly created fixture.
shutil.rmtree(base)
'''
helper=base64.b64encode(Path('scripts/build/h10/restore_live_acls.sh').read_bytes()).decode()
script='SQUASHFS_PROBE='+repr('/'+str(fixture.relative_to('/mnt/lfs')) if fixture else None)+'\nCOPY_UP_ACLS='+repr(options.copy_up_acls)+'\nRESTORE_HELPER='+repr(helper)+'\n'+script.replace('PROFILE',profile)
r=subprocess.run(['python3','scripts/host/vm.py','ssh','source /opt/toddy-build/scripts/build/target.sh; guard_target && unshare --mount --propagation private chroot /mnt/lfs /usr/bin/env -i PATH=/usr/bin:/usr/sbin LC_ALL=C /usr/bin/python3 -'],input=script,text=True,capture_output=True)
p=Path('.local/logs/h10-overlay-acl-index-'+profile+('-squashfs' if fixture else '')+'-probe.json')
p.parent.mkdir(parents=True,exist_ok=True)
raw=(json.dumps({'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr},indent=2)+'\n').encode()
# Preserve cited generations before replacing the convenient current report.
for content in ([p.read_bytes()] if p.exists() else [])+[raw]:
 generation=p.with_name(p.stem+'.'+hashlib.sha256(content).hexdigest()+p.suffix)
 if generation.exists():
  if generation.read_bytes()!=content:raise RuntimeError('Preserve changed evidence generation')
 else:generation.write_bytes(content)
p.write_bytes(raw)
print(r.stdout,r.stderr);print('exit',r.returncode,'SHA256',hashlib.sha256(p.read_bytes()).hexdigest());r.check_returncode()
