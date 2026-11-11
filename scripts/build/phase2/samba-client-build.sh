#!/bin/bash
set -euo pipefail
test "$(id -u)" = 101
awk '/^NoNewPrivs:/ {n=$2} /^CapEff:/ {c=$2} END {exit !(n==1 && c=="0000000000000000")}' /proc/self/status
test "$(findmnt -n -o OPTIONS /src | tr , '\n' | sed -n '/^ro$/p')" = ro
test "$(findmnt -n -o OPTIONS /usr | tr , '\n' | sed -n '/^ro$/p')" = ro
awk -F: 'NR > 2 {gsub(/ /, "", $1); if ($1 != "lo") exit 1; count++} END {if (count != 1) exit 1}' /proc/net/dev
awk 'NR > 1 && NF {exit 1}' /proc/net/route
export PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=1 WAF_MAKE=1 NO_LOCK_IN_TOP=1 NO_LOCK_IN_RUN=1
cd /build/probe-configured
test -s c4che/_cache.py
(cd default; /usr/bin/python3 /src/buildtools/bin/waf build --targets=smbclient,client/smbclient --jobs=6)
find default/source3 -type f \( -name 'libsmbclient.so*' -o -name smbclient \) -print | sort > /build/samba-client-artifacts-1.txt
test -s /build/samba-client-artifacts-1.txt
grep -Eq '/libsmbclient[.]so([.]|$)' /build/samba-client-artifacts-1.txt
grep -Eq '/smbclient$' /build/samba-client-artifacts-1.txt
