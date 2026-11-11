#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import hashlib,json,os,shutil,subprocess,sys
R=Path('/opt/toddy-build');T=Path('/mnt/lfs');sys.path.insert(0,str(R/'scripts/build/phase2'))
import desktop_defaults as defaults
assert shutil.disk_usage(T).free>=16*1024**3+2*1024**2
for name in [defaults.PROFILE,defaults.KEYFILE,defaults.DATABASE]:assert not os.path.lexists(T/name.lstrip('/')),'Preserve existing dconf policy'
for name in defaults.FAVORITES:assert (T/'usr/share/applications'/name).is_file(),name
stage=T/'sources/stage/phase2-toddy-desktop-defaults'
conffiles=defaults.stage(stage,R)
subprocess.run(['chroot',str(T),'dconf','compile','/sources/stage/phase2-toddy-desktop-defaults'+defaults.DATABASE,'/sources/stage/phase2-toddy-desktop-defaults/etc/dconf/db/toddy-desktop.d'],check=True)
(stage/defaults.DATABASE.lstrip('/')).chmod(0o644)
subprocess.run(['python3',str(R/'scripts/build/stage_package.py'),'toddy-desktop-defaults','0.2.0-1+toddy1',str(stage),'--architecture','all','--recipe','scripts/build/phase2/desktop-defaults-install.sh','--depends','dconf (>= 0.49.0-1+toddy1), gnome-shell (>= 50.4-1+toddy1), gnome-terminal (>= 3.60.0-1+toddy1), firefox (>= 153.7.0esr-1+toddy1)',*[v for name in conffiles for v in ['--conffile',name]],'--install'],cwd=R,check=True)
Path('/var/log/toddy/phase2/desktop-defaults-installed.json').write_text(json.dumps({'scope':'Owned provisional dconf desktop/Terminal defaults. Existing user database, artwork and schema cache unchanged; native behavior/visual verification separate.','database_sha256':hashlib.sha256((T/defaults.DATABASE.lstrip('/')).read_bytes()).hexdigest(),'conffiles':conffiles,'favorites':defaults.FAVORITES},indent=2)+'\n')
PY
