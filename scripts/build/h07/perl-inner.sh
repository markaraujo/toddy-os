#!/bin/bash
# Frozen LFS 13.1-systemd chapter 8; security overlays and generic ISA explicit.
set -euo pipefail
cd /sources/perl-5.44.0
test ! -e /sources/stage/perl
export BUILD_ZLIB=False BUILD_BZIP2=0
sh Configure -des -D prefix=/usr -D vendorprefix=/usr \
 -D privlib=/usr/lib/perl5/5.44/core_perl -D archlib=/usr/lib/perl5/5.44/core_perl \
 -D sitelib=/usr/lib/perl5/5.44/site_perl -D sitearch=/usr/lib/perl5/5.44/site_perl \
 -D vendorlib=/usr/lib/perl5/5.44/vendor_perl -D vendorarch=/usr/lib/perl5/5.44/vendor_perl \
 -D man1dir=/usr/share/man/man1 -D man3dir=/usr/share/man/man3 \
 -D pager="/usr/bin/less -isR" -D useshrplib -D usethreads
make
mkdir -p /sources/evidence/h07-perl
TEST_JOBS=8 make test_harness 2>&1 | tee /sources/evidence/h07-perl/check.log
find . -type f \( -name '*.log' -o -name '*.trs' -o -name '*.sum' \) -print0 | \
 tar --null -T - -czf /sources/evidence/h07-perl/test-reports.tar.gz
make DESTDIR=/sources/stage/perl install
mkdir -p /sources/stage/perl/usr/share/doc/perl
cat Artistic Copying > /sources/stage/perl/usr/share/doc/perl/copyright
