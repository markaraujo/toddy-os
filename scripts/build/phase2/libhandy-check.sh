#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import json,os,shutil,subprocess,tempfile
T=Path('/mnt/lfs');prefix=['chroot',str(T)];env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':'/tmp','PYTHONDONTWRITEBYTECODE':'1'}
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','libhandy'],text=True)=='install ok installed 1.8.3-1+toddy1'
assert subprocess.check_output(prefix+['pkg-config','--modversion','libhandy-1'],text=True).strip()=='1.8.3'
assert not subprocess.check_output(prefix+['dpkg','--audit'],text=True).strip();subprocess.run(prefix+['apt-get','check'],check=True)
w=T/'sources/phase2/work/libhandy-1';r=json.loads((w/'stage-results.json').read_text())
source=w/'probe-2/native-probe'
if not source.exists():source=w/'native-probe'
assert not (T/'stage').exists()
with tempfile.TemporaryDirectory(prefix='toddy-libhandy-',dir=T/'tmp') as directory:
 p=Path(directory);os.chown(p,101,101);p.chmod(0o755);shutil.copyfile(source,p/'native-probe');(p/'native-probe').chmod(0o755)
 shutil.copyfile('/opt/toddy-build/scripts/build/phase2/libhandy-gi-probe.py',p/'GI.py');virtual='/tmp/'+p.name
 command=['unshare','--net','chroot','--userspec=101:101',str(T)]
 actual=json.loads(subprocess.check_output(command+[virtual+'/native-probe'],env=env,text=True,timeout=20));assert actual==r['consumer']
 gi=json.loads(subprocess.check_output(command+['python3',virtual+'/GI.py'],env=env,text=True,timeout=15));assert gi==r['GI_consumer']
 libs=subprocess.check_output(prefix+['ldd',virtual+'/native-probe'],env=env,text=True);assert 'libhandy-1.so.0 => /usr/lib/libhandy-1.so.0' in libs and 'not found' not in libs
Path('/var/log/toddy/phase2/libhandy-installed-consumer.json').write_text(json.dumps({'scope':'Actual installed UID101/no-route shared libhandy/GI typed Unicode value-copy/take-dup ownership/enum/two reset cycles/pkg-config/APT0. No widget/display/Terminal acceptance. All30original graphical programs compiled/deferred and mandatory runtime scope remains before B02 closure.','consumer':actual,'GI_consumer':gi,'shared_library_resolution':True,'original_graphical_tests_pending':r['original_graphical_tests_pending']},indent=2)+'\n')
PY
