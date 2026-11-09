#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import hashlib,json,subprocess,tempfile
prefix=['chroot','/mnt/lfs'];env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':'/root','PYTHONDONTWRITEBYTECODE':'1'}
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','polkit'],text=True,env=env)=='install ok installed 127-1+toddy1'
assert subprocess.check_output(prefix+['pkg-config','--modversion','polkit-gobject-1'],text=True,env=env).strip()=='127'
assert not subprocess.check_output(prefix+['dpkg','--audit'],text=True,env=env).strip()
subprocess.run(prefix+['apt-get','check'],env=env,check=True)
user=next(r.split(':') for r in Path('/mnt/lfs/etc/passwd').read_text().splitlines() if r.startswith('polkitd:'));assert user[2:4]==['27','27'] and user[5:]==['/etc/polkit-1','/bin/false']
shadow=next(r.split(':') for r in Path('/mnt/lfs/etc/shadow').read_text().splitlines() if r.startswith('polkitd:'));assert shadow[1].startswith('!');del shadow
rules=Path('/mnt/lfs/etc/polkit-1/rules.d');st=rules.stat();assert (st.st_uid,st.st_gid,st.st_mode&0o7777)==(0,27,0o750) and not list(rules.iterdir())
assert Path('/mnt/lfs/etc/pam.d/polkit-auth').read_text()=='auth required pam_unix.so\naccount required pam_unix.so\npassword required pam_deny.so\nsession required pam_unix.so\n'
assert not Path('/mnt/lfs/etc/systemd/system/sockets.target.wants/polkit-agent-helper.socket').exists()
acceptance=json.loads(Path('/var/log/toddy/phase2/polkit-standard-native-acceptance-1.json').read_text())
for name,sha in acceptance['summary']['helpers'].items():
 p=Path('/mnt/lfs')/name.lstrip('/');st=p.stat();assert hashlib.sha256(p.read_bytes()).hexdigest()==sha and (st.st_uid,st.st_gid,st.st_mode&0o7777)==(0,0,0o4755)
with tempfile.TemporaryDirectory(prefix='toddy-polkit-',dir='/mnt/lfs/tmp') as directory:
 p=Path(directory);native='/tmp/'+p.name;(p/'consumer.c').write_bytes(Path('/opt/toddy-build/scripts/build/phase2/polkit-strict-subject-probe.c').read_bytes());(p/'polkit').mkdir();(p/'polkit/polkitprivate.h').write_bytes(Path('/mnt/lfs/sources/phase2/inputs/polkit-127-full-1/src/polkit/polkitprivate.h').read_bytes())
 subprocess.run(prefix+['bash','-c','cc -Wall -Wextra -Werror -D_POLKIT_COMPILATION -I"$1" -I/usr/include/polkit-1/polkit "$1/consumer.c" $(pkg-config --cflags --libs polkit-gobject-1 gio-unix-2.0) -o "$1/consumer"','probe',native],check=True,env=env)
 r=subprocess.run(['unshare','--mount','--pid','--fork','--mount-proc=/mnt/lfs/proc','--',*prefix,native+'/consumer','--corrected'],env={**env,'G_DEBUG':'fatal-warnings'},capture_output=True,text=True,check=True);consumer=json.loads(r.stdout)
assert consumer['cases']==13 and consumer['invalid_subject_cases_refused']==consumer['error_pointer_null_controls']==9
for command in ['pkaction','pkcheck','pkexec','pkttyagent']:
 r=subprocess.run(prefix+[command,'--version'],env=env,capture_output=True,text=True,check=True);assert '127' in r.stdout
proof={'scope':'Actual installed native parser13cases/9NULL-error controls using frozen private header and installed public SDK, exact helper modes/hashes, locked service account, deny-preserving PAM profile and APT audit; native real privilege evidence reused, GNOME permission UI pending','consumer':consumer,'service_account':{'uid':27,'gid':27,'locked':True,'login_shell':'/bin/false'},'rules_directory_mode':'root:27 0750','helper_transport':'Qualified standard SUID fallback; optional socket not enabled/unqualified','native_qualification':acceptance['summary']}
Path('/var/log/toddy/phase2/polkit-installed-consumer.json').write_text(json.dumps(proof,indent=2)+'\n')
PY
