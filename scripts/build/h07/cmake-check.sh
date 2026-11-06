#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' cmake) == 'install ok installed' ]]
chroot_run <<'INNER'
set -euo pipefail
cmake --version | grep -F '4.4.2'
fixture=$(mktemp -d /tmp/toddy-cmake.XXXXXX)
trap 'rm -rf "$fixture"' EXIT
cat > "$fixture/CMakeLists.txt" <<'CMAKE'
cmake_minimum_required(VERSION 3.16)
project(toddy_native C)
enable_testing()
add_executable(toddy main.c)
add_test(NAME native COMMAND toddy)
CMAKE
printf 'int main(void) { return 0; }\n' > "$fixture/main.c"
cmake -S "$fixture" -B "$fixture/build" -G Ninja
cmake --build "$fixture/build" --parallel 8
ctest --test-dir "$fixture/build" --output-on-failure
INNER
