#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import errno,json,os,shutil,subprocess,sys
sys.path.insert(0,'/opt/toddy-build/scripts/build/phase2')
from qualify_nautilus import qualify,digest,REPORT_SHA
T=Path('/mnt/lfs');prefix=['chroot',str(T)]
proof=qualify(Path('/opt/toddy-build'))
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','nautilus'],text=True)=='install ok installed 50.2.2-1+toddy1'
assert not subprocess.check_output(prefix+['dpkg','--audit'],text=True).strip()
subprocess.run(prefix+['apt-get','check'],check=True)
for name,sha in proof['stage_sha256'].items():assert digest(T/name)==sha
stage=T/'sources/phase2/work/nautilus-1/stage'
for p in stage.rglob('*'):
 if p.is_symlink():assert os.readlink(T/p.relative_to(stage))==os.readlink(p)
files=[p for p in stage.rglob('*') if p.is_file() and not p.is_symlink()]
assert not any(p.stat().st_mode&0o6000 for p in files)
elfs=[p for p in files if p.open('rb').read(4)==b'\x7fELF'];assert len(elfs)==5
for p in elfs:
 relative='/'+str(p.relative_to(stage))
 linked=subprocess.check_output(prefix+['ldd',relative],text=True)
 assert 'not found' not in linked,relative
 assert not any(path in linked for path in ['/sources/','/build/','/src/'])
services=list((stage/'usr/share/dbus-1/services').glob('*.service'));assert len(services)==2
for p in services:
 text=p.read_text();assert 'User=' not in text and 'Exec=/usr/bin/nautilus --gapplication-service' in text
assert not (stage/'usr/lib/systemd/system').exists()
# Frozen nautilus-main.c explicitly rejects root before application construction.
refusal=subprocess.run(prefix+['/usr/bin/nautilus','--version'],capture_output=True,text=True,timeout=15)
assert refusal.returncode==errno.ENOTSUP and 'Running as root is not supported' in refusal.stderr
assert shutil.disk_usage(T).free>=16*1024**3
result={'scope':'Owned Nautilus50.2.2 exact installed stage,5ELF ABI/APT,source notices,user D-Bus activation and upstream root refusal only. Reuses focused native12program/73GLib-case evidence for the identical stage. Installed GUI/nonroot CLI,shared schema cache,icons/MIME integration remain pending. No service started or enabled.',
 'native_functional_report_sha256':REPORT_SHA,'installed_identical_regular_files':154,'installed_ELF_count':5,'no_setuid_sgid':True,'user_activation_definitions_only':True,
 'root_refusal':{'exit':refusal.returncode,'stderr':refusal.stderr}}
Path('/var/log/toddy/phase2/nautilus-installed-consumer.json').write_text(json.dumps(result,indent=2)+'\n')
PY
