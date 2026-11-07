#!/bin/bash
set -euo pipefail
source_dir=${TODDY_APT_SOURCE:-/sources/apt-3.0.4}
evidence_dir=${TODDY_APT_EVIDENCE:-/sources/evidence/h07-apt}
build_jobs=${TODDY_APT_JOBS:-8}
[[ $build_jobs =~ ^[1-8]$ ]]
cd "$source_dir"
test ! -e /sources/stage/apt
apt_configure() {
mkdir -p "$evidence_dir" vendor/toddy
cat > vendor/toddy/apt.conf-00toddy <<'APTCONF'
APT::Sandbox::User "_apt";
APT::Sandbox::Seccomp "true";
Acquire::AllowInsecureRepositories "false";
Acquire::AllowDowngradeToInsecureRepositories "false";
APT::Get::AllowUnauthenticated "false";
APTCONF
berkeley=()
if [[ -n ${TODDY_APT_BERKELEY_PREFIX:-} ]]; then
 test -f "$TODDY_APT_BERKELEY_PREFIX/include/db.h"
 test -f "$TODDY_APT_BERKELEY_PREFIX/lib/libdb-5.3.so"
 berkeley=(-DBERKELEY_INCLUDE_DIRS="$TODDY_APT_BERKELEY_PREFIX/include"
           -DBERKELEY_LIBRARIES="$TODDY_APT_BERKELEY_PREFIX/lib/libdb-5.3.so")
fi
cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=/usr \
 -DCMAKE_INSTALL_LIBDIR=lib -DCMAKE_INSTALL_LIBEXECDIR=libexec \
 -DCMAKE_INSTALL_SYSCONFDIR=/etc -DCMAKE_INSTALL_LOCALSTATEDIR=/var \
 -DCURRENT_VENDOR=toddy -DDEFAULT_PAGER=less -DWITH_DOC=OFF -DWITH_TESTS=ON -DUSE_NLS=ON "${berkeley[@]}"
# These are optional to upstream, but required by the selected native profile.
# Refuse a silently reduced build if library discovery regresses.
for feature in SECCOMP SYSTEMD UDEV ZSTD; do
 grep -Fx "#define HAVE_$feature" build/include/config.h
done
cp build/include/config.h "$evidence_dir/config.h"
cp build/CMakeCache.txt "$evidence_dir/CMakeCache.txt"
}
apt_build() {
cmake --build build -j"$build_jobs"
}
apt_check() {
chown -R tester:tester .
su tester -c 'cd build && ctest --output-on-failure --no-tests=error' 2>&1 | tee "$evidence_dir/ctest.log"
}
apt_install() {
DESTDIR=/sources/stage/apt cmake --install build
install -Dm644 COPYING /sources/stage/apt/usr/share/doc/apt/copyright
cp README.md /sources/stage/apt/usr/share/doc/apt/
# Root identity/account databases are generated configuration, never package data.
if ! getent passwd _apt >/dev/null; then
 useradd --system --user-group --home-dir /nonexistent --shell /usr/bin/nologin _apt
fi
[[ $(getent passwd _apt | cut -d: -f7) == /usr/bin/nologin ]]
}
case ${1:-all} in
 configure) apt_configure ;;
 build) apt_build ;;
 check) apt_check ;;
 install) apt_install ;;
 all) apt_configure; apt_build; apt_check; apt_install ;;
 *) echo "Unknown native APT stage" >&2; exit 2 ;;
esac
