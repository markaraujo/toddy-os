#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/project ]]
cp -a /src /build/project
cd /build/project
patch --batch --forward --fuzz=0 -Np1 -i /src/toddy-supplemental/lua-5.4.8-shared_library-1.patch \
    > /build/patch.log 2>&1
make -j4 linux > /build/compile.log 2>&1
make test > /build/version.log 2>&1
make INSTALL_TOP=/stage/usr INSTALL_DATA='cp -d' INSTALL_MAN=/stage/usr/share/man/man1 \
    TO_LIB='liblua.so liblua.so.5.4 liblua.so.5.4.8' install > /build/stage.log 2>&1
mkdir -p /stage/usr/lib/pkgconfig
cat > /stage/usr/lib/pkgconfig/lua.pc <<'PC'
prefix=/usr
exec_prefix=${prefix}
libdir=${exec_prefix}/lib
includedir=${prefix}/include
Name: Lua
Description: An Extensible Extension Language
Version: 5.4.8
Libs: -L${libdir} -llua -lm -ldl
Cflags: -I${includedir}
PC
cd /build/project/toddy-supplemental/lua-5.4.8-tests
LD_LIBRARY_PATH=/stage/usr/lib /stage/usr/bin/lua -e '_U=true' all.lua > /build/upstream-tests.log 2>&1
cc -std=c11 -Wall -Wextra -Werror /src/toddy-probe.c -I/stage/usr/include \
    -L/stage/usr/lib -Wl,-rpath,/stage/usr/lib -llua -lm -ldl -o /build/consumer
/build/consumer > /build/consumer.log 2>&1
python3 - <<'PY'
from pathlib import Path
import json
log=Path('/build/upstream-tests.log').read_text();assert 'final OK' in log
Path('/build/test-results.json').write_text(json.dumps({
    'scope':'Native Lua shared library/interpreter and original upstream basic suite for Wireplumber; no desktop/session routing acceptance',
    'upstream_basic_suite_exit':0,'upstream_mode':'_U=true as frozen BLFS13.1; portable/soft basic mode, internal C harness and long/nonportable tests omitted',
    'upstream_final_marker':'final OK','version_banner_only':'make test is version output, not an additional passing suite',
    'staged_consumer_exit':0,'profile':'BLFS13.1 shared-library patch and pkg-config layout; no shell/user preference edits'
},indent=2)+'\n')
PY
