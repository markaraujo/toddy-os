#!/bin/bash
# BLFS 13.1 Node 24.19.0; private bundled libraries do not replace foundation ABI.
set -euo pipefail
[[ $(id -u) == 101 && -f /src/configure && -d /stage ]]
test ! -e /build/source
mkdir /build/source
cp -R --no-preserve=ownership /src/. /build/source/
cd /build/source
# Node's configure generates source-tree outputs. The original /src stays read-only;
# this is a disposable derived build copy. No runtime npm is required by the worker.
./configure --prefix=/usr --without-npm --without-corepack --ninja --dest-cpu=x64
ninja -C out/Release -j4
./out/Release/node --version | grep -Fx 'v24.19.0'
./out/Release/node -e 'const c = require("node:crypto"); if (c.createHash("sha256").update("toddy").digest("hex").length !== 64) process.exit(1); console.log("native crypto passed")'
make DESTDIR=/stage install
test -x /stage/usr/bin/node
