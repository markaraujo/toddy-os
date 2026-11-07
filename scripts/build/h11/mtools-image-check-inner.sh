#!/bin/bash
# Actual installed package acceptance; the caller appends the shared roundtrip.
set -euo pipefail
[[ $(dpkg-query -W -f='${Status} ${Version}' mtools) == 'install ok installed 4.0.50-1' ]]
dpkg-query -S /usr/bin/mformat /usr/bin/mcopy /usr/bin/mdir
