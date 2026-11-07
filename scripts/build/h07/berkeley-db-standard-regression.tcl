# Complete upstream standard suite, with the same acceptance as the native recipe.
# This file never installs a library or grants package/milestone acceptance.
if {[catch {source ../test/tcl/test.tcl; run_std} problem options]} {
 puts stderr [dict get $options -errorinfo]
 exit 1
}
set fd [open ALL.OUT r]
set report [read $fd]
close $fd
if {![regexp -line {^Regression Tests Succeeded$} $report] ||
    [regexp -line {^FAIL|^Regression Tests Failed$} $report]} {
 puts stderr "Complete DB regression summary failed"
 exit 1
}
puts "Complete native DB standard regression suite accepted"
