#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import json,subprocess
prefix=['chroot','/mnt/lfs'];env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':'/tmp','PYTHONDONTWRITEBYTECODE':'1'}
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version} ${Architecture}','gweather-locations'],text=True)=='install ok installed 2026.2-1+toddy1 amd64'
assert subprocess.check_output(prefix+['pkg-config','--modversion','gweather-locations'],text=True).strip()=='2026.2'
assert subprocess.check_output(prefix+['pkg-config','--variable=locations_db','gweather-locations'],text=True).strip()=='/usr/lib/gweather-locations/Locations.bin'
assert not subprocess.check_output(prefix+['dpkg','--audit'],text=True).strip();subprocess.run(prefix+['apt-get','check'],check=True)
expected=json.loads(Path('/mnt/lfs/sources/phase2/work/gweather-locations-1/stage-results.json').read_text())['consumer']
probe=Path('/opt/toddy-build/scripts/build/phase2/gweather-locations-probe.py').read_text()
actual=json.loads(subprocess.check_output(prefix+['python3','-c',probe,'/'],env=env,text=True,timeout=30));assert actual==expected
Path('/var/log/toddy/phase2/gweather-locations-installed-consumer.json').write_text(json.dumps({'scope':'Owned native-endian static location database/normal-form/schema/index/BR/PT/airport/timezone invariants and SDK/APT only. No actual owner position, permission, forecasts, full GWeather or GNOME GUI acceptance.','consumer':actual,'architecture':'amd64','not_architecture_all':True,'source_and_generated_data_unchanged':True},indent=2)+'\n')
PY
