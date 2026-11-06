#!/bin/bash
# Private native metadata-channel experiment, not Squashfs/live boot acceptance.
source /opt/toddy-build/scripts/build/h06/common.sh
chroot_run <<'INNER'
set -euo pipefail
PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
from pathlib import Path
import hashlib,json,os,shutil,stat,subprocess,tempfile
with tempfile.TemporaryDirectory(prefix='toddy-acl-sidecar-') as directory:
 root=Path(directory);root.chmod(0o755)
 source=root/'input';output=root/'output';source.mkdir(mode=0o755);output.mkdir(mode=0o755)
 name='payload with spaces\nsecond line';original=source/name;copied=output/name
 original.write_bytes(b'Native metadata preservation fixture\n')
 os.chown(original,18,18)
 subprocess.run(['setfacl','-m','u:101:r--',str(original)],check=True)
 original.chmod(0o4750)
 dump=subprocess.check_output(['getfacl','-R','-P','-p','-n','--skip-base','.'],cwd=source,text=True)
 assert dump.count('# file: ')==1
 for line in dump.splitlines():
  if line.startswith('# file: '):
   path=line[len('# file: '):];assert not path.startswith('/') and '..' not in Path(path).parts
 sidecar=root/'metadata.acl';sidecar.write_text(dump)
 shutil.copyfile(original,copied);copied.chmod(0o4750)
 assert 'system.posix_acl_access' not in os.listxattr(copied)
 assert subprocess.run(['test','-r',str(copied)],user=101,group=101,extra_groups=[]).returncode==1
 subprocess.run(['setfacl','-P','--restore='+str(sidecar)],cwd=output,check=True)
 restored=subprocess.check_output(['getfacl','-R','-P','-p','-n','--skip-base','.'],cwd=output,text=True)
 assert restored==dump
 assert (copied.stat().st_uid,copied.stat().st_gid,stat.S_IMODE(copied.stat().st_mode))==(18,18,0o4750)
 assert copied.read_bytes()==original.read_bytes()
 subprocess.run(['test','-r',str(copied)],user=101,group=101,extra_groups=[],check=True)
 assert subprocess.run(['test','-x',str(copied)],user=101,group=101,extra_groups=[]).returncode==1
 print(json.dumps({'acl_sidecar_roundtrip':True,'numeric_ownership':[18,18],'mode':'4750','relative_escaped_names':True,'named_user_effective_access_verified':True,'content_unchanged':True,'sidecar_sha256':hashlib.sha256(dump.encode()).hexdigest(),'installed_changes':False,'squashfs_roundtrip':False,'kernel_boot_validated':False}))
PY
INNER
