#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import hashlib,json,os,subprocess
root=Path('/mnt/lfs');repository=Path('/opt/toddy-build');prefix=['chroot',str(root)]
proof=json.loads(Path('/var/log/toddy/phase2/executor-package-source.json').read_text())
assert proof['generator_sha256']==hashlib.sha256((repository/'scripts/build/phase2/executor_package.py').read_bytes()).hexdigest()
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','toddy-executor'],text=True)=='install ok installed '+proof['version']
assert not subprocess.check_output(prefix+['dpkg','--audit'],text=True).strip()
subprocess.run(prefix+['apt-get','check'],check=True)
stage=root/'sources/stage/phase2-toddy-executor-1';checked=[]
for path in stage.rglob('*'):
 relative=path.relative_to(stage)
 if relative.parts[0]=='DEBIAN' or (path.is_dir() and not path.is_symlink()):continue
 actual=root/relative
 if path.is_symlink():assert actual.is_symlink() and actual.readlink()==path.readlink()
 else:
  assert actual.is_file() and not actual.is_symlink() and actual.read_bytes()==path.read_bytes()
  expected=0o755 if str(relative)=='usr/lib/toddy/executor/owner_policy.py' else 0o644
  info=actual.stat();assert info.st_uid==info.st_gid==0 and info.st_mode&0o7777==expected
 owner=subprocess.check_output(prefix+['dpkg-query','-S','/'+str(relative)],text=True)
 assert owner.startswith('toddy-executor: ')
 checked.append('/'+str(relative))
assert not (root/'var/lib/toddy/executor').exists(),'No build-time policy/grant state may enter image'
subprocess.run(prefix+['python3','-I','-B','-c',"import sys;sys.path.insert(0,'/usr/lib/toddy/executor');import service,operations,store,session_identity;assert 'gi.repository.Gtk' not in sys.modules"],check=True)
Path('/var/log/toddy/phase2/executor-package-check.json').write_text(json.dumps({'scope':'Native package ownership/source/modes/dependency/import closure only; no running-daemon or owner acceptance','version':proof['version'],'checked':checked,'build_time_grant_state_absent':True,'gtk_import_absent':True},indent=2)+'\n')
PY
