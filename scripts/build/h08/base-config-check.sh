#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
python3 /opt/toddy-build/scripts/build/h08/require_gate.py
python3 - <<'PY'
import sys
from pathlib import Path
sys.path.insert(0,'/opt/toddy-build/scripts/build/h08')
from stage_config import FILES,LINKS
root=Path('/mnt/lfs')
for relative,expected in FILES.items():
 path=root/relative
 assert path.is_file() and not path.is_symlink() and path.read_text()==expected,relative
for relative,expected in LINKS.items():assert (root/relative).readlink().as_posix()==expected,relative
print('Installed base configuration matches reviewed native package inputs')
PY
chroot_run <<'INNER'
set -euo pipefail
[[ $(dpkg-query -W -f='${Status} ${Version}' toddy-base-config) == 'install ok installed 0.1-1' ]]
[[ -z $(dpkg --audit) ]]
apt-get check
[[ $(LC_ALL=en_US.UTF-8 locale charmap) == UTF-8 ]]
[[ $(LC_ALL=pt_BR.UTF-8 locale charmap) == UTF-8 ]]
cmp /etc/localtime /usr/share/zoneinfo/Etc/UTC
[[ $(date +%z) == +0000 ]]
test -s /usr/share/consolefonts/Lat2-Terminus16.psfu.gz
test -s /usr/share/keymaps/i386/qwerty/us.map.gz
for shell in /usr/bin/sh /usr/bin/bash /usr/bin/csh /usr/bin/tcsh; do
 test -x "$shell"
 grep -Fx "$shell" /etc/shells
done
[[ $(passwd -S root | awk '{print $2}') == L ]]
for pair in messagebus:18 systemd-network:76 systemd-resolve:77 systemd-timesync:78; do
 name=${pair%:*};uid=${pair#*:}
 [[ $(id -u "$name") == "$uid" ]]
done
[[ $(stat -c '%a:%u:%g' /run/dbus) == 755:18:18 ]]
for unit in dbus.socket systemd-networkd.service systemd-resolved.service systemd-timesyncd.service; do
 [[ $(systemctl --root=/ is-enabled "$unit") == enabled ]]
done
if systemctl --root=/ is-enabled --quiet systemd-networkd-wait-online.service; then exit 1;fi
[[ $(systemctl --root=/ get-default) == multi-user.target ]]
getent hosts localhost
findmnt --verify --tab-file /etc/fstab --verbose
printf 'Native offline configuration accepted; boot, DHCP and service operation remain H12 tests\n'
INNER
python3 /opt/toddy-build/scripts/build/audit_native_payload.py > /var/log/toddy/h08-base-config-payload.json
python3 - <<'PY'
import json
from pathlib import Path
r=json.loads(Path('/var/log/toddy/h08-base-config-payload.json').read_text())
assert not r['findings'],r['findings']
assert not r['duplicate_owners'],r['duplicate_owners']
print('Native package payload/ownership preserved after base configuration')
PY
python3 /opt/toddy-build/scripts/build/audit_unowned_files.py > /var/log/toddy/h08-base-config-unowned.json
python3 - <<'PY'
import json
from pathlib import Path
r=json.loads(Path('/var/log/toddy/h08-base-config-unowned.json').read_text())
assert not r['unknown'],r['unknown']
assert not r['pending_h08_configuration'],r['pending_h08_configuration']
print('Bootstrap configuration replaced; runtime links and owned service targets explicitly classified')
PY
