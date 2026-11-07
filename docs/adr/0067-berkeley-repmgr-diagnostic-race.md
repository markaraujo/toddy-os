# ADR-0067: Wait for the asynchronous repmgr007 diagnostic

- Date: 2026-11-07
- Status: Native focused correction passed; complete suite remains failed/pending
- Scope: Test fixture timing only; no C/runtime source or assertion removed

At 00:42 UTC the ongoing Berkeley DB standard suite reached other_repmgr and
failed repmgr007's final unexpected-input diagnostic assertion. Restarted clients
and all three transaction/data checks had passed. The test writes invalid bytes
to the master's TCP port, closes the socket and immediately reads the error log.
The replication manager processes that socket in another thread, so close does
not guarantee that its diagnostic has already reached the file.

A private copy of the verified native test build reproduced the original
assertion failure. Reading the same diagnostic file 200 ms after the failure
found the expected BDB3676 message, and all subsequent delayed reads found it.
This is measured timing evidence; it does not excuse missing diagnostics or a
replication data mismatch. The original active source tree and running standard
suite were not modified.

The correction rereads the file with a bounded twenty-iteration, one-second wait
using the existing tclsleep helper. It exits the wait when the expected text is
present, then runs the original error_check_good assertion unchanged. If the
message never arrives, the same assertion still fails. The file is closed as
before, followed by all original environment-close assertions. A fixed arbitrary
sleep is less robust; suppressing the assertion or swallowing the failure is
unacceptable. No upstream acknowledgement is claimed.

Patch db-5.3.28-repmgr007-async-diagnostic-1.patch is 653 bytes, SHA-256
7e5bccd45146a7bc3230da2595207bd0c2919a5e565a26eade8aba0b64ba54df.
Preimage d036980f70aacba44c2dc6eab9ac4808fcbb2b5914933cf8bb12279a96f08f0f;
postimage f3ec292bdd03ea1066c683bde617ed27288c16c814a6eecd3a0cddd5a580fd44.
Retain the upstream copyright/license header and apply with fuzz zero after
hash verification. Source is frozen 5.3.28 test/tcl/repmgr007.tcl; existing
reputils.tcl uses bounded waits for asynchronous replication conditions too.
Freeze the published patch URL and integrate fresh/recovery preflight only at
the next quiescent build-input boundary; it is not installed in the active run.

Native original reproduction exited 12 with the captured assertion and delayed
diagnostic, log SHA-256
0fc79fb40748b3ca4b49275fdc9dbc32e87f070b057432020a3f77fc3c415bef.
The corrected test passed three complete repetitions in a private network
namespace with loopback enabled, using the same source-built library and tools.
Captured exit 0, log SHA-256
1c5a5916d16b91896ef3ebe578c1ffa70f3e1148b79138a684b2ddd32565fd59.
The versioned focused script is
scripts/build/h07/berkeley-db-repmgr007-regression.tcl. It does not substitute
for full group/suite acceptance. The initial private-copy probe counted only
479 .tcl files rather than all 483 frozen test-directory files; it refused
before execution. The corrected comparison includes the four non-Tcl inputs.

## Separate missing test-program dependency

The next group, multi_repmgr, independently failed at repmgr100 because
db_repsite is absent. A private test build with C++ enabled and explicit
make -j2 all cutest db_repsite confirmed that its required source file
test/repmgr/db_repsite.cpp is absent, not merely an unbuilt executable. That
experiment exited 2; log SHA-256
efa0aeaf6eb918aea1cf344bffd28ca176a734b1f3d8e1022ad0687ee2e0b46b.
The production C-only package profile has not changed.

The frozen maintained source archive has no test/repmgr subtree. The complete
9,579-entry upstream v5.3.28 tree at commit
e66a5e66d5a8db89d13532012f28d17d375e8564 also lacks it. Raw tree response
.local/references/bdb-5.3.28-upstream-tree.json SHA-256
13a19307e54e4e4bd5a93d23731e403c80ad584f7ade64d7fc04a56ffb29ed3a.
See the [versioned upstream tree](https://github.com/berkeleydb/libdb/tree/e66a5e66d5a8db89d13532012f28d17d375e8564/test).
The [Gentoo 5.3.28 recipe](https://raw.githubusercontent.com/gentoo/gentoo/e93bffad510cb98f11fb9a1e49051b0e7d1fe89f/sys-libs/db/db-5.3.28-r2.ebuild)
independently documents stripped upstream helper sources and removes this group.
That removal is not adopted here. Changing C++ flags alone cannot restore absent
sources, so do not repeat that failed build as an unblocking attempt.

Keep the eleven original multi-process test cases and their real database/
replication assertions. Resolving their actual helper dependency remains open;
an implementation must perform real native operations, never synthesize success
or replace the tests with mocks. No source-availability exception or skipped
group has been accepted. Do not restart the same complete suite before resolving
this prerequisite and checking the other_repmgr group with the timing correction.

## Recovery and acceptance boundary

All native experiments are preserved under
/mnt/lfs/tmp/toddy-repmgr-diagnosis-w59p805n. The failed first copy is separately
preserved at toddy-repmgr-diagnosis-4axxv1n6. Consolidated experiment results
.local/logs/h07-repmgr-diagnosis-results.json SHA-256
509f747f11842fc76a2c528d05bcb64092d1ce5ccfdcb5436a465d7f21f16192.
Initial standard failures .local/logs/h07-repmgr-failures.json SHA-256
61667172f909a12cce1c6de361611abbc33642b1907b99c9850deba9f6141304.
The latter is a partial observation, not a final full-suite log.

The original driver remains active collecting later replication tests. Its
success-gated supervisor must not start APT after a failed result. Preserve
the complete terminal output and installed-state audit when it ends. A separate
bounded private run of all twenty other_repmgr tests is now collecting results;
inspect its actual exit file before any acceptance claim. H07 remains at 124
accepted packages, with Berkeley DB/APT and final closure unaccepted.


## Frozen correction and recovery preflight

The correction is now pinned in supplemental-sources.lock.json to immutable
project commit 4b8fc31e89ab4d3897cf4df12ba26b659808e5ca. A fresh HTTPS download
matched the recorded 653-byte patch and its SHA-256. The apply/reference scripts
cover both reviewed fixture corrections, with exact preimage/postimage hashes.
Fresh/recovery paths remain gated on the full standard suite; these changes are
not synchronized into the still-running original attempt.

python3 scripts/host/probe_db_test_fixtures.py extracts the frozen Tcl inputs to
a private host directory, applies the maintained patch and both corrections,
compares all 483 files against an independently generated reference, and checks
idempotence. Six negative checks reject changed source, changed patch bytes and
redirected fixtures for both corrections without altering the rejected input.
Raw .local/logs/h07-db-fixture-preflight.json SHA-256:
094224aac25163c8cf5020657b3bd9c9bd7451355032fff6795b49ddc9f5f51f.
The same 483 expected hashes matched the running private native test fixture.
This validates input handling, not a replacement for native regression tests.

Source-notice enumeration now covers 157 frozen inputs and 891 notice candidates;
new inventory SHA-256
0937212b5d73a90505b58ea34fed170d23d819ff30a6d2c831c46289708cdd26.
The added patch is not a new installed package or a complete license review.
ADR-0068 records the separately resolved native helper and its eleven passing
multiprocess cases. The complete twenty-case other_repmgr result remains pending.
