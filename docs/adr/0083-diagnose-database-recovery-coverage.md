# ADR-0083: Measure database log coverage independently of the summary filter

- Date: 2026-11-07
- Status: Diagnostic implementation; complete-suite acceptance remains pending
- Extends: ADR-0069 and ADR-0079

## Problem and decision

The original complete Berkeley DB 5.3.28 run ended with recipe/driver exit 1
and zero installed changes. Its strict output summary contains 25 unexpected
lines: two real repmgr failures already diagnosed, thirteen copies of a Test142
informational message, and ten recovery log-record coverage warnings. The
prepared handoff correctly rejected this additional output. It remains closed.

The actual native Tcl check_output procedure rejects the extra space after the
Test142.b message's initial tab. A disposable four-control probe shows that
removing only that space satisfies the unchanged checker, while deliberately
injected FAIL and missing-coverage lines still fail. Original and corrected
source hashes match; the active corrected log already contains this message.
Its full assertions must still finish, but waiting alone cannot fix the strict
summary. Preserve all raw output and actual exits. Do not edit active inputs.

Frozen logtrack.tcl:112-117 compares its recorded log types with logtrack.list.
Frozen test.tcl:1856-1921 initializes/summarizes this tracking only around
run_recds. testutils.tcl:1446 and 1714 collect inside the recovery helpers.
Access-method tests such as test140 also perform real recovery, but are outside
that coverage collection. This identifies a possible coverage-accounting gap;
it does not itself prove that each missing record is exercised or correct.

Add a bounded native diagnostic in a fresh isolated copy of the existing
verified compiled inputs. Use unmodified frozen test bodies, a separate
standard-regression.tcl diagnostic entry, native db_printlog and an execution
trace immediately before env_cleanup. The trace reads real logs before the
normal test cleanup removes them. It never changes assertion code, adds a
record to Berkeley's tracker or substitutes synthetic records. Empty log
formatting headers are not record names; collect actual __symbol identifiers.

Run original test140 hash recovery, sdb013 named-memory transactions, test112
with its full 80,000-entry deep-tree workload, and test111 with its default
10,000-entry hash workload. The latter two use explicit transactional
40,000-lock/20,000-object environments (the capacities used by frozen run_recd)
and a 64 MiB cache. Compare actual database dumps across native db_recover.
An additional named-memory case checks committed/aborted rename and removal,
then actual recovery/reopen data. Require evidence of all ten reported types;
missing coverage remains failure. Passing this diagnostic does not accept the
complete standard suite, Berkeley package or H07.

The launcher copies only hash-matching entries from the 10,208-input manifest,
changes only the diagnostic entry, and retains frozen Tcl bodies and compiled
checkpoint bytes. It uses the already exercised private mount/IPC/network/PID
namespace and tmpfs setup. A detached driver captures actual process exits,
checks source/harness hashes before and after, and retains result/logs with an
1800-second outer timeout and 60-second kill grace. The complete corrected run
remains isolated and untouched. No production installation is present.

Alternatives rejected: silently allowing every warning hides future defects;
restarting the same full suite cannot repair a deterministic formatting issue;
changing the live run loses its input provenance. A small real diagnostic
provides evidence for the next correction while the complete run finishes.
No final-result qualification or acceptance-gate exception is introduced here.

## Diagnostic corrections and preserved failures

The initial private harness used Tcl's reserved global env array as a scalar.
Corrected the local diagnostic handle name. Next, native deep-tree insertion
exhausted the default environment's lock table; used the frozen recovery
harness's explicit capacities. Compaction then exhausted the small default
buffer cache; sized this private workload to 64 MiB, within the measured guest
resources. These were diagnostic environment defects, not changed library
versions or suppressed test assertions. The earlier three exit-1 results and
unchanged-input reports are retained; combined evidence SHA-256:
a252684cce44c41c81c55d6ed503fcc094ae9a121aeabaac24d02ec1f65f6d2c
(.local/logs/h07-db-coverage-initial-failures.json).

