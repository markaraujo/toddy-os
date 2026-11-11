#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import hashlib,json,os,shutil,subprocess,sys,tempfile
sys.path.insert(0,'/opt/toddy-build/scripts/build/phase2')
from qualify_localsearch import qualify,digest,REPORT_SHA
T=Path('/mnt/lfs');prefix=['chroot',str(T)]
proof=qualify(Path('/opt/toddy-build'))
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','localsearch'],text=True)=='install ok installed 3.11.1-1+toddy1'
assert not subprocess.check_output(prefix+['dpkg','--audit'],text=True).strip()
subprocess.run(prefix+['apt-get','check'],check=True)
for name,sha in proof['stage_sha256'].items():assert digest(T/name)==sha
stage=Path('/mnt/lfs/sources/phase2/work/localsearch-1/stage')
for p in stage.rglob('*'):
 if p.is_symlink():assert os.readlink(T/p.relative_to(stage))==os.readlink(p)
files=[p for p in stage.rglob('*') if p.is_file() and not p.is_symlink()]
assert not any(p.stat().st_mode&0o6000 for p in files)
elfs=[p for p in files if p.open('rb').read(4)==b'\x7fELF'];assert len(elfs)==21
for p in elfs:
 relative='/'+str(p.relative_to(stage))
 linked=subprocess.check_output(prefix+['ldd',relative],text=True)
 assert 'not found' not in linked,relative
 assert '/sources/' not in linked and '/build/' not in linked and '/src/' not in linked
for p in (stage/'usr/share/dbus-1/services').glob('*.service'):
 text=p.read_text();assert 'User=root' not in text and 'SystemdService=' in text
for p in (stage/'usr/lib/systemd/user').glob('*.service'):
 assert '[Service]' in p.read_text() and 'User=root' not in p.read_text()
with tempfile.TemporaryDirectory(prefix='toddy-localsearch-installed-',dir=T/'var/tmp') as directory:
 home=Path(directory);os.chown(home,101,101)
 virtual='/var/tmp/'+home.name
 env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':virtual,'XDG_CONFIG_HOME':virtual+'/config','XDG_CACHE_HOME':virtual+'/cache'}
 command=['setpriv','--no-new-privs','chroot','--userspec=101:101','--groups=101',str(T),'/usr/bin/localsearch']
 rows=[]
 for arguments,expected in [(['--version'],0),(['toddy-no-such-command'],1),(['--help'],0),(['--version'],0)]:
  r=subprocess.run(command+arguments,env=env,capture_output=True,text=True,timeout=20)
  assert r.returncode==expected,(arguments,r.returncode,r.stderr)
  if arguments==['--version']:assert r.stdout.startswith('LocalSearch 3.11.1\n')
  rows.append({'arguments':arguments,'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr})
assert shutil.disk_usage(T).free>=16*1024**3
result={'scope':'Owned LocalSearch3.11.1 exact installed stage,21ELF ABI/APT, installed UID101/NNP CLI version/invalid-command refusal/help/recovery. Reuses real native9program/20case search/denial proof for identical staged binaries. Shared system schema cache integration, installed user service/search and Nautilus/GUI remain pending. No service enabled or started.','native_functional_report_sha256':REPORT_SHA,'installed_identical_regular_files':133,'installed_ELF_count':21,'no_setuid_sgid':True,'user_activation_definitions_only':True,'installed_cli_runs':rows}
Path('/var/log/toddy/phase2/localsearch-installed-consumer.json').write_text(json.dumps(result,indent=2)+'\n')
PY
