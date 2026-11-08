#!/bin/bash
# BLFS13.1 libpng1.6.58 for Cairo/GDK; no unqualified APNG patch/system-Firefox flag.
set -euo pipefail
[[ $(id -u) == 101 && -d /stage ]]
mkdir /build/compile
cd /build/compile
/src/configure --prefix=/usr --disable-static
make -j4
make check -j4 > /build/check.log 2>&1
python3 - <<'TEST'
import json,re
from pathlib import Path
log=Path('/build/compile/test-suite.log').read_text()
counts={k:int(v) for k,v in re.findall(r'^# (TOTAL|PASS|SKIP|XFAIL|FAIL|XPASS|ERROR):\s*(\d+)',log,re.M)}
assert counts['TOTAL']>0 and counts['TOTAL']==counts['PASS']
assert all(counts[k]==0 for k in ['SKIP','XFAIL','FAIL','XPASS','ERROR'])
Path('/build/test-results.json').write_text(json.dumps(counts,indent=2)+'\n')
TEST
make DESTDIR=/stage install
[[ -f /stage/usr/lib/libpng16.so.16 && -f /stage/usr/include/png.h ]]
