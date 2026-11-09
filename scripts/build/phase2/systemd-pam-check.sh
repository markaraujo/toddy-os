#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'CHECK'
from pathlib import Path
import json,subprocess,sys
sys.path.insert(0,'/opt/toddy-build/scripts/build/phase2')
from install_systemd_pam import verify_installed
prefix=['chroot','/mnt/lfs'];env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':'/root'}
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','systemd'],text=True,env=env)=='install ok installed 261.2-1+toddy3'
record=json.loads(Path('/var/log/toddy/packages/systemd_261.2-1+toddy3_amd64.json').read_text());assert record['installed'];verify_installed(record)
assert not subprocess.check_output(prefix+['dpkg','--audit'],text=True,env=env).strip()
subprocess.run(prefix+['apt-get','check'],env=env,check=True)
versions=[]
for program in ['/usr/lib/systemd/systemd','/usr/lib/systemd/systemd-executor','/usr/bin/systemctl','/usr/bin/loginctl','/usr/bin/busctl']:
 r=subprocess.run(prefix+[program,'--version'],text=True,capture_output=True,env=env,check=True)
 assert '261.2' in r.stdout.splitlines()[0]
 versions.append({'program':program,'exit':r.returncode,'version_line':r.stdout.splitlines()[0],'features_line':r.stdout.splitlines()[1] if len(r.stdout.splitlines())>1 else None})
assert '+PAM' in versions[0]['features_line'] and '+PAM' in versions[1]['features_line']
subprocess.run(prefix+['python3','-c',"import ctypes;p=ctypes.CDLL('/usr/lib/security/pam_systemd.so');assert p.pam_sm_open_session and p.pam_sm_close_session"],env=env,check=True)
policy=Path('/mnt/lfs/etc/pam.d/systemd-user').read_text()
assert 'account  required   pam_unix.so no_pass_expiry' in policy and 'session  optional   pam_systemd.so' in policy
proof={'scope':'Owned same-version four runtime replacements and PAM files; complete payload/CLI/module/APT checks only, native cold boot/session gate still pending','version':'261.2-1+toddy3','installed_payload_entries':len(record['payload']),'versions':versions,'module_load_exit':0,'unqualified':'Native new PID1 cold boot, PAMName allow/deny, logind/user-session and recovery not yet verified'}
Path('/var/log/toddy/phase2/systemd-pam-installed-consumer.json').write_text(json.dumps(proof,indent=2)+'\n')
CHECK
