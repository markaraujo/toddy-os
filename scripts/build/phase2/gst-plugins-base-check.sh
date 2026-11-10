#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import json,os,shutil,subprocess,tempfile
T=Path('/mnt/lfs');prefix=['chroot',str(T)];env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':'/tmp','PYTHONDONTWRITEBYTECODE':'1'}
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','gst-plugins-base'],text=True)=='install ok installed 1.28.6-1+toddy1'
for m in ['gstreamer-audio-1.0','gstreamer-video-1.0','gstreamer-app-1.0','gstreamer-gl-1.0']:
 assert subprocess.check_output(prefix+['pkg-config','--modversion',m],text=True).strip()=='1.28.6'
assert not subprocess.check_output(prefix+['dpkg','--audit'],text=True).strip();subprocess.run(prefix+['apt-get','check'],check=True)
expected=json.loads((T/'sources/phase2/work/gst-plugins-base-1/stage-results.json').read_text())['consumer']
with tempfile.TemporaryDirectory(prefix='toddy-gst-base-',dir=T/'tmp') as directory:
 p=Path(directory);os.chown(p,101,101);p.chmod(0o755)
 shutil.copyfile('/opt/toddy-build/scripts/build/phase2/gst-plugins-base-probe.py',p/'probe.py')
 virtual='/tmp/'+p.name;env.update(HOME=virtual,GST_REGISTRY_1_0=virtual+'/registry.bin')
 actual=json.loads(subprocess.check_output(['unshare','--net','chroot','--userspec=101:101',str(T),'python3',virtual+'/probe.py'],env=env,text=True,timeout=30));assert actual==expected
Path('/var/log/toddy/phase2/gst-plugins-base-installed-consumer.json').write_text(json.dumps({'scope':'Actual installed UID101 GstApp/Audio/Video GI/typed raw caps and exact synthetic red RGB/silent stereo samples, two video+audio EOS→NULL cycles in private no-route namespace; no devices/real playback/GL/screencast acceptance. Original37validate skips/17GL-context deferrals remain unqualified. Four SDK versions/APT0.','consumer':actual,'SDKs':['audio','video','app','gl'],'SDK_version':'1.28.6','private_registry_removed':True,'actual_GL_or_devices_tested':False},indent=2)+'\n')
PY
