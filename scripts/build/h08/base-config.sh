#!/bin/bash
# Prepared LFS 13.1-systemd configuration; H07 must have actually passed.
source /opt/toddy-build/scripts/build/h06/common.sh
python3 /opt/toddy-build/scripts/build/h08/require_gate.py
stage="$LFS/sources/stage/toddy-base-config"
python3 /opt/toddy-build/scripts/build/h08/stage_config.py "$stage"
python3 /opt/toddy-build/scripts/build/h08/prepare_config_install.py
conffiles=()
while IFS= read -r -d '' path; do
 conffiles+=(--conffile "/${path#"$stage/"}")
done < <(find "$stage/etc" -type f -print0)
python3 /opt/toddy-build/scripts/build/stage_package.py toddy-base-config 0.1-1 "$stage" \
 --architecture all --depends 'systemd, dbus, bash, glibc-locales, tzdata, kbd, tcsh, filesystem-layout' \
 "${conffiles[@]}" --recipe /opt/toddy-build/scripts/build/h08/base-config.sh --install
chroot_run <<'INNER'
set -euo pipefail
# Runtime configuration links are mutable generated state, not immutable
# package payload. Later package updates preserve owner-selected timezone/DNS.
if [[ ! -e /etc/localtime && ! -L /etc/localtime ]]; then
 ln -s ../usr/share/zoneinfo/UTC /etc/localtime
fi
if [[ ! -e /etc/resolv.conf && ! -L /etc/resolv.conf ]]; then
 ln -s /run/systemd/resolve/stub-resolv.conf /etc/resolv.conf
fi
systemd-tmpfiles --create --prefix=/run/dbus
INNER
python3 /opt/toddy-build/scripts/build/h08/offline_services.py
bash /opt/toddy-build/scripts/build/chroot-resolver.sh
