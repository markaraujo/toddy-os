#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'CHECK'
from pathlib import Path
import hashlib,json,shlex,stat,subprocess,tempfile
root=Path('/opt/toddy-build/scripts/build/phase2');prefix=['chroot','/mnt/lfs'];env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':'/root'}
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','linux-pam'],text=True,env=env)=='install ok installed 1.7.2-1+toddy2'
assert subprocess.check_output(prefix+['pkg-config','--modversion','pam'],text=True,env=env).strip()=='1.7.2'
assert not subprocess.check_output(prefix+['dpkg','--audit'],text=True,env=env).strip()
subprocess.run(prefix+['apt-get','check'],env=env,check=True)
helper=Path('/mnt/lfs/usr/sbin/unix_chkpwd');st=helper.stat()
assert (st.st_uid,st.st_gid,stat.S_IMODE(st.st_mode))==(0,0,0o4755)
assert hashlib.sha256(helper.read_bytes()).hexdigest()=='2176a32b57f8c0ec676503cec517534695e96689f5d29c16e81ff264de600e29'
assert Path('/mnt/lfs/etc/pam.d/other').read_text()==''.join(f'{kind} required pam_deny.so\n' for kind in ['auth','account','password','session'])
with tempfile.TemporaryDirectory(prefix='toddy-pam-',dir='/mnt/lfs/tmp') as directory:
 p=Path(directory);native='/tmp/'+p.name;(p/'consumer.c').write_bytes((root/'pam-probe.c').read_bytes())
 flags=shlex.split(subprocess.check_output(prefix+['pkg-config','--cflags','--libs','pam'],text=True,env=env))
 subprocess.run(prefix+['cc','-Wall','-Wextra','-Werror',native+'/consumer.c',*flags,'-o',native+'/consumer'],check=True,env=env)
 result=subprocess.run(prefix+[native+'/consumer',native+'/policy','/usr/lib/security'],text=True,capture_output=True,env=env,check=True)
proof={'scope':'Installed owned PAM public API/module allow-deny/refusal/recovery and exact reviewed helper ownership; real native shadow/password7cases reused, no Shadow/systemd/GDM/login acceptance','version':'1.7.2','consumer_exit':0,'stdout':result.stdout.strip(),'helper_mode':'4755','helper_uid':0,'helper_gid':0,'fallback_policy':'deny all four PAM management groups','unqualified':'Shadow PAM rebuild, pam_systemd/logind/session, recoverable authenticated boot and GNOME integration pending'}
Path('/var/log/toddy/phase2/pam-installed-consumer.json').write_text(json.dumps(proof,indent=2)+'\n')
CHECK
