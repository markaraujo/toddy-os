#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
chroot_run <<'INNER'
set -euo pipefail
audit=$(dpkg --audit)
[[ -z $audit ]]
apt-get check
python3 - <<'PY'
from pathlib import Path
import subprocess,json
rows=subprocess.check_output(['dpkg-query','-W','-f=${Package}\t${Status}\t${Version}\n'],text=True).splitlines()
for row in rows:
 name,status,version=row.split('\t')
 if status!='install ok installed':raise SystemExit('Unconfigured package: '+name)
 if not version.endswith('+toddy1'):raise SystemExit('Old metadata generation: '+name)
for path in Path('/sources/evidence/h07-metadata-closure/packages').glob('*.json'):
 assert json.loads(path.read_text())['complete'],path
print('All native package metadata upgrades configured and recorded')
PY
INNER
python3 /opt/toddy-build/scripts/build/audit_native_elf.py > /var/log/toddy/h07-final-elf.json
python3 - <<'PYREPORT'
import json,subprocess
from pathlib import Path
p=Path('/var/log/toddy/h07-final-elf.json');report=json.loads(p.read_text())
expected={'package':'systemd','file':'/usr/lib/systemd/libsystemd-core-261.so','needed':'libsystemd-shared-261.so','problem':'provider absent from reviewed native search paths'}
assert report['findings']==[expected],report['findings']
result=subprocess.run(['chroot','/mnt/lfs','/lib64/ld-linux-x86-64.so.2','--list','/usr/lib/systemd/systemd'],capture_output=True,text=True,check=True)
assert 'libsystemd-core-261.so => /usr/lib/systemd/libsystemd-core-261.so' in result.stdout
assert 'libsystemd-shared-261.so => /usr/lib/systemd/libsystemd-shared-261.so' in result.stdout
report['qualified_private_library_context']={'decision':'ADR-0036','loader_exit':result.returncode,'loader_output':result.stdout,'standalone_library_loadability_claimed':False}
report['unqualified_findings']=[]
p.write_text(json.dumps(report,indent=2)+'\n')
print('Direct ELF dependency metadata accepted; exact Systemd private execution context verified')
PYREPORT
python3 /opt/toddy-build/scripts/build/audit_native_payload.py > /var/log/toddy/h07-final-payload.json
python3 - <<'PYPAYLOAD'
import json
from pathlib import Path
report=json.loads(Path('/var/log/toddy/h07-final-payload.json').read_text())
assert not report['findings'],report['findings']
assert not report['duplicate_owners'],report['duplicate_owners']
assert Path('/mnt/lfs/usr/share/info/dir').stat().st_size>0
for file in Path('/mnt/lfs/var/lib/dpkg/info').glob('*.list'):
 assert '/usr/share/info/dir' not in file.read_text().splitlines(),file
print('Native SHA-256/link/mode/ownership audit passed; modified conffiles reported separately')
PYPAYLOAD
python3 /opt/toddy-build/scripts/build/audit_script_interpreters.py > /var/log/toddy/h07-final-script-interpreters.json
python3 - <<'PYSCRIPTS'
import json
from pathlib import Path
report=json.loads(Path('/var/log/toddy/h07-final-script-interpreters.json').read_text())
assert not report['findings'],report['findings']
print('Native executable shebang and env-provider metadata passed')
PYSCRIPTS
python3 /opt/toddy-build/scripts/build/audit_unowned_files.py > /var/log/toddy/h07-final-unowned.json
python3 - <<'PYOWNED'
import json
from pathlib import Path
report=json.loads(Path('/var/log/toddy/h07-final-unowned.json').read_text())
assert not report['unknown'],report['unknown']
print('Final-base package ownership has no unexplained files; generated and H08 configuration remain explicit')
PYOWNED
python3 /opt/toddy-build/scripts/build/audit_native_build_flow.py > /var/log/toddy/h07-final-native-build-flow.json
