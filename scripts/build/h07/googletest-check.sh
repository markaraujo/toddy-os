#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' googletest) == 'install ok installed' ]]
chroot_run <<'INNER'
set -euo pipefail
fixture=$(mktemp -d /tmp/toddy-gtest.XXXXXX)
trap 'rm -rf "$fixture"' EXIT
cat > "$fixture/test.cc" <<'C'
#include <gtest/gtest.h>
TEST(ToddyNative, LinkedFramework) { EXPECT_EQ(6*7,42); }
C
c++ -std=c++17 "$fixture/test.cc" $(pkg-config --cflags --libs gtest_main) -o "$fixture/test"
"$fixture/test"
INNER
