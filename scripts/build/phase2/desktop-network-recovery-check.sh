#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'INNER'
from pathlib import Path
import hashlib,json,os,subprocess
T=Path('/mnt/lfs');L=Path('/var/log/toddy/phase2')
r=json.loads(Path('/var/log/toddy/packages/toddy-desktop-network_0.2.0-1+toddy2_all.json').read_text());assert r['installed']
for n,row in r['payload'].items():
 p=T/n.lstrip('/');st=p.lstat();assert (st.st_mode,st.st_uid,st.st_gid)==(row['mode'],row['uid'],row['gid']),n
 if 'sha256' in row:
  with p.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==row['sha256'],n
 elif 'symlink' in row:assert os.readlink(p)==row['symlink'],n
assert subprocess.check_output(['chroot',str(T),'dpkg-query','-W','-f=${Version}','toddy-desktop-network'],text=True)=='0.2.0-1+toddy2'
assert not subprocess.check_output(['chroot',str(T),'dpkg','--audit'],text=True).strip()
subprocess.run(['chroot',str(T),'apt-get','check'],check=True)
proof=json.loads((L/'desktop-network-recovery-update-1.json').read_text());assert proof['state']=='complete'
assert (T/'etc/toddy/network/use-networkmanager').read_text()=='NetworkManager\n'
assert (T/'etc/resolv.conf').readlink()==Path('/run/systemd/resolve/stub-resolv.conf')
(L/'desktop-network-recovery-update-check-1.json').write_text(json.dumps({'scope':'README-only native package ownership/integrity/dependency verification; runtime proof retained separately','verified_entries':len(r['payload']),'archive_sha256':r['archive_sha256'],'unchanged_configuration':True},indent=2)+'\n')
INNER
