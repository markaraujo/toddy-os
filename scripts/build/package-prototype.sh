#!/bin/bash
# Exercise project-built .deb payloads in a throwaway root INSIDE the VM.
set -euo pipefail
[[ $(hostname) == toddy-builder ]] || exit 1
work=$(mktemp -d /var/tmp/toddy-pkg-probe.XXXXXX)
trap 'rm -rf "$work"' EXIT
root=$work/root
mkdir -p "$root/var/lib/dpkg" "$root/var/log"
touch "$root/var/lib/dpkg/status"
build_probe() {
    local package=$1 version=$2 payload=$3
    local stage=$work/$package-$version
    mkdir -p "$stage/DEBIAN" "$stage/usr/share/toddy-probe" "$stage/etc"
    cat > "$stage/DEBIAN/control" <<CONTROL
Package: $package
Version: $version
Architecture: all
Maintainer: Toddy OS Development <noreply@example.invalid>
Description: Disposable package ownership acceptance probe
CONTROL
    echo "$payload" > "$stage/usr/share/toddy-probe/value"
    echo "default-$version" > "$stage/etc/toddy-probe.conf"
    echo /etc/toddy-probe.conf > "$stage/DEBIAN/conffiles"
    dpkg-deb --build --root-owner-group "$stage" "$work/$package-$version.deb"
}
build_probe toddy-probe 1.0 one
build_probe toddy-probe 2.0 two
build_probe toddy-conflict 1.0 conflict
pkg() { dpkg --root="$root" "$@"; }
pkg --install "$work/toddy-probe-1.0.deb"
[[ $(cat "$root/usr/share/toddy-probe/value") == one ]]
dpkg-query --admindir="$root/var/lib/dpkg" -S /usr/share/toddy-probe/value
echo user-setting > "$root/etc/toddy-probe.conf"
pkg --force-confold --install "$work/toddy-probe-2.0.deb"
[[ $(cat "$root/usr/share/toddy-probe/value") == two ]]
[[ $(cat "$root/etc/toddy-probe.conf") == user-setting ]]
if pkg --install "$work/toddy-conflict-1.0.deb"; then echo 'Conflict was accepted' >&2; exit 1; fi
[[ $(cat "$root/usr/share/toddy-probe/value") == two ]]
echo 'PASS: ownership conflict rejected without replacing payload'
cp -a "$root" "$work/checkpoint"
# Deliberately invalid dependency: dpkg must not configure this update.
echo 'Depends: toddy-nonexistent-dependency' >> "$work/toddy-probe-2.0/DEBIAN/control"
sed -i 's/Version: 2.0/Version: 3.0/' "$work/toddy-probe-2.0/DEBIAN/control"
dpkg-deb --build --root-owner-group "$work/toddy-probe-2.0" "$work/bad-update.deb"
if pkg --force-confold --install "$work/bad-update.deb"; then echo 'Missing dependency accepted' >&2; exit 1; fi
[[ $(dpkg-query --admindir="$root/var/lib/dpkg" -W -f='${Status}' toddy-probe) != 'install ok installed' ]]
# Restore the entire offline package root/database, not only one file.
mv "$root" "$work/failed-root"
cp -a "$work/checkpoint" "$root"
[[ $(dpkg-query --admindir="$root/var/lib/dpkg" -W -f='${Version}' toddy-probe) == 2.0 ]]
[[ $(cat "$root/etc/toddy-probe.conf") == user-setting ]]
echo 'PASS: failed dependency update restored from full-root checkpoint'
pkg --remove toddy-probe
[[ ! -e $root/usr/share/toddy-probe/value && -f $root/etc/toddy-probe.conf ]]
pkg --purge toddy-probe
[[ ! -e $root/etc/toddy-probe.conf ]]
echo 'PASS: install, ownership, upgrade, conffile preservation, conflicts, dependency rejection, rollback, remove and purge'
