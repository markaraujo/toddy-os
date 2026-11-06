# ADR-0043: Correct Berkeley DB test142 environment isolation

- Date: 2026-11-06
- Status: Native focused correction passed; full standard rerun/install pending

The unchanged 5.3.28 maintained-source standard suite fails test142 during range
partition tests: BDB1540 configured environment flags incompatible with existing
environment. test139 creates/closes a nontransactional environment and leaves
its region files; test142 opens a transactional environment before its cleanup.
Library src/env/env_region.c deliberately rejects adding incompatible subsystems
to an existing environment. This is a measured fixture-state leak, not a reason
to ignore the failure or claim the complete suite passed.

A separate TESTDIR using the same compiled native test library reproduces the
original test139-to-test142 error. Prior environment cleanup lets unchanged
exclusive-handle assertions complete. The correction places env_cleanup in the
branch where test142 creates its own environment, before that open. Externally
supplied environments retain their intended handling. No assertion, expected
result, test selection or C/runtime source changes. Preserve original license
header. Do not disable Thread, skip the test or qualify this as an accepted fail.
Global per-test cleanup would change unrelated fixtures; the local own-environment
correction is narrower. No upstream bug acknowledgement is claimed.

Focused corrected plain/range/callback cases each run original test139 followed
by corrected test142 without caller cleanup between them; all pass, captured
exit 0. Raw .local/logs/h07-bdb-test142-corrected.log SHA-256
94e0e6186890f5f50fe33004fe5c662eafacd7607a69354dfa11bde0203a8485. A preliminary sentinel-only probe is separate
and is not substituted for the exit-captured result. The versioned regression
script repeats these cases before the complete standard suite and leaves an
empty TESTDIR for its initial state.

Patch db-5.3.28-test142-environment-1.patch SHA-256
c624d2855e08cf3c214edec5e8c33eb387c8354398a4844139a409ef93f7669c,
362 bytes, immutable project commit db25caa6eaa344cef555fd5a46961f5a638dba5d.
Fixture preimage 033f9b71ac70bab8723f13aa4b3467dbf815b76b593bc37123edcfaa39bf9ef9;
postimage 3cacea1ce719d20e585e74d40a7f5b3cc07671f32f78c52aa64aea3c269ac28b.
Verify patch/preimage/postimage and use fuzz zero. Source versions and the 19
maintained patches remain frozen. Patch is test-only; no upstream signature claim.

The already-failed attempt was stopped through verified PGID 426446. Runner
recipe -15, postcheck null, zero installed changes; no production build started.
Full partial evidence and cancellation reason remain in builder history
berkeley-db-test142-20261106T161146Z. Reuse only the root-protected hash-verified
460-file native test-build checkpoint (C source/configuration, utilities/shared
objects), seed SHA-256
75d8c0e77db2c0b42af7de2ff813e908ee4f2d5cc470dcb62bb5082013937e63.
This is a recovery ingredient, not package acceptance. Archive dirty TESTDIR and
original logs, verify frozen archives/build hashes, apply the fixture correction,
repeat C tests, focused regression and the complete standard suite. Production
build, native package installation and transaction/reopen postchecks follow only
actual success. Fresh builds take the same patch and original test scope.

Independent Perl/Triehash/Which/Libseccomp/Tcsh work may finish first. APT still
requires accepted Berkeley DB. H07/G1 remain incomplete; no failed test is removed
or turned into success by this decision. Sources are exact frozen test139.tcl,
test142.tcl, test.tcl/testutils.tcl and src/env/env_region.c, plus measured native
logs; this is a project correction derived from those sources.

Recovery now also checks the fixed recovery-seed digest, root ownership and
private permissions. Before running Tcl, compare all 483 frozen test/tcl files
with an independent extraction plus maintained 004-tclsleep.patch and the
reviewed test142 patch. Refuse unexpected Tcl scripts. The pre-patch read-only
probe correctly refuses original test142 (preimage hash above); it is not a
corrected-suite acceptance. The recovery sequence applies the exact correction
before this comparison. Raw refusal log .local/logs/
h07-bdb-tcl-frozen-files-probe.log SHA-256
fc3738633be4dfa4814c5a7dd963450f7c0e3d2cf95f192d0b022a462ac9f660.

Actual retry passed fixed-seed verification, all 483 independent Tcl file
comparisons, repeated C tests and all three focused cases before starting the
complete standard suite at 17:12 UTC. The complete result remains unfinished;
there is still no DB installation or acceptance claim.
