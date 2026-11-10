#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import json,os,subprocess,sys
T=Path('/mnt/lfs');prefix=['chroot',str(T)];env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8'}
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','tecla'],text=True)=='install ok installed 50.0-1+toddy1'
assert not subprocess.check_output(prefix+['dpkg','--audit'],text=True).strip();subprocess.run(prefix+['apt-get','check'],check=True)
sys.path.insert(0,'/opt/toddy-build/scripts/build/phase2');from qualify_tecla import qualify,digest
proof=qualify(Path('/opt/toddy-build'))
for relative,sha in proof['stage_sha256'].items():assert digest(T/relative)==sha
assert subprocess.check_output(prefix+['pkg-config','--modversion','tecla'],env=env,text=True).strip()=='50.0'
assert subprocess.check_output(prefix+['pkg-config','--variable=app','tecla'],env=env,text=True).strip()=='/usr/bin/tecla'
libs=subprocess.check_output(prefix+['ldd','/usr/bin/tecla'],env=env,text=True)
assert 'not found' not in libs
for name in ['libgtk-4.so.1','libadwaita-1.so.0','libxkbcommon.so.0']:assert name+' => /usr/lib/'+name in libs
s=os.statvfs(T);assert s.f_bavail*s.f_frsize>=16*1024**3
Path('/var/log/toddy/phase2/tecla-installed-consumer.json').write_text(json.dumps({'scope':'Owned pinned Tecla50.0 installed payload/pkg-config application path/shared ABI/APT. Reuses actual native7.1.8/Systemd/Mutter staged CLI evidence for the identical installed executable. CLI requires display, no headless replay. No keyboard preview GUI/input/focus/complete GNOME/hardware acceptance.','installed_stage_files_identical':len(proof['stage_sha256']),'native_cli_report_sha256':digest(Path('/var/log/toddy/phase2/native-tecla-cli-report-1.json')),'shared_library_resolution':True,'graphical_preview_tested':False},indent=2)+'\n')
PY
