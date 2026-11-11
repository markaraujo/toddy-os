#!/bin/bash
set -euo pipefail
test "$(id -u)" = 101
awk '/^NoNewPrivs:/ {n=$2} /^CapEff:/ {c=$2} END {exit !(n==1 && c=="0000000000000000")}' /proc/self/status
test "$(findmnt -n -o OPTIONS /src | tr , '\n' | sed -n '/^ro$/p')" = ro
test "$(findmnt -n -o OPTIONS /usr | tr , '\n' | sed -n '/^ro$/p')" = ro
awk -F: 'NR > 2 {gsub(/ /, "", $1); if ($1 != "lo") exit 1; count++} END {if (count != 1) exit 1}' /proc/net/dev
awk 'NR > 1 && NF {exit 1}' /proc/net/route
printf 'UID101, no effective capabilities, NNP, read-only inputs and loopback-only namespace verified\n'
export PYTHON=/usr/bin/python3 PYTHONDONTWRITEBYTECODE=1 NO_LOCK_IN_TOP=1 NO_LOCK_IN_RUN=1
cd /src
/bin/sh ./configure --out=/build/probe-configured --prefix=/usr --sysconfdir=/etc \
    --localstatedir=/var --with-piddir=/run/samba --with-pammodulesdir=/usr/lib/security \
    --enable-fhs --without-ad-dc --with-system-mitkrb5 --with-systemd \
    --without-ldap --without-ads --without-json --disable-python --without-ldb-lmdb --disable-rpath-install
test -s /build/probe-configured/config.log
test -s /build/probe-configured/c4che/_cache.py
