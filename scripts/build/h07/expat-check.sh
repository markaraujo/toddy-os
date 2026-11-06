#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' expat) == 'install ok installed' ]]
chroot_run <<'INNER'
set -euo pipefail
printf '<toddy><native/></toddy>\n' > /tmp/toddy-valid.xml
xmlwf /tmp/toddy-valid.xml
printf '<toddy>\n' > /tmp/toddy-invalid.xml
if xmlwf /tmp/toddy-invalid.xml; then echo 'Malformed XML was accepted' >&2; exit 1; fi
rm /tmp/toddy-{valid,invalid}.xml
INNER
