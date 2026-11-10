#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import json,subprocess
T=Path('/mnt/lfs');prefix=['chroot',str(T)];env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':'/tmp','PYTHONDONTWRITEBYTECODE':'1'}
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','glycin-gtk4'],text=True)=='install ok installed 2.1.0-1+toddy1'
for name in ['glycin-2','glycin-gtk4-2']:assert subprocess.check_output(prefix+['pkg-config','--modversion',name],text=True).strip()=='2.1.0'
assert not subprocess.check_output(prefix+['dpkg','--audit'],text=True).strip();subprocess.run(prefix+['apt-get','check'],check=True)
from sys import path
path.insert(0,'/opt/toddy-build/scripts/build/phase2')
from qualify_glycin_gtk4 import qualify,digest
proof=qualify(Path('/opt/toddy-build'))
for name,sha in proof['stage_sha256'].items():assert digest(T/name)==sha
code="import gi,ctypes;gi.require_version('Gly','2');gi.require_version('GlyGtk4','2');from gi.repository import Gly,GlyGtk4;assert callable(GlyGtk4.frame_get_texture);lib=ctypes.CDLL('/usr/lib/libglycin-gtk4-2.so.0');assert lib.gly_gtk_frame_get_texture and lib.gly_frame_get_width"
subprocess.run(['chroot','--userspec=101:101',str(T),'python3','-c',code],env=env,check=True,timeout=15)
libs=subprocess.check_output(prefix+['ldd','/usr/lib/libglycin-gtk4-2.so.0'],env=env,text=True);assert 'not found' not in libs and 'libglycin-2.so.0 => /usr/lib/libglycin-2.so.0' in libs
Path('/var/log/toddy/phase2/glycin-gtk4-installed-consumer.json').write_text(json.dumps({'scope':'Installed owned companion all five runtime/SDK stage files byte-identical to actual native conversion proof, unchanged owned default-path core/loaders, installed UID101 GI/shared symbols/pkg-config/APT0. Real native sandboxed image/texture/pixel/refusal/recovery evidence reused for identical inputs; no decoder retry under Ubuntu builder kernel, no display/widget/GNOME acceptance.','qualified_stage_files_identical':5,'GI_shared_symbol_exit':0,'shared_library_resolution':True,'reused_native_report_sha256':proof['report_sha256'],'native_consumer':proof['consumer']},indent=2)+'\n')
PY
