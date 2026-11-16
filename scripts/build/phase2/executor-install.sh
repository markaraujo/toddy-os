#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import hashlib,json,shutil,subprocess,sys
repository=Path('/opt/toddy-build');target=Path('/mnt/lfs')
sys.path.insert(0,str(repository/'scripts/build/phase2'))
from executor_package import stage,VERSION,DEPENDENCIES
assert shutil.disk_usage(target).free>=16*1024**3+4*1024**2
prefix=['chroot',str(target)]
for name in ['python','pygobject','glib','dbus','polkit','systemd','apt','dpkg','networkmanager']:
 assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status}',name],text=True)=='install ok installed'
assert subprocess.run(prefix+['dpkg-query','-W','toddy-executor'],capture_output=True).returncode!=0,'Preserve existing executor; this recipe is first install only'
assert not (target/'var/lib/toddy/executor').exists(),'Preserve any existing policy state; image first-install requires clean state'
destination=target/'sources/stage/phase2-toddy-executor-1'
manifest=stage(destination,repository)
for path in destination.rglob('*'):
 if path.is_dir() and not path.is_symlink():continue
 actual=target/path.relative_to(destination)
 assert not actual.exists() and not actual.is_symlink(),'Refuse unreviewed executor payload conflict'
subprocess.run(['python3',str(repository/'scripts/build/stage_package.py'),'toddy-executor',VERSION,str(destination),
 '--architecture','all','--recipe','scripts/build/phase2/executor-install.sh','--depends',DEPENDENCIES,'--install'],cwd=repository,check=True)
Path('/var/log/toddy/phase2/executor-package-source.json').write_text(json.dumps({'scope':'First native package install only; no daemon/owner/broker runtime acceptance','version':VERSION,'source_manifest':manifest,
 'generator_sha256':hashlib.sha256((repository/'scripts/build/phase2/executor_package.py').read_bytes()).hexdigest(),
 'next':'Run executor-check.sh; native runtime qualification independently required'},indent=2)+'\n')
PY
