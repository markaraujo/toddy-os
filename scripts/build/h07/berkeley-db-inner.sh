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
su tester -c 'cd build-test && tclsh' <<'TCL' 2>&1 | tee /sources/evidence/h07-berkeley-db/standard.log
if {[catch {source ../test/tcl/test.tcl; run_std} error options]} {
 puts stderr [dict get $options -errorinfo]
 exit 1
}
set fd [open ALL.OUT r]
set report [read $fd]
close $fd
if {![regexp -line {^Regression Tests Succeeded$} $report] || [regexp -line {^FAIL|^Regression Tests Failed$} $report]} {
 puts stderr "Complete DB regression summary failed"
 exit 1
}
puts "Complete native DB standard regression suite accepted"
TCL
cp build-test/ALL.OUT /sources/evidence/h07-berkeley-db/
cd build-production
CFLAGS='-O2 -std=gnu17' ../dist/configure --prefix=/usr --libdir=/usr/lib \
 --sysconfdir=/etc --localstatedir=/var --enable-static --disable-cxx \
 --disable-compat185 --disable-dbm --disable-java --disable-sql --disable-stl \
 --with-mutex=POSIX/pthreads/library --disable-tcl --disable-test
make
make DESTDIR=/sources/stage/berkeley-db install
# Static objects are required by the maintained symbol-version generator only.
find /sources/stage/berkeley-db/usr/lib -maxdepth 1 -type f \( -name "*.a" -o -name "*.la" \) -delete
! grep -E '^#define CONFIG_TEST 1' db_config.h
cd ..
mkdir -p /sources/stage/berkeley-db/usr/share/doc/berkeley-db
cat LICENSE debian/copyright > /sources/stage/berkeley-db/usr/share/doc/berkeley-db/copyright