The next diagnostic passed deep-tree compaction and disk-database recovery,
but named-memory reopen failed after the standalone recovery utility exited.
Frozen util/db_recover.c:147 selects DB_PRIVATE unless retain_env is requested;
its native manual documents -e to retain the recovered environment. Use -e for
this named-memory shared-cache check, preserving the data comparison. The
ordinary disk-backed comparisons keep their original recovery mode. This is a
correction of the diagnostic invocation, not removal of a failing assertion.
The failed fixture db-standard-coverage-yz3majrp remains preserved with exit 1.

Sources: frozen Berkeley 5.3.28 test/tcl/test.tcl, testutils.tcl, logtrack.tcl,
test112.tcl, test111.tcl, test140.tcl, sdb013.tcl, sdb017.tcl;
util/db_recover.c and docs/api_reference/C/db_recover.html. The
[Oracle recovery utility manual](https://docs.oracle.com/cd/E17076_04/html/api_reference/C/db_recover.html)
currently serves version 12.1.6.1 and also documents the retained-environment option. The exact frozen source and
actual native behavior define this experiment, not a newer library release.

Reproduce by running `python3 scripts/host/probe_bdb_recovery_coverage.py` only
after inspecting any existing diagnostic. It prints a new private fixture and
PID. Inspect that fixture's driver.log, running.json, result.json, test.exit and
driver.exit; actual terminal output is required. Do not infer success from the
launcher exit or run another copy while the existing diagnostic is active.

The first hash-extension invocation tried to dump test111.db after the original
test had advanced to its final -revsplitoff subcase. Frozen test111 cleans the
earlier file and leaves test111.rev.db; use that actual final database for the
extra recovery comparison. The upstream test already compares both subcases.
Keep the missing-file failure and correct the invocation, without skipping the
recovery or comparison. Its diagnostic output already recorded all ten target
log types, but the failed overall result is not accepted.

## Completed native diagnostic

The final fixture db-standard-coverage-0_05jaht ran from 09:27:49 to 09:28:45 UTC.
Actual test and driver exits are both zero. CuTest and all diagnostic cases
passed, including byte-identical pre/post-recovery disk dumps and the actual
named-memory recovery/reopen comparison with -e. Every input hash remained
unchanged; a separate collection rechecked terminal exits, reports and all
source inputs. No active corrected-suite input or installed package was changed.

All ten target types were observed in real native db_printlog output:

| Log record | Captured observations |
| --- | ---: |
| __bam_irep | 3616 |
| __crdel_inmem_create | 23 |
| __crdel_inmem_remove | 22 |
| __crdel_inmem_rename | 28 |
| __db_merge | 32844 |
| __db_pg_trunc | 96 |
| __db_pgno | 4144 |
| __db_realloc | 40 |
| __ham_changeslot | 40 |
| __ham_contract | 2566 |

These are observations across multiple scans, not unique records or distinct
assertions. Type presence is the measured coverage property. The original
library behavior and test assertions remain intact. This establishes that the
limited run_recds tracker omits types exercised by the separate native workloads;
it is not proof of exhaustive database correctness or full-suite acceptance.

- Captured result SHA-256: b2730bcd16ec81fb3d228c20afdeef5dd32d4f0fd9b7091416f1a273e5afd5af
- Guest result.json SHA-256: 25346654d8a206d28fe1a239247a0a730a119b2ef6493299ce0a017960119edf
- Input manifest SHA-256: 042c63826149c3b1bf647152b7c2140ab0c7e730327fb36ff0491cae74df59e7
- Diagnostic Tcl SHA-256: 8e7fe113e00e113c9537705df36ca46af7a6dc5955af5354b6302ffead0879f0
- Driver SHA-256: 9b780466c8dc3b2175fb5e85c100d47dce273f1fc04fb780edd91b25bbb9988e
- Native diagnostic log SHA-256: 171a44007a38110fd8353783f309d32397dad79ea259d009c8e418af5994b0cb
- Record observations SHA-256: 76f89b5413fb96ea9ca7ad1323360961afb40f8e5b7d58293f0f2d962b938b41

Collect the existing fixture without relaunching:

```sh
python3 scripts/host/probe_bdb_recovery_coverage.py --collect \
  /mnt/lfs/sources/recovery/db-standard-coverage-0_05jaht
```

The result is explicitly suite_accepted=false and package_accepted=false. The
complete corrected run remains live. Its actual complete assertions, exact
terminal diagnostics and any subsequently reviewed result qualification still
need independent acceptance review; production and APT remain gated.
