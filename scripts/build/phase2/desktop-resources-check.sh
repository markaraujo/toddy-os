#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import hashlib,json,subprocess
root=Path('/opt/toddy-build');prefix=['chroot','/mnt/lfs'];env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':'/root','PYTHONDONTWRITEBYTECODE':'1'}
for name,version in [('hicolor-icon-theme','0.18-1+toddy1'),('adwaita-icon-theme','50.0-1+toddy1'),('gsettings-desktop-schemas','50.1-1+toddy1'),('gtk','4.22.4-1+toddy2')]:
    assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}',name],env=env,text=True)=='install ok installed '+version
assert not subprocess.check_output(prefix+['dpkg','--audit'],env=env,text=True).strip()
subprocess.run(prefix+['apt-get','check'],env=env,check=True)
for theme in ['hicolor','Adwaita']:
    subprocess.run(prefix+['gtk4-update-icon-cache','--validate','/usr/share/icons/'+theme],env=env,check=True)
body=(root/'scripts/build/phase2/desktop_resources_probe.py').read_text()
r=subprocess.run(prefix+['python3','-B','-c',body,'/','/usr/share/glib-2.0/schemas','/usr/share/icons'],env=env,text=True,capture_output=True,check=True)
receipt=json.loads(Path('/var/log/toddy/phase2/desktop-resources-transaction.json').read_text());assert receipt['state']=='complete'
cache=Path('/mnt/lfs/usr/share/glib-2.0/schemas/gschemas.compiled')
assert hashlib.sha256(cache.read_bytes()).hexdigest()==receipt['new_schema_cache_sha256']
Path('/var/log/toddy/phase2/desktop-resources-installed-consumer.json').write_text(json.dumps({'scope':'Actual installed native themes/schema/default fonts/GI/icons/SVG/cursor data; no native window/session interaction acceptance',
    'native_consumer_exit':0,'consumer':json.loads(r.stdout),'transaction':receipt},indent=2)+'\n')
PY
