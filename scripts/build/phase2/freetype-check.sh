#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/h06/common.sh
chroot_run <<'NATIVE'
set -euo pipefail
[[ $(dpkg-query -W -f='${Status}' freetype) == 'install ok installed' ]]
test -z "$(dpkg --audit)"
apt-get check
work=$(mktemp -d /tmp/toddy-freetype-consumer.XXXXXX)
trap 'rm -rf "$work"' EXIT
cc /sources/phase2/inputs/freetype-2.14.3/toddy-probe.c $(pkg-config --cflags --libs freetype2) -o "$work/probe"
"$work/probe"
grep -q 'work of the FreeType Team' /usr/share/doc/freetype/README.Toddy
grep -q 'The FreeType Project LICENSE' /usr/share/doc/freetype/copyright
grep -q 'GNU GENERAL PUBLIC LICENSE' /usr/share/doc/freetype/copyright
NATIVE
