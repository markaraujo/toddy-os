#!/bin/bash
set -euo pipefail
cd /sources/e2fsprogs-1.47.4/build
test ! -e /sources/stage/e2fsprogs
printf '2\n' > /sources/evidence/h07-e2fsprogs/check.exit
python3 /sources/toddy-evaluate-e2fs.py /sources/evidence/h07-e2fsprogs tests ..
mkdir -p /sources/evidence/h07-e2fsprogs/test-reports
cp tests/m_assume_storage_prezeroed.{failed,log,out} /sources/evidence/h07-e2fsprogs/test-reports/
make DESTDIR=/sources/stage/e2fsprogs install
rm -f /sources/stage/e2fsprogs/usr/lib/{libcom_err,libe2p,libext2fs,libss}.a
gunzip /sources/stage/e2fsprogs/usr/share/info/libext2fs.info.gz
makeinfo -o doc/com_err.info ../lib/et/com_err.texinfo
install -m644 doc/com_err.info /sources/stage/e2fsprogs/usr/share/info
sed 's/metadata_csum_seed,//' -i /sources/stage/e2fsprogs/etc/mke2fs.conf
cd ..

mkdir -p /sources/stage/e2fsprogs/usr/share/doc/e2fsprogs
cat NOTICE > /sources/stage/e2fsprogs/usr/share/doc/e2fsprogs/copyright
