#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import hashlib,json,shutil,subprocess,tempfile
prefix=['chroot','/mnt/lfs'];env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':'/tmp','PYTHONDONTWRITEBYTECODE':'1'}
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','geocode-glib'],text=True)=='install ok installed 3.26.4-1+toddy1'
assert subprocess.check_output(prefix+['pkg-config','--modversion','geocode-glib-2.0'],text=True).strip()=='3.26.4'
assert not subprocess.check_output(prefix+['dpkg','--audit'],text=True).strip();subprocess.run(prefix+['apt-get','check'],check=True)
w=Path('/mnt/lfs/sources/phase2/work/geocode-glib-1');expected=json.loads((w/'stage-results.json').read_text())['consumer'];assert not Path('/mnt/lfs/stage').exists()
with tempfile.TemporaryDirectory(prefix='toddy-geocode-',dir='/mnt/lfs/tmp') as directory:
 p=Path(directory);shutil.copyfile(w/'native-probe',p/'probe');(p/'probe').chmod(0o755)
 assert hashlib.sha256((p/'probe').read_bytes()).digest()==hashlib.sha256((w/'native-probe').read_bytes()).digest()
 native='/tmp/'+p.name+'/probe';libs=subprocess.check_output(prefix+['ldd',native],text=True,env=env);assert 'libgeocode-glib-2.so.0 => /usr/lib/libgeocode-glib-2.so.0' in libs
 consumer=json.loads(subprocess.check_output(prefix+[native],env=env,text=True,timeout=20));assert consumer==expected
code="""import gi,json
gi.require_version('GeocodeGlib','2.0')
from gi.repository import GeocodeGlib
p=GeocodeGlib.Location.new(-15.793889,-47.882778,1000)
p.set_description('Brasília · Toddy')
assert p.get_description()=='Brasília · Toddy' and abs(p.get_latitude()+15.793889)<1e-6 and abs(p.get_longitude()+47.882778)<1e-6
print(json.dumps({'namespace':'GeocodeGlib2.0','UTF8_and_coordinates':True}))
"""
gi=json.loads(subprocess.check_output(prefix+['python3','-c',code],env=env,text=True,timeout=20))
Path('/var/log/toddy/phase2/geocode-glib-installed-consumer.json').write_text(json.dumps({'scope':'Owned libsoup3 ABI/geo-URI/UTF8/refusal/two-cycle recovery and installed GIR/SDK only. Original JSON mocks remain fixtures; foreign-locale/remote geocoding/owner location permissions and GNOME/GWeather not accepted.','consumer':consumer,'GI':gi,'loaded_owned_library':True},indent=2)+'\n')
PY
