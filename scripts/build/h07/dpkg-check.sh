#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' dpkg) == 'install ok installed' ]]
chroot_run <<'INNER'
set -euo pipefail
dpkg --version | grep -F '1.22.22'
dpkg-deb --version | grep -F '1.22.22'
dpkg-query --version | grep -F '1.22.22'
[[ $(dpkg --print-architecture) == amd64 ]]
[[ $(dpkg-architecture -qDEB_HOST_ARCH) == amd64 ]]
fixture=$(mktemp -d /tmp/toddy-native-dpkg.XXXXXX)
trap 'rm -rf "$fixture"' EXIT
before=$(sha256sum /var/lib/dpkg/status)
mkdir -p "$fixture/root/var/lib/dpkg"
touch "$fixture/root/var/lib/dpkg/status"
for version in 1 2; do
 pkg="$fixture/pkg-$version"
 mkdir -p "$pkg/DEBIAN" "$pkg/etc" "$pkg/usr/share/toddy-dpkg-probe"
 printf 'Package: toddy-dpkg-probe\nVersion: %s\nArchitecture: all\nMaintainer: Toddy OS <build@example.invalid>\nDescription: Disposable native package probe\n' "$version" > "$pkg/DEBIAN/control"
 printf '/etc/toddy-dpkg-probe.conf\n' > "$pkg/DEBIAN/conffiles"
 printf 'default-%s\n' "$version" > "$pkg/etc/toddy-dpkg-probe.conf"
 printf 'payload-%s\n' "$version" > "$pkg/usr/share/toddy-dpkg-probe/value"
 dpkg-deb --build "$pkg" "$fixture/version-$version.deb"
done
dpkg --root="$fixture/root" --log="$fixture/operations.log" --install "$fixture/version-1.deb"
printf 'owner-customized\n' > "$fixture/root/etc/toddy-dpkg-probe.conf"
dpkg --root="$fixture/root" --log="$fixture/operations.log" --force-confold --force-confdef --install "$fixture/version-2.deb"
grep -Fx owner-customized "$fixture/root/etc/toddy-dpkg-probe.conf"
grep -Fx payload-2 "$fixture/root/usr/share/toddy-dpkg-probe/value"
dpkg-query --admindir="$fixture/root/var/lib/dpkg" -S /usr/share/toddy-dpkg-probe/value | grep -F toddy-dpkg-probe
conflict="$fixture/conflict"
mkdir -p "$conflict/DEBIAN" "$conflict/usr/share/toddy-dpkg-probe"
printf 'Package: toddy-dpkg-conflict\nVersion: 1\nArchitecture: all\nMaintainer: Toddy OS <build@example.invalid>\nDescription: Intentional conflict probe\n' > "$conflict/DEBIAN/control"
printf 'must-not-overwrite\n' > "$conflict/usr/share/toddy-dpkg-probe/value"
dpkg-deb --build "$conflict" "$fixture/conflict.deb"
set +e
dpkg --root="$fixture/root" --log="$fixture/operations.log" --install "$fixture/conflict.deb" > "$fixture/conflict.log" 2>&1
result=$?
set -e
[[ $result != 0 ]]
grep -F 'trying to overwrite' "$fixture/conflict.log"
grep -Fx payload-2 "$fixture/root/usr/share/toddy-dpkg-probe/value"
dpkg --root="$fixture/root" --log="$fixture/operations.log" --remove toddy-dpkg-probe
test -f "$fixture/root/etc/toddy-dpkg-probe.conf"
dpkg --root="$fixture/root" --log="$fixture/operations.log" --purge toddy-dpkg-probe
test ! -e "$fixture/root/etc/toddy-dpkg-probe.conf"
[[ $(sha256sum /var/lib/dpkg/status) == "$before" ]]
printf 'Native package build/install/ownership/conffile upgrade/conflict/remove/purge passed; main DB unchanged\n'
INNER
