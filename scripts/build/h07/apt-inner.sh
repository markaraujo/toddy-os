#!/bin/bash
set -euo pipefail
cd /sources/apt-3.0.4
test ! -e /sources/stage/apt
mkdir -p /sources/evidence/h07-apt vendor/toddy
cat > vendor/toddy/apt.conf-00toddy <<'APTCONF'
APT::Sandbox::User "_apt";
APT::Sandbox::Seccomp "true";
Acquire::AllowInsecureRepositories "false";
Acquire::AllowDowngradeToInsecureRepositories "false";
APT::Get::AllowUnauthenticated "false";
APTCONF
cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=/usr \
 -DCMAKE_INSTALL_LIBDIR=lib -DCMAKE_INSTALL_LIBEXECDIR=libexec \
 -DCMAKE_INSTALL_SYSCONFDIR=/etc -DCMAKE_INSTALL_LOCALSTATEDIR=/var \
 -DCURRENT_VENDOR=toddy -DDEFAULT_PAGER=less -DWITH_DOC=OFF -DWITH_TESTS=ON -DUSE_NLS=ON
# These are optional to upstream, but required by the selected native profile.
# Refuse a silently reduced build if library discovery regresses.
for feature in SECCOMP SYSTEMD UDEV ZSTD; do
 grep -Fx "#define HAVE_$feature" build/include/config.h
done
cp build/include/config.h /sources/evidence/h07-apt/config.h
cp build/CMakeCache.txt /sources/evidence/h07-apt/CMakeCache.txt
cmake --build build -j8
chown -R tester:tester .
su tester -c 'cd build && ctest --output-on-failure' 2>&1 | tee /sources/evidence/h07-apt/ctest.log
DESTDIR=/sources/stage/apt cmake --install build
install -Dm644 COPYING /sources/stage/apt/usr/share/doc/apt/copyright
cp README.md /sources/stage/apt/usr/share/doc/apt/
# Root identity/account databases are generated configuration, never package data.
if ! getent passwd _apt >/dev/null; then
 useradd --system --user-group --home-dir /nonexistent --shell /usr/bin/nologin _apt
fi
[[ $(getent passwd _apt | cut -d: -f7) == /usr/bin/nologin ]]
