#!/bin/bash
set -euo pipefail
cd /sources/db-5.3.28
test ! -e /sources/stage/berkeley-db
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
