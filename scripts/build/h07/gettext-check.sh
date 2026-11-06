#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' gettext) == 'install ok installed' ]]
check_native /usr/bin/msgfmt 1.0
chroot_run <<'INNER'
set -euo pipefail
cat > /tmp/toddy-gettext.po <<'PO'
msgid ""
msgstr "Content-Type: text/plain; charset=UTF-8\n"

msgid "hello"
msgstr "ola"
PO
msgfmt /tmp/toddy-gettext.po -o /tmp/toddy-gettext.mo
msgunfmt /tmp/toddy-gettext.mo | grep -F 'msgstr "ola"'
rm /tmp/toddy-gettext.{po,mo}
INNER
