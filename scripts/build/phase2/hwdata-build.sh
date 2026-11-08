#!/bin/bash
# Source-verified hardware name data; no device access or modprobe policy.
set -euo pipefail
[[ $(id -u) == 101 && -f /src/pnp.ids && -d /stage ]]
cp -a /src /build/source
cd /build/source
./configure --prefix=/usr --disable-blacklist
make
python3 check-pci-ids.py > /build/upstream-pci-sort.log 2>&1
# Upstream USB test invokes privileged podman/device access: explicitly skipped.
NO_DOCKER=1 bash check-usb-ids.sh > /build/upstream-usb-skip.log 2>&1
make DESTDIR=/stage install
python3 - <<'PY'
from pathlib import Path
import hashlib,json,subprocess
names=['pci.ids','usb.ids','oui.txt','iab.txt','pnp.ids'];rows=[]
for name in names:
    src=Path('/src')/name;out=Path('/stage/usr/share/hwdata')/name
    assert src.read_bytes()==out.read_bytes()
    text=out.read_text(encoding='utf-8');assert text.strip()
    rows.append({'file':name,'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'bytes':out.stat().st_size,'utf8_exit':0})
lines=[x for x in Path('/stage/usr/share/hwdata/pnp.ids').read_text().splitlines() if x and not x.startswith('#')]
ids=[x.split(None,1)[0] for x in lines]
assert len(ids)==2557 and len(set(ids))==len(ids) and all(len(x)==3 and x.isascii() for x in ids)
assert not Path('/stage/usr/lib/modprobe.d').exists()
assert subprocess.check_output(['pkg-config','--modversion','/stage/usr/share/pkgconfig/hwdata.pc'],text=True).strip()=='0.410'
Path('/build/test-results.json').write_text(json.dumps({'scope':'Native staged hardware-name databases/PnP lookup input only; not device/driver/hardware acceptance',
'data_inputs':rows,'upstream_pci_order_exit':0,'pnp_records':len(ids),'pnp_duplicate_ids':0,
'upstream_lspci_dump':'Unavailable lspci utility; not counted as pass',
'upstream_usb_device_test':'Explicit NO_DOCKER=1 skip: privileged external podman/device test outside compiler scope',
'staged_consumer_exit':0,'modprobe_blacklist_installed':False},indent=2)+'\n')
PY
