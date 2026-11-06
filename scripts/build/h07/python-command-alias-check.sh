#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
chroot_run <<'INNER'
set -euo pipefail
[[ $(readlink /usr/bin/python) == python3 ]]
dpkg-query -S /usr/bin/python | grep -F 'python:'
python -c 'import sys; assert sys.version_info[:3]==(3,14,10); print("Native unversioned Python 3.14.10 command passed")'
fixture=$(mktemp -d /tmp/python-command-native.XXXXXX)
trap 'rm -rf "$fixture"' EXIT
python - "$fixture" <<'PY'
import pathlib,py_compile,sys
root=pathlib.Path(sys.argv[1])
for index,name in enumerate(['/usr/share/vim/vim92/tools/demoserver.py','/usr/share/doc/dbus/examples/GetAllMatchRules.py']):
 py_compile.compile(name,cfile=str(root/f'{index}.pyc'),doraise=True)
print('Installed unversioned Python consumers compile with the selected interpreter')
PY
[[ $(printf hello | /usr/lib/python3.14/encodings/rot_13.py) == uryyb ]]
INNER
