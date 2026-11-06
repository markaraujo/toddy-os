#!/bin/bash
# Frozen LFS 13.1-systemd chapter 8; guarded disposable target only.
set -euo pipefail
cd /sources/e2fsprogs-1.47.4
test ! -e /sources/stage/e2fsprogs
mkdir -p /sources/evidence/h07-e2fsprogs
mkdir build
cd build
../configure --prefix=/usr --sysconfdir=/etc --enable-elf-shlibs \
 --disable-libblkid --disable-libuuid --disable-uuidd --disable-fsck
make
make check 2>&1 | tee /sources/evidence/h07-e2fsprogs/check.log
make DESTDIR=/sources/stage/e2fsprogs install
rm -f /sources/stage/e2fsprogs/usr/lib/{libcom_err,libe2p,libext2fs,libss}.a
gunzip /sources/stage/e2fsprogs/usr/share/info/libext2fs.info.gz
makeinfo -o doc/com_err.info ../lib/et/com_err.texinfo
install -m644 doc/com_err.info /sources/stage/e2fsprogs/usr/share/info
sed 's/metadata_csum_seed,//' -i /sources/stage/e2fsprogs/etc/mke2fs.conf
cd ..

mkdir -p /sources/stage/e2fsprogs/usr/share/doc/e2fsprogs
cat NOTICE > /sources/stage/e2fsprogs/usr/share/doc/e2fsprogs/copyright
