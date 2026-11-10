#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/nowait-case-21 ]]
[[ $(stat -f -c %T /build) == ext2/ext3 ]]
ulimit -c 0
casework=/build/nowait-case-21
mkdir -p "$casework/src"
cp -a /src/harness "$casework/harness"
cp /src/src/libaio.h "$casework/src/"
make -C "$casework/harness" cases/21.p LIBAIO=/build/compile/src/libaio.a > /build/nowait-21-compile.log 2>&1
cd "$casework/harness"
timeout 25 ./runtests.sh cases/21.p > /build/nowait-21-run.log 2>&1
