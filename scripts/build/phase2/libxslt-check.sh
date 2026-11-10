#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import json,os,shutil,subprocess,tempfile,sys
T=Path('/mnt/lfs');prefix=['chroot',str(T)];env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':'/tmp','PYTHONDONTWRITEBYTECODE':'1'}
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','libxslt'],text=True)=='install ok installed 1.1.45-1+toddy1'
assert subprocess.check_output(prefix+['pkg-config','--modversion','libxslt'],text=True).strip()=='1.1.45'
assert not subprocess.check_output(prefix+['dpkg','--audit'],text=True).strip();subprocess.run(prefix+['apt-get','check'],check=True)
r=json.loads((T/'sources/phase2/work/libxslt-1/stage-results.json').read_text())
with tempfile.TemporaryDirectory(prefix='toddy-libxslt-',dir=T/'tmp') as directory:
 p=Path(directory);os.chown(p,101,101);p.chmod(0o755);shutil.copyfile('/opt/toddy-build/scripts/build/phase2/libxslt-probe.py',p/'probe.py');virtual='/tmp/'+p.name
 actual=json.loads(subprocess.check_output(['unshare','--net','chroot','--userspec=101:101',str(T),'python3',virtual+'/probe.py','/',virtual+'/consumer'],env=env,text=True,timeout=70));assert actual==r['consumer']
 libs=subprocess.check_output(prefix+['ldd','/usr/bin/xsltproc'],env=env,text=True);assert 'libxslt.so.1 => /usr/lib/libxslt.so.1' in libs and 'not found' not in libs
sys.path.insert(0,'/opt/toddy-build/scripts/build/phase2');from qualify_libxslt import review
reviewed=review(T/'sources/phase2/work/libxslt-1/original-tests.log',T/'sources/phase2/inputs/libxslt-1.1.45')
Path('/var/log/toddy/phase2/libxslt-installed-consumer.json').write_text(json.dumps({'scope':'Actual installed UID101/no-route xsltproc build SDK bounded UTF8 transform/malformed refusal/EXSLT write refusal-no-effect/two recovery cycles/pkg-config/APT0. Original core driver reports748noerrors; four swallowed DocBook golden differences remain unaccepted, no full suite or general CLI default sandbox claim. Not Terminal runtime dependency.','consumer':actual,'shared_library_resolution':True,'original_review':reviewed,'image_role':'build-only SDK, exclude from default Terminal runtime closure'},indent=2)+'\n')
PY
