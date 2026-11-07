# ADR-0079: Determine database progress from the outer dispatcher

- Date: 2026-11-07
- Status: Reporting defect corrected against actual live logs

The 07:59–08:30 UTC reports incorrectly placed both Berkeley DB runs in the
final access-method matrix. Only the original run had reached that group.
The corrected complete rerun was still in partition (18/27), then compression
(19/27). The raw Test044/Test142 case observations were real, but those names
repeat inside multiple groups. Inferring the outer group from them overstated
progress. This is an implementation defect in monitoring/reporting, not a
database test failure or evidence of an infinite loop. Correct the public
snapshot and annotate the historical narrative; preserve raw evidence.

Read each run's own standard.log, whose `Running ...` lines are emitted directly
by the frozen run_std dispatcher. Keep ALL.OUT only for detailed case/parameter,
failure and crash/recovery information. Verify actual PID command identity and
start ticks, and read terminal exit files separately. Neither a detailed case
number, another run's progress nor a quiet parent log establishes completion.

The source-qualified observer verifies both input hashes before classification:

- db-5.3.28 test/tcl/test.tcl:
  81b82f33c9ca4fc878ee51fd1f235645824f1d4faba28d187bc23955c21681df.
- Actual build-test/db_config.h:
  12a33fcd1ac46b1296fd1916e6a1cb588dc35432d93adffea661188b0e07e941.

The exact compiled profile enables crypto, queue, hash and heap. Its run_std
sequence contains 24 initial groups, recovery, join and the access-method
matrix: 27 logical groups. The final group emits nine method headings, giving
35 outer headings overall. The observer validates the complete observed header
prefix and refuses unknown, missing, duplicated or out-of-order sequences.
It reports final-method position separately from the logical group, plus the
remaining logical groups. A group that returned may contain recorded failures;
it is not automatically passed. No time/effort percentage is calculated.

Read the outer log before and after scanning ALL.OUT and explicitly flag a
group transition during the observation. Preserve the full outer log snapshot
and its digest in content-addressed local evidence. Observation is read-only:
do not invoke run_std -n in either active source tree, since even that option
removes/recreates ALL.OUT. Do not execute or modify a test to estimate progress.

Actual 08:36:33 UTC verification:

| Run | Actual outer group | Detailed observation | Failures so far |
| --- | --- | --- | --- |
| Original, PID 1364 | 27/27, matrix method 8/9: hash | Test044, cycle 1 | Same two known failures |
| Corrected, PID 1107192 | 19/27: compression | Test076 btree with -compress | Zero FAIL entries |

Both actual process identities were live; neither terminal exit existed.
Complete raw observation SHA-256:
0ffd396f79afaea39598e11cee701e5b31af7fa6fcf28d5f3fee61742c49787b.
The corrected run still needs the remainder of compression, three replication
manager groups, replication, security, recovery, join and the complete final
matrix. Focused earlier corrections do not replace these complete-run groups.
The original run's later position cannot be transferred to the corrected run.

Four regression tests cover repeated Test044 names in groups 18/19/27, all nine
final-method positions, missing/unknown/duplicate/out-of-order headers and the
actual post-compression group list. The same observer passed against both real
live runs. Keep suite/package acceptance in the existing strict terminal and
production postcheck verifiers; this observer grants no success marker.

Reproduction:
`python3 scripts/host/observe_bdb.py --corrected-fixture /mnt/lfs/sources/recovery/db-standard-nfv62s4o`.
Supply the actual printed fixture for later runs. The legacy local observation
shortcut now delegates to this versioned command, preventing reuse of the old
case-only report. H07 remains 124/126 accepted packages and 38% foundation credit.

## Replication detail labels — 2026-11-07 09:03 UTC

The outer group was correctly reported as 20/21, but the configuration field
recognized only Recd/Fop/Test prefixes and could retain the earlier Test142
compression description. Extend detail parsing to the actual numbered suite
labels and Basic repmgr substeps/reproduction commands. These details never
determine the group, pass state or time estimate. Two regressions cover stale
configuration replacement, automated replication steps, failure preservation
and the bounded tail. All six observer regressions pass.

Actual source-qualified observation now reports original 27/hash, Test097,
and corrected 21/other repmgr, Repmgr025.h. Both identities remain live; no
terminal exits exist, original retains two failures and corrected has none.
Raw observation SHA-256:
db25c36e4e06c63e292f20a84a47c56f21b13e0607fea48dca8c6adc8f9e19a8.
Only the read-only observer changed; no active test input or acceptance changed.
