#!/bin/bash
# Frozen BLFS13.1 ICU78.3, out-of-source build with original check target.
set -euo pipefail
[[ $(id -u) == 101 && -f /src/source/configure && -d /stage ]]
mkdir /build/compile
cd /build/compile
/src/source/configure --prefix=/usr --disable-static --with-data-packaging=library
make -j4
make -j4 check > /build/upstream-check.log 2>&1
printf '0\n' > /build/upstream-check.exit
make DESTDIR=/stage install
export PKG_CONFIG_PATH=/stage/usr/lib/pkgconfig
cc -Wall -Wextra -Werror /src/toddy-probe.c -o /build/native-consumer \
    -I/stage/usr/include -L/stage/usr/lib -Wl,-rpath,/stage/usr/lib \
    $(pkg-config --cflags --libs icu-i18n icu-uc)
LD_LIBRARY_PATH=/stage/usr/lib /build/native-consumer > /build/native-consumer.log 2>&1
LD_LIBRARY_PATH=/stage/usr/lib python3 - <<'PY'
import json,subprocess
from pathlib import Path
result=subprocess.run(['/stage/usr/bin/uconv','-f','UTF-8','-t','UTF-16LE'],input='ação'.encode(),capture_output=True,check=True)
assert result.stdout=='ação'.encode('utf-16le')
Path('/build/test-results.json').write_text(json.dumps({'scope':'Native original ICU make check, NFC/Portuguese collation/malformed UTF8 refusal and real uconv CLI; no GNOME/browser acceptance','version':'78.3','upstream_exit':0,'staged_consumer_exit':0,'staged_cli_exit':0,'converted_bytes':len(result.stdout)},indent=2)+'\n')
PY
