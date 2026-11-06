#!/usr/bin/env python3
"""Compare OverlayFS ACL copy-up in a private builder mount namespace.

This uses the builder kernel and an ext4 lower fixture, not a Toddy live image.
The off profile is a negative control; only on preserves hardlink semantics.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import subprocess

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('index', choices=('off', 'on'))
profile = parser.parse_args().index
os.chdir(Path(__file__).resolve().parents[2])
script=r'''import hashlib,json,os,pathlib,shutil,stat,subprocess,tempfile
from pathlib import Path
base=Path(tempfile.mkdtemp(prefix='toddy-overlay-acl-',dir='/tmp'))
base.chmod(0o755)
mounted=[]
def command(*args,**kw):return subprocess.run(args,check=True,text=True,capture_output=True,**kw)
def reader(path):
 code='import os,sys;os.setgroups([]);os.setgid(101);os.setuid(101);open(sys.argv[1]).read()'
 return subprocess.run(['/usr/bin/python3','-c',code,str(path)],text=True,capture_output=True).returncode
def identity(path):
 def drop():
  os.setgroups([]);os.setgid(101);os.setuid(101)
 return command(str(path),preexec_fn=drop).stdout.strip()
try:
 lower=base/'lower';ram=base/'ram';merged=base/'merged'
 for p in (lower,ram,merged):p.mkdir(mode=0o755)
 code=base/'identity.c'
 code.write_text('#include <stdio.h>\n#include <unistd.h>\nint main(void){printf("%lu %lu\\n",(unsigned long)getuid(),(unsigned long)geteuid());return 0;}\n')
 privileged=lower/'privilege-check'
 command('cc','-O2','-Wall','-Werror',str(code),'-o',str(privileged))
 os.chown(privileged,0,0);privileged.chmod(0o4755)
 original_privileged=hashlib.sha256(privileged.read_bytes()).hexdigest()
 name='acl-ação\nfile';f=lower/name;f.write_text('overlay ACL fixture\n');os.chown(f,18,18);f.chmod(0o4750)
 os.link(f,lower/'linked')
 command('setfacl','-m','u:101:r--',str(f))
 acl=command('getfacl','-n','-P','--skip-base','--',name,'linked',cwd=lower).stdout
 expected_mode=stat.S_IMODE(f.stat().st_mode)
 command('setfacl','-b',str(f))
 original={'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'mode':stat.S_IMODE(f.stat().st_mode),'inode':f.stat().st_ino,'acl':command('getfacl','-n','-c',str(f)).stdout}
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
 command('setfacl','-P','--restore=-',input=acl,cwd=merged)
 actual=command('getfacl','-n','-P','--skip-base','--',name,'linked',cwd=merged).stdout
 assert actual==acl,(acl,actual)
 assert reader(merged/name)==0
 assert stat.S_IMODE((merged/name).stat().st_mode)==expected_mode
 assert (merged/name).stat().st_uid==18 and (merged/name).stat().st_gid==18
 assert f.stat().st_ino==original['inode'] and hashlib.sha256(f.read_bytes()).hexdigest()==original['sha256']
 assert command('getfacl','-n','-c',str(f)).stdout==original['acl']
 assert (ram/'upper'/name).exists()
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
 print(json.dumps({'kernel':os.uname().release,'mount_namespace':os.readlink('/proc/self/ns/mnt'),'readonly_lower_unchanged':True,'native_acl_restore_and_uid101_read':True,'special_mode_uid_gid_preserved':True,'index':'PROFILE','mount_options':mount_options,'hardlink_identity_after_restore':hardlinks,'hardlink_write_propagates':propagated,'volatile_upper_discarded':True,'identity_before_copyup':lower_identity,'identity_after_copyup':upper_identity,'identity_via_nosuid_upper':direct_upper_identity,'squashfs_tested':False,'toddy_native_kernel_boot':False,'fixture':str(base)},indent=2))
except BaseException:
 print('Failed private fixture retained:',base)
 raise
finally:
 for p in reversed(mounted):command('umount',str(p))
# No mount remains beneath this explicitly created fixture.
shutil.rmtree(base)
'''
r=subprocess.run(['python3','scripts/host/vm.py','ssh','source /opt/toddy-build/scripts/build/target.sh; guard_target && unshare --mount --propagation private chroot /mnt/lfs /usr/bin/env -i PATH=/usr/bin:/usr/sbin LC_ALL=C /usr/bin/python3 -'],input=script.replace('PROFILE',profile),text=True,capture_output=True)
p=Path('.local/logs/h10-overlay-acl-index-'+profile+'-probe.json')
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
