#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
chroot_run <<'INNER'
set -euo pipefail
[[ $(gcc -dumpmachine) == x86_64-pc-linux-gnu ]]
! gcc -print-search-dirs | grep -E '/tools|x86_64-lfs-linux-gnu'
fixture=$(mktemp -d /tmp/native-cleanup-check.XXXXXX)
trap 'rm -rf "$fixture"' EXIT
cat > "$fixture/probe.cpp" <<'CXX'
#include <thread>
#include <string>
int main(){std::string value; std::thread thread([&]{value="native";});thread.join();return value!="native";}
CXX
g++ "$fixture/probe.cpp" -pthread -o "$fixture/probe"
"$fixture/probe"
python3 -c 'import ssl, sqlite3, ctypes; assert ssl.create_default_context().cert_store_stats()["x509_ca"]>0; print("Native Python modules/trust passed")'
perl -e 'use threads; threads->create(sub{return 42})->join == 42 or die; print "Native Perl threading passed\n"'
xz --version | head -n1 | grep -F 5.8.4
INNER
