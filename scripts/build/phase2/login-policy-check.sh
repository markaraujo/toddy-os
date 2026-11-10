#!/bin/bash
set -euo pipefail
python3 - <<'PY'
from pathlib import Path
import hashlib,json,subprocess,sys
sys.path.insert(0,'/opt/toddy-build/scripts/build/phase2')
from schema_union_install import verify
T=Path('/mnt/lfs');r=json.loads(Path('/var/log/toddy/phase2/login-policy-install-1.json').read_text());assert r['state']=='complete' and r['existing_PAM_and_modules_unchanged']
p=json.loads(Path('/var/log/toddy/packages/toddy-login-policy_0.1.0-1+toddy1_all.json').read_text());verify(p);assert p['installed'] and p['archive_sha256']==r['archive_sha256']
for n,sha in r['input_sha256'].items():assert hashlib.sha256((T/'etc/pam.d'/n).read_bytes()).hexdigest()==sha
prefix=['chroot',str(T)];assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','toddy-login-policy'],text=True)=='install ok installed 0.1.0-1+toddy1'
assert set(subprocess.check_output(prefix+['dpkg-query','-W','-f=${Conffiles}','toddy-login-policy'],text=True).split()[::2])=={'/etc/pam.d/'+n for n in r['input_sha256']}
assert not subprocess.check_output(prefix+['dpkg','--audit'],text=True).strip();subprocess.run(prefix+['apt-get','check'],check=True)
PY
