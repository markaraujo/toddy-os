#!/bin/bash
set -euo pipefail
test "$(id -u)" = 101
awk '/^NoNewPrivs:/ {n=$2} /^CapEff:/ {c=$2} END {exit !(n==1 && c=="0000000000000000")}' /proc/self/status
test -s /build/samba-client-artifacts-1.txt
test ! -e /build/stage-full
mkdir /build/stage-full
export PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=1 WAF_MAKE=1 NO_LOCK_IN_TOP=1 NO_LOCK_IN_RUN=1
cd /build/probe-configured/default
/usr/bin/python3 /src/buildtools/bin/waf install --destdir=/build/stage-full --jobs=6
test -x /build/stage-full/usr/bin/smbclient
test -s /build/stage-full/usr/lib/libsmbclient.so.0
test -s /build/stage-full/usr/lib/pkgconfig/smbclient.pc
test -s /build/stage-full/usr/include/samba-4.0/libsmbclient.h
find /build/stage-full -mindepth 1 -printf '%y %P\n' | sort > /build/samba-client-stage-2.txt
