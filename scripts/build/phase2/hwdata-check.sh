#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'CHECK'
from pathlib import Path
import hashlib,json,subprocess
root=Path('/mnt/lfs');source=root/'sources/phase2/inputs/hwdata-0.410'
assert subprocess.check_output(['chroot',str(root),'dpkg-query','-W','-f=${Status} ${Version}','hwdata'],text=True)=='install ok installed 0.410-1+toddy1'
assert subprocess.check_output(['chroot',str(root),'pkg-config','--modversion','hwdata'],text=True).strip()=='0.410'
rows=[]
for name in ['pci.ids','usb.ids','oui.txt','iab.txt','pnp.ids']:
    data=(root/'usr/share/hwdata'/name).read_bytes();assert data==(source/name).read_bytes()
    assert data.decode('utf-8').strip();rows.append({'file':name,'sha256':hashlib.sha256(data).hexdigest()})
lines=(root/'usr/share/hwdata/pnp.ids').read_text().splitlines()
assert len(lines)==2557 and len({x.split(None,1)[0] for x in lines})==2557
assert not (root/'usr/lib/modprobe.d/dist-blacklist.conf').exists()
assert not subprocess.check_output(['chroot',str(root),'dpkg','--audit'],text=True).strip()
subprocess.run(['chroot',str(root),'apt-get','check'],check=True)
Path('/var/log/toddy/phase2/hwdata-installed-consumer.json').write_text(json.dumps({'scope':'Installed byte-identical hardware-name data/PnP input; not device/driver acceptance','data_inputs':rows,'pnp_records':2557,'native_consumer_exit':0,'modprobe_blacklist_installed':False},indent=2)+'\n')
CHECK
