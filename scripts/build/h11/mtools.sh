#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
python3 /opt/toddy-build/scripts/build/h10/require_media_tools.py
cd "$LFS/sources"
python3 "$SOURCE_TOOL" mtools-4.0.50.tar.bz2
chroot_run <<'INNER'
set -euo pipefail
cd /sources/mtools-4.0.50
test ! -e /sources/stage/mtools
mkdir -p /sources/evidence/h11-mtools
./configure --prefix=/usr --sysconfdir=/etc --without-x --disable-floppyd
make
# Upstream explicitly has no self tests. Preserve that fact, not a PASS claim.
make check > /sources/evidence/h11-mtools/upstream-check-target.log 2>&1
make DESTDIR=/sources/stage/mtools install
install -Dm644 COPYING /sources/stage/mtools/usr/share/doc/mtools/copyright
cp README INSTALL NEWS mtools.texi /sources/stage/mtools/usr/share/doc/mtools/
test ! -e /sources/stage/mtools/usr/bin/floppyd
INNER
cp /opt/toddy-build/LICENSES/GFDL-1.3.txt "$LFS/sources/stage/mtools/usr/share/doc/mtools/"
cat > "$LFS/sources/stage/mtools/usr/share/doc/mtools/profile.txt" <<'PROFILE'
Native GNU Mtools image construction profile, 4.0.50.
The floppyd/X11 server is disabled; no service is installed or enabled.
Acceptance covers private FAT image creation, EFI copy/readback, UTF-8 names
and malformed-image refusal. Actual ISO UEFI boot remains a separate gate.
Auxiliary archive scripts require their respective format tools; optional
lzip handling requires a separately installed lzip command. It is not tested
or required by the GRUB image-construction path.
PROFILE
python3 /opt/toddy-build/scripts/build/stage_package.py mtools 4.0.50-1 \
 "$LFS/sources/stage/mtools" --depends 'glibc, bash, coreutils, diffutils, tar, gzip, bzip2, grep, sed, gawk' \
 --source mtools-4.0.50.tar.bz2 --recipe /opt/toddy-build/scripts/build/h11/mtools.sh --install
