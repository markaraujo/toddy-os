# Run from a private native build-test directory after the reviewed fixture patch.
# This focused result never substitutes for complete standard-suite acceptance.
if {[catch {
 source ../test/tcl/test.tcl
 foreach iteration {1 2 3} {
  puts "CORRECTED_REPMGR007_BEGIN $iteration"
  repmgr007
  puts "CORRECTED_REPMGR007_PASSED $iteration"
 }
 env_cleanup $testdir
 puts "ALL_CORRECTED_REPMGR007_PASSED"
} problem options]} {
 puts stderr [dict get $options -errorinfo]
 exit 1
}
