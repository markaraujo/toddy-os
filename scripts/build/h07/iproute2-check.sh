#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' iproute2) == 'install ok installed' ]]
chroot_run <<'INNER'
set -euo pipefail
ip -Version | grep -F 7.1.0
ip -j address show lo > /tmp/toddy-ip.json
python3 -c 'import json; a=json.load(open("/tmp/toddy-ip.json")); assert any(i["ifname"]=="lo" for i in a)'
tc qdisc show dev lo
ss -ln > /tmp/toddy-sockets.txt
rm /tmp/toddy-ip.json /tmp/toddy-sockets.txt
INNER
