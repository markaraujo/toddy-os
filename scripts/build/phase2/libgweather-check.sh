#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import hashlib,json,shutil,subprocess,tempfile
prefix=['chroot','/mnt/lfs'];env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':'/tmp','PYTHONDONTWRITEBYTECODE':'1'}
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','libgweather'],text=True)=='install ok installed 4.6.0-1+toddy1'
assert subprocess.check_output(prefix+['pkg-config','--modversion','gweather4'],text=True).strip()=='4.6.0'
assert not subprocess.check_output(prefix+['dpkg','--audit'],text=True).strip();subprocess.run(prefix+['apt-get','check'],check=True)
w=Path('/mnt/lfs/sources/phase2/work/libgweather-1');expected=json.loads((w/'stage-results.json').read_text())['consumer'];assert not Path('/mnt/lfs/stage').exists()
with tempfile.TemporaryDirectory(prefix='toddy-gweather-',dir='/mnt/lfs/tmp') as directory:
 p=Path(directory);shutil.copyfile(w/'native-probe',p/'probe');(p/'probe').chmod(0o755)
 assert hashlib.sha256((p/'probe').read_bytes()).digest()==hashlib.sha256((w/'native-probe').read_bytes()).digest()
 native='/tmp/'+p.name+'/probe';libs=subprocess.check_output(prefix+['ldd',native],text=True,env=env);assert 'libgweather-4.so.0 => /usr/lib/libgweather-4.so.0' in libs
 consumer=json.loads(subprocess.check_output(prefix+[native],env=env,text=True,timeout=20));assert consumer==expected
code="""import gi,json
gi.require_version('GWeather','4.0')
from gi.repository import GWeather
w=GWeather.Location.get_world();assert w
l=GWeather.Location.find_by_station_code(w,'SBGR');assert l and l.get_code()=='SBGR'
assert GWeather.Location.find_by_country_code(w,'BR')
print(json.dumps({'namespace':'GWeather4.0','owned_station_and_country_lookup':True}))
"""
gi=json.loads(subprocess.check_output(prefix+['python3','-c',code],env=env,text=True,timeout=20))
common=Path('/opt/toddy-build/LICENSES/third-party/LGPL-2.1.txt').read_bytes()
assert Path('/mnt/lfs/usr/share/doc/libgweather/LGPL-2.1.txt').read_bytes()==common
copyright=Path('/mnt/lfs/usr/share/doc/libgweather/copyright').read_bytes();assert b'John Tsiombikas' in copyright and common in copyright
Path('/var/log/toddy/phase2/libgweather-installed-consumer.json').write_text(json.dumps({'scope':'Owned offline location DB/C/GI4.0/variant/refusal/two-cycle recovery and SDK/APT only; original three core programs12cases reused. Actual external METAR original remains failed/unqualified, no forecasts/owner location/GNOME or stock Info/schema acceptance.','consumer':consumer,'GI':gi,'loaded_owned_library_and_database':True,'GPL_LGPL_BSD_notices_retained':True},indent=2)+'\n')
PY
