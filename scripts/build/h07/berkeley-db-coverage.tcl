# Diagnostic coverage experiment, not run_std or package acceptance.
# Frozen test bodies remain unchanged. Observe logs before their normal cleanup.
source ../test/tcl/test.tcl
set coverage_records [dict create]
set coverage_reads 0
proc coverage_read {dir} {
    global util_path coverage_records coverage_reads
    if {[llength [glob -nocomplain $dir/log.*]] == 0} {return}
    set path coverage-printlog.tmp
    exec $util_path/db_printlog -N -h $dir > $path
    set fd [open $path r]
    while {[gets $fd line] >= 0} {
        if {[regexp {\[[^\]]*\]\[[^\]]*\](__[A-Za-z0-9_]+)\:} $line all name]} {
            dict incr coverage_records $name
        }
    }
    close $fd
    file delete $path
    incr coverage_reads
}
proc coverage_before_cleanup {command operation} {
    coverage_read [lindex $command 1]
}
proc coverage_named_memory {} {
    global testdir util_path
    # Uses the same named-memory API as frozen sdb013/sdb017, with explicit
    # transactions and a real recovery/reopen comparison after committed rename.
    env_cleanup $testdir
    set handle [berkdb_env_noerr -create -txn -home $testdir -mode 0644]
    set db [berkdb_open_noerr -create -btree -env $handle -auto_commit "" before]
    set txn [$handle txn]
    error_check_good coverage_put [$db put -txn $txn key value] 0
    error_check_good coverage_commit [$txn commit] 0
    error_check_good coverage_close [$db close] 0
    foreach ending {abort commit} {
        set txn [$handle txn]
        error_check_good coverage_rename [berkdb dbrename -env $handle -txn $txn "" before after] 0
        error_check_good coverage_end [$txn $ending] 0
        set name [expr {$ending eq "abort" ? "before" : "after"}]
        set db [berkdb_open_noerr -btree -env $handle -auto_commit "" $name]
        error_check_good coverage_read_value [$db get key] {{key value}}
        error_check_good coverage_close [$db close] 0
    }
    error_check_good coverage_env_close [$handle close] 0
    coverage_read $testdir
    # db_recover defaults to DB_PRIVATE; -e preserves the recovered shared
    # environment and its named-memory cache for the subsequent process.
    exec $util_path/db_recover -e -h $testdir
    set handle [berkdb_env_noerr -create -txn -home $testdir -mode 0644]
    set db [berkdb_open_noerr -btree -env $handle -auto_commit "" after]
    error_check_good coverage_recovered_value [$db get key] {{key value}}
    error_check_good coverage_close [$db close] 0
    foreach ending {abort commit} {
        set txn [$handle txn]
        error_check_good coverage_remove [berkdb dbremove -env $handle -txn $txn "" after] 0
        error_check_good coverage_end [$txn $ending] 0
        set ret [catch {berkdb_open_noerr -btree -env $handle -auto_commit "" after} db]
        if {$ending eq "abort"} {
            error_check_good coverage_remove_abort $ret 0
            error_check_good coverage_retained_value [$db get key] {{key value}}
            error_check_good coverage_close [$db close] 0
        } else {
            error_check_bad coverage_remove_commit $ret 0
        }
    }
    error_check_good coverage_env_close [$handle close] 0
    coverage_read $testdir
    env_cleanup $testdir
}
trace add execution env_cleanup enter coverage_before_cleanup
set coverage_status 0

if {[catch {
    # This original test includes commit/abort, real db_recover, and exact
    # before/after database comparisons. Its final cleanup would lose the logs.
    puts "COVERAGE_CASE test140 hash full default parameters"
    test140 -hash
    puts "COVERAGE_CASE sdb013 btree full default parameters"
    sdb013 -btree
    coverage_read $testdir
    env_cleanup $testdir
    # Exercise original deep-tree compaction in an actual transactional env.
    puts "COVERAGE_CASE test112 btree 80000 transactional"
    # Match run_recd's frozen compaction environment capacity (test.tcl:1712).
    set coverage_env [berkdb_env_noerr -create -txn -home $testdir -mode 0644 \
        -lock_max_locks 40000 -lock_max_objects 20000 -cachesize {0 67108864 1}]
    error_check_good coverage_env [is_valid_env $coverage_env] TRUE
    test112 -btree 80000 112 -env $coverage_env
    error_check_good coverage_close [$coverage_env close] 0
    coverage_read $testdir
    puts "COVERAGE_CASE test112 real recovery and byte comparison"
    exec $util_path/db_dump -h $testdir test112.db > coverage-before.dump
    exec $util_path/db_recover -h $testdir
    exec $util_path/db_dump -h $testdir test112.db > coverage-after.dump
    error_check_good coverage_recovery_compare [filecmp coverage-before.dump coverage-after.dump] 0
    env_cleanup $testdir
    puts "COVERAGE_CASE test111 hash 10000 transactional"
    set coverage_env [berkdb_env_noerr -create -txn -home $testdir -mode 0644 \
        -lock_max_locks 40000 -lock_max_objects 20000 -cachesize {0 67108864 1}]
    test111 -hash 10000 111 -env $coverage_env
    error_check_good coverage_close [$coverage_env close] 0
    coverage_read $testdir
    # test111's final original subcase is -revsplitoff; it removes the earlier
    # test111.db while starting this subcase and leaves test111.rev.db.
    exec $util_path/db_dump -h $testdir test111.rev.db > coverage-before.dump
    exec $util_path/db_recover -h $testdir
    exec $util_path/db_dump -h $testdir test111.rev.db > coverage-after.dump
    error_check_good coverage_hash_recovery_compare [filecmp coverage-before.dump coverage-after.dump] 0
    env_cleanup $testdir
    puts "COVERAGE_CASE transactional named-memory rename and recovery"
    coverage_named_memory
    foreach name {__bam_irep __crdel_inmem_create __crdel_inmem_remove
        __crdel_inmem_rename __db_merge __db_pg_trunc __db_pgno __db_realloc
        __ham_changeslot __ham_contract} {
        error_check_good coverage_seen_$name [dict exists $coverage_records $name] 1
    }
} error options]} {
    puts stderr [dict get $options -errorinfo]
    set coverage_status 1
}
trace remove execution env_cleanup enter coverage_before_cleanup
set fd [open coverage-records.txt w]
foreach name [lsort [dict keys $coverage_records]] {
    puts $fd "$name [dict get $coverage_records $name]"
}
close $fd
puts "COVERAGE_READS $coverage_reads"
if {$coverage_status != 0} {exit $coverage_status}
puts "Diagnostic native coverage cases completed; full suite and package remain unaccepted"
