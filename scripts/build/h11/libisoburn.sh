#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
python3 /opt/toddy-build/scripts/build/h10/require_media_tools.py
for package in libburn libisofs; do
 [[ -f /var/log/toddy/build/h11-$package.success.json ]] || exit 1
done
cd "$LFS/sources"
python3 "$SOURCE_TOOL" libisoburn-1.5.8.pl02.tar.gz
cp /opt/toddy-build/scripts/build/h11/libisoburn-symlink-metadata.patch "$LFS/sources/libisoburn-1.5.8/"
chroot_run <<'INNER'
set -euo pipefail
cd /sources/libisoburn-1.5.8
test ! -e /sources/stage/libisoburn
mkdir -p /sources/evidence/h11-libisoburn
patch --batch --fuzz=0 -p1 < libisoburn-symlink-metadata.patch
# ADR-0077: probe the actual Glibc header, matching frozen libisofs; no
# configure-cache override or compatibility header in the installed system.
for input in configure configure.ac; do
 grep -F 'attr/xattr.h' "$input"
 sed 's@attr/xattr.h@sys/xattr.h@g' "$input" > "$input.toddy"
 chmod --reference="$input" "$input.toddy"
 touch -r "$input" "$input.toddy"
 mv "$input.toddy" "$input"
done
sha256sum configure configure.ac xorriso/read_run.c libisoburn-symlink-metadata.patch > /sources/evidence/h11-libisoburn/local-source-adaptations.sha256
./configure --prefix=/usr --disable-static --disable-ldconfig-at-install --enable-pkg-check-modules --disable-libjte --disable-libcdio
for feature in Libisofs_with_aaip_acL Libisofs_with_aaip_xattR Libisofs_with_zliB; do
 grep -F -- "-D$feature" Makefile
done
grep -F -- '-DXorriso_with_readlinE' Makefile
cp config.log /sources/evidence/h11-libisoburn/configure.log
make
# Frozen BLFS explicitly reports no upstream test suite for this package.
make DESTDIR=/sources/stage/libisoburn install
rm /sources/stage/libisoburn/usr/lib/libisoburn.la
install -Dm644 COPYING /sources/stage/libisoburn/usr/share/doc/libisoburn/copyright
cp COPYRIGHT AUTHORS README /sources/stage/libisoburn/usr/share/doc/libisoburn/
cp libisoburn-symlink-metadata.patch /sources/stage/libisoburn/usr/share/doc/libisoburn/
cat > /sources/stage/libisoburn/usr/share/doc/libisoburn/profile.txt <<'PROFILE'
Native shared libburn/libisofs stack; no bundled replacement libraries.
CLI image construction and extraction are the selected release-build path.
The retained upstream xorriso-tcltk frontend requires optional Tk/wish;
it is not exercised or advertised as a working GUI in the foundation.
Jigdo/libjte and libcdio support are disabled. No physical-media test is claimed.
Embedded MD5 detects accidental corruption; artifact identity uses SHA-256.
Toddy ADR-0077 probes Glibc sys/xattr.h and restores symlink ownership/times
without following link destinations; the source patch is retained here.
PROFILE
INNER
python3 /opt/toddy-build/scripts/build/stage_package.py libisoburn 1.5.8.pl02-1 \
 "$LFS/sources/stage/libisoburn" --depends 'glibc, libburn, libisofs, acl, zlib, readline, ncurses, bash, coreutils, grep, sed, gawk, util-linux' \
 --source libisoburn-1.5.8.pl02.tar.gz --recipe /opt/toddy-build/scripts/build/h11/libisoburn.sh --install
