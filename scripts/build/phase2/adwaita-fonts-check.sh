#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/h06/common.sh
chroot_run <<'NATIVE'
set -euo pipefail
[[ $(dpkg-query -W -f='${Status}' adwaita-fonts) == 'install ok installed' ]]
test -z "$(dpkg --audit)"
apt-get check
python3 - <<'PY'
import subprocess
from pathlib import Path
fonts=list(Path('/usr/share/fonts/Adwaita').glob('*.ttf'));assert len(fonts)==6
for path in fonts:
    assert subprocess.check_output(['dpkg-query','-S',str(path)],text=True).startswith('adwaita-fonts: ')
for family in ['Adwaita Sans','Adwaita Mono']:
    for style in ['Regular','Italic','Bold','Bold Italic']:
        result=subprocess.check_output(['fc-match','-f','%{family}\n%{file}\n',family+':style='+style],text=True).splitlines()
        assert family in result[0] and result[1].startswith('/usr/share/fonts/Adwaita/'),result
        chars=subprocess.check_output(['fc-query','-f','%{charset}',result[1]],text=True)
        assert '20-7e' in chars,'ASCII coverage missing'
assert list(Path('/var/cache/fontconfig').glob('*.cache-*'))
PY
NATIVE
