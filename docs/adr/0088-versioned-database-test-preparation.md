# ADR-0088: Version the private native database test preparation

- Date: 2026-11-07
- Status: Actual preparation/isolation passed; fresh-recipe integration pending
- Extends: ADR-0032, ADR-0069 and ADR-0087

## Decision

Replace the session-local preparation dependency with
scripts/build/db_standard_prepare.py. It takes an existing native test build,
independently reconstructs the frozen Tcl reference, inventories source and
compiled test inputs, then copies them into a unique private generation. No
historical diagnosis-directory name or historical binary digest is required by
this preparer. The caller must retain actual source/compile provenance; copying
bytes is not proof of compilation or successful tests.

Keep the existing namespace runner and complete standard Tcl entry unchanged.
Their isolation semantics and source references remain ADR-0069's. Selection
preserves native executables/wrappers, headers, object/archive inputs, .libs and
Makefile/include.tcl. It excludes previous build-test output and other build
products, creates an empty production directory, and records 10,207 copied
files plus the separately installed complete-suite entry. Check file bytes,
modes and relative links after copying, and recheck original inputs after the
native isolation probe. Refuse external/absolute links, special inputs, missing
compiled prerequisites, changed test-helper source or insufficient disk reserve.

The root-private preparation intent, input manifest, copied driver and namespace
scripts are retained alongside the probe log/exit and final preparation record.
Only the isolation probe runs here. The factory neither invokes run_std nor
installs/accepts a package. Fresh-recipe dispatch, portable compile/coverage
provenance and terminal qualification integration remain required. In particular,
these generic preparation records are not interchangeable with the pinned
recovery verifier's accepted-result profile.

Alternatives: retaining the ignored launcher preserves an unavailable temporary
path on a new checkout; copying an entire tested build carries mutable database
files/old outcomes; recompiling solely to obtain another copy wastes the existing
verified native checkpoint. Inventory and verify the necessary bytes instead,
while keeping eventual native provenance and full-suite acceptance mandatory.

## Actual evidence

The host probe transfers current code/locks and the missing frozen patch only
into a private guest directory. It uses the completed, protected native coverage
source, leaving the full running suite and shared deployment untouched.
The final prepared generation is
/mnt/lfs/sources/recovery/db-standard-z4zf__8c; private code is
/mnt/lfs/tmp/db-prepare-code-yr3nnuny.

Actual result: 10,207 native input files copied, all 483 Tcl files independently
verified and all 460 historical native checkpoint entries equal. Probe exit zero;
four namespace identities differ from the outer view, canonical source resolves
to the private copy, temporary directories are private and effective shared
memory is tmpfs. The outside temporary marker is absent, original inputs and
coverage records are unchanged, and no standard log/ALL.OUT/driver PID exists
in the new generation. The empty production directory carries no old artifacts.
The original uncorrected source and an outside source path were both refused
before creating a generation.

Raw report SHA-256:
3345c582b5b82356773496d4228499c1dc79290313ad59c73324654ab605924e.
Preparation module SHA-256:
20480ccc5bd0bf208a9932ca1b7bba40e00624a5f710a593741210823d9a800e.
Input manifest SHA-256:
229a27d4530bb3a2f32cbdc4a7de9a21786688d98dd93f7a0c4d1597422fb78c.

Three additional local filesystem checks cover excluded prior outcomes, preserved
relative library links, changed source during copying and escaping/absolute
links. They do not simulate full native suite success. The earlier preparation
probe (before retaining an empty production directory) is also preserved:
861a0670b6cf7c96bcc1e2ce7c1d042a85d0701e781eecf44202e0b6e0849eb9.

The running full standard suite remains the sole complete corrected attempt.
Do not launch the prepared generation as a duplicate or replace its actual
outcomes with these preparation results.
