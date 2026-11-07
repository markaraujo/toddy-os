# Run from the native test build with the test-only db_repsite adapter.
# Keep every upstream multi_repmgr case and its assertions unchanged.
# This focused check does not replace the complete standard suite.
if {[catch {
 source ../test/tcl/test.tcl
 run_subsystem multi_repmgr 1 1
 puts "ALL_MULTI_REPMGR_PASSED"
} problem options]} {
 puts stderr [dict get $options -errorinfo]
 exit 1
}
