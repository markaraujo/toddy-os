#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/h06/common.sh
chroot_run <<'NATIVE'
set -euo pipefail
[[ $(dpkg-query -W -f='${Status}' llama-cpp) == 'install ok installed' ]]
test -z "$(dpkg --audit)"
apt-get check
python3 - <<'CPU'
from pathlib import Path
import json
profile=json.loads(Path('/usr/share/doc/llama-cpp/cpu-profile.json').read_text())
flags=set(next(l for l in Path('/proc/cpuinfo').read_text().splitlines() if l.startswith('flags')).split(':',1)[1].split())
assert set(profile['cpu_flags'])<=flags
assert not profile['weights_in_package'] and not profile['gpu']
CPU
NATIVE
for command in llama-server llama-completion; do
    result=$(chroot --userspec=101:101 "$LFS" /usr/bin/env -i HOME=/tmp \
        PATH=/usr/bin:/usr/sbin "/usr/bin/$command" --version 2>&1)
    printf '%s\n' "$result"
    [[ $result == *'0.9.0'* ]]
done
