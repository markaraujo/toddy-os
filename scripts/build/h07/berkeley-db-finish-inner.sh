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
