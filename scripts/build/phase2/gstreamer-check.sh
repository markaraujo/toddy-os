#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import json,os,shutil,subprocess,tempfile
T=Path('/mnt/lfs');prefix=['chroot',str(T)];env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':'/tmp','PYTHONDONTWRITEBYTECODE':'1'}
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','gstreamer'],text=True)=='install ok installed 1.28.6-1+toddy1'
assert subprocess.check_output(prefix+['pkg-config','--modversion','gstreamer-1.0'],text=True).strip()=='1.28.6'
assert not subprocess.check_output(prefix+['dpkg','--audit'],text=True).strip();subprocess.run(prefix+['apt-get','check'],check=True)
assert not (T/'usr/libexec/gstreamer-1.0/gst-ptp-helper').exists()
expected=json.loads((T/'sources/phase2/work/gstreamer-1/stage-results.json').read_text())['consumer']
with tempfile.TemporaryDirectory(prefix='toddy-gst-',dir=T/'tmp') as directory:
 p=Path(directory);os.chown(p,101,101);p.chmod(0o755)
 shutil.copyfile('/opt/toddy-build/scripts/build/phase2/gstreamer-probe.py',p/'probe.py')
 virtual='/tmp/'+p.name
 env.update(HOME=virtual,GST_REGISTRY_1_0=virtual+'/registry.bin')
 actual=json.loads(subprocess.check_output(['unshare','--net','chroot','--userspec=101:101',str(T),'python3',virtual+'/probe.py'],env=env,text=True,timeout=25));assert actual==expected
Path('/var/log/toddy/phase2/gstreamer-installed-consumer.json').write_text(json.dumps({'scope':'Actual installed UID101 Gst GI/typed raw caps/buffer, missing-element refusal and two synthetic fakesrc/fakesink EOS→NULL cycles in private no-route namespace. SDK/APT0, optional privileged PTP helper absent; no codecs/devices/audio/video/GNOME screencast acceptance. Private user registry removed.','consumer':actual,'SDK':'1.28.6','private_registry_removed':True,'privileged_PTP_helper_absent':True},indent=2)+'\n')
PY
