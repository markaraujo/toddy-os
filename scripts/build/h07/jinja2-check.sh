#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' jinja2) == 'install ok installed' ]]
chroot_run <<'INNER'
set -euo pipefail
python3 -c "from jinja2 import Environment; e=Environment(autoescape=True); assert e.from_string('{{ x }}').render(x='<native>')=='&lt;native&gt;'"
INNER
