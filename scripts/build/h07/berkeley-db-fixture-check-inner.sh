#!/bin/bash
# Regression for the measured test139/test142 state leak; retain all assertions.
set -euo pipefail
cd /sources/db-5.3.28
su tester -c 'cd build-test && tclsh' <<'TCL' 2>&1 | tee /sources/evidence/h07-berkeley-db/test142-regression.log
if {[catch {
 source ../test/tcl/test.tcl
 foreach {label options} [list plain {} range [list -partition {ab cd key key1 zzz}] callback [list -partition_callback 5 part]] {
  env_cleanup $testdir
  puts "REGRESSION $label: test139 then test142, no intervening caller cleanup"
  eval [linsert $options 0 test139 btree 512 1000 139]
  eval [linsert $options 0 test142 btree 142]
  puts "REGRESSION_PASSED $label"
 }
 env_cleanup $testdir
 puts "ALL_TEST142_REGRESSIONS_PASSED"
} error options]} {
 puts stderr [dict get $options -errorinfo]
 exit 1
}
TCL
