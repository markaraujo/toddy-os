# ADR-0087: Prepare an exact complete-run diagnostic qualification

- Date: 2026-11-07
- Status: Prepared; native refusal/record checks passed, complete positive result pending
- Extends: ADR-0083, ADR-0084 and ADR-0086

## Decision and acceptance boundary

PRD section 5 permits an identified, justified upstream test failure. ADR-0083
measured two diagnostic defects: thirteen informational Test142 messages whose
spacing confuses the output checker, and ten recovery log warnings whose record
types were exercised by the separate native coverage witness. This does not
permit ignoring an assertion, unknown message, changed multiplicity or missing
part of run_std. The complete corrected run is still executing.

Prepare scripts/build/db_standard_qualify.py as a separate terminal decision.
It first requires the complete independent native review, actual raw exits 1/1,
all 35 ordered outer headers, unchanged verified execution/source/report bytes,
zero actual FAIL entries, zero unclassified diagnostics and exactly the known
23 diagnostic lines. It also requires the actual protected native witness from
ADR-0086. No new output category or generic warning waiver is introduced.

After that review, protect the full source using the same custody operation
already exercised on the completed coverage source, then repeat the native
review. Record a separate standard-qualification.json with the full original
review, native checker output, stable evidence hashes and source-custody hash.
Both raw process exits remain 1 and the original summary remains Regression
Tests Failed. The decision is explicitly standard_suite_qualified, not an
invented standard_suite_passed producer field. package_accepted stays false.

The read-only verifier rechecks native reports, reruns the independent frozen
checker, revalidates protected coverage and compares actual source metadata with
the custody receipt. Private checker command paths and their path-dependent
script hashes may differ on independent reruns; original command provenance is
retained in the recorded review, while checker output, body, source and result
hashes must match. Rewritten outcomes, changed witness/custody, missing output,
real assertions and unknown diagnostics remain errors.

The production handoff has not changed: it still calls strict verify_completed.
Do not wire this prepared path into production until the actual complete
positive qualification has been inspected and verified. No qualification,
source-custody intent or production candidate has been created for the running
full suite. Fresh-build namespace/diagnostic handling remains implementation
work; this recovery-specific decision is not a portable replacement for tests.

Alternatives rejected: changing a live test input would invalidate the run;
rewriting exits or removing diagnostics would misstate evidence; treating a
focused success as the full suite would omit required execution; accepting
arbitrary warnings would weaken the gate. A separate source-bound decision
preserves the actual result and the complete-run obligation.

## Atomic records and recovery

The shared custody writer now creates/fsyncs a private temporary record, publishes
it with an exclusive same-filesystem hardlink and fsyncs the parent directory.
It never overwrites an earlier record or exposes partially written JSON under
the final name. A crash before publication may leave a private .pending-* file;
that name is never an accepted receipt. Existing completed records are verified
instead of regenerated. Source-custody intent/recovery semantics are unchanged.

Qualification interrupted after source sealing can repeat the complete review
and reuse the same verified custody receipt. Changed source identity or bytes
must still refuse. Preserve raw results and pending/failed evidence; do not
rerun the hours-long suite merely to recover a lost observation.

## Actual verification so far

The native probe confirmed the specific full driver was live. Qualification and
qualification verification refused it; trying to use the completed coverage run
as the full suite also refused. Full source ownership/modes remained unchanged,
and no full custody/qualification file or complete-review directory was created.
The refactored shared custody path reverified the actual coverage receipt with
the same hash. A real native record was private and a second write was refused,
preserving its original bytes/inode and cleaning the temporary name.

Native gate report SHA-256:
04756beb7f0e5f779a560eccd71477937392ae2c94216f6b6beebb9f27884267
(.local/logs/h07-db-qualification-gate-<sha256>.json).
Three local regression methods additionally exercise raw outcome/type binding,
actual/unknown failure refusal, unprotected witness refusal, native output and
custody binding, and non-overwriting private records. Their small fixtures are
parser/filesystem tests, not proof of a successful complete native qualification.
168 local checks pass. The complete positive path remains unexecuted.

Reproduce current premature-refusal checks without global build-input sync:

```sh
python3 scripts/host/probe_bdb_qualification_gate.py
```

After genuine terminal completion, inspect actual diagnostics first. The
prepared qualification command and its remaining production boundary are in
docs/RECOVERY.md. If the raw suite succeeds instead, use the existing strict
success path; do not manufacture a failed-summary qualification.


## Actual final-review dependency preflight

Read-only inspection confirmed that the shared deployed input set predates the
repmgr007 patch and the new review/qualification modules. The three older DB
source inputs are present and match their deployed locks; the 653-byte
repmgr007 archive patch and its lock row are absent there. This is the deferred
quiescent deployment already required by recovery policy, not an authentication
or network blocker and not evidence that the active test is stalled.

To validate the final-review dependency chain without updating active shared
inputs, scripts/host/probe_bdb_review_inputs.py creates a root-private metadata/
source-reference directory. It transfers the current frozen public locks and
verified local patch bytes, refers to existing immutable archives by private
links, independently extracts/patches the Tcl reference and compares it with
the running fixture's immutable input manifest. It also verifies all native
compiled checkpoint entries. No database cases or original-source writes occur.

Actual result: all 483 Tcl files and 460 native seed files match. The full input
manifest remains 336abd7ca1442e5102249da2f774b30326e06d268cd2b16b65fc81e8c333e6f9;
shared source archives are unchanged and the deferred patch remains absent from
the shared location. Its verified private bytes have SHA-256
7e5bccd45146a7bc3230da2595207bd0c2919a5e565a26eade8aba0b64ba54df.
Native preflight report SHA-256:
432eb23619a42d72bd8779be0e16744df594230efdab5a77987d416a5a95d32a.

After the complete standard producer is genuinely terminal and other jobs are
quiescent, sync the committed input set with scripts/host/sync_build.py before
using the prepared guest CLI. That receiver transfers the missing frozen patch,
its lock and the new modules. Do not run an incomplete deployed verifier or
synchronize the active suite merely to remove this known deployment gap.
