#!/bin/bash
# Frozen LFS 13.1-systemd chapter 8; guarded disposable target only.
set -euo pipefail
cd /sources/systemd-261.2
test ! -e /sources/stage/systemd
mkdir -p /sources/evidence/h07-systemd
sed -e 's/GROUP="render"/GROUP="video"/' -e 's/GROUP="sgx", //' -i rules.d/50-udev-default.rules.in
mkdir build
cd build
meson setup .. --prefix=/usr --buildtype=release --wrap-mode=nofallback \
 -D default-dnssec=no -D firstboot=false -D install-tests=false \
 -D ldconfig=false -D sysusers=false -D rpmmacrosdir=no -D homed=disabled \
 -D man=disabled -D mode=release -D pamconfdir=no -D dev-kvm-mode=0660 \
 -D nobody-group=nogroup -D sysupdate=disabled -D ukify=disabled \
 -D docdir=/usr/share/doc/systemd-261.2
ninja -j8
if [[ ! -e /etc/os-release ]]; then
 printf 'NAME="Toddy OS"\nID=toddy\nPRETTY_NAME="Toddy OS experimental build"\n' > /etc/os-release
fi
# UTF-8 is required by upstream ellipsis/terminal-width assertions.
set +e
LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8 unshare -m ninja test 2>&1 | tee /sources/evidence/h07-systemd/check.log
results=("${PIPESTATUS[@]}")
set -e
[[ ${results[1]} == 0 ]]
printf '%s\n' "${results[0]}" > /sources/evidence/h07-systemd/check.exit
python3 /sources/toddy-evaluate-systemd.py /sources/evidence/h07-systemd meson-logs/testlog.json
DESTDIR=/sources/stage/systemd ninja install
mkdir -p /sources/stage/systemd/usr/share/man
tar -xf /sources/systemd-man-pages-261.2.tar.xz --no-same-owner --strip-components=1 -C /sources/stage/systemd/usr/share/man
cp -a meson-logs /sources/evidence/h07-systemd/
cd ..
mkdir -p /sources/stage/systemd/usr/share/doc/systemd-261.2
cp -a LICENSES /sources/stage/systemd/usr/share/doc/systemd-261.2/

mkdir -p /sources/stage/systemd/usr/share/doc/systemd
cat LICENSE.GPL2 LICENSE.LGPL2.1 > /sources/stage/systemd/usr/share/doc/systemd/copyright
