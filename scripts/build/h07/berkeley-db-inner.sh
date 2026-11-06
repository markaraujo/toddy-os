#!/bin/bash
# Maintained frozen source/patch series; no Debian build or maintainer script runs.
set -euo pipefail
cd /sources/db-5.3.28
test ! -e /sources/stage/berkeley-db
mkdir -p /sources/evidence/h07-berkeley-db
while IFS= read -r patchname; do
 [[ -z $patchname || $patchname == \#* ]] && continue
 [[ $patchname != */* ]]
 patch --batch --forward --fuzz=0 -p1 -i "debian/patches/$patchname"
done < debian/patches/series
(
 cd dist
 libtoolize --copy --force --install
 ./s_config
 test -s config.hin && test -x configure
 sh -n configure
) 2>&1 | tee /sources/evidence/h07-berkeley-db/regenerate.log
mkdir build-test build-production
cd build-test
CFLAGS='-O2 -std=gnu17' ../dist/configure --prefix=/usr --libdir=/usr/lib \
 --sysconfdir=/etc --localstatedir=/var --enable-static --disable-cxx \
 --enable-compat185 --enable-dbm --disable-java --disable-sql --disable-stl \
 --with-mutex=POSIX/pthreads/library --enable-tcl --with-tcl=/usr/lib --enable-test
make
make cutest
cd ..
chown -R tester:tester .
su tester -c 'cd build-test && ./cutest' 2>&1 | tee /sources/evidence/h07-berkeley-db/cutest.log
