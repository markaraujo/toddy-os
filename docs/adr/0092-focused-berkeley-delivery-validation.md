# ADR-0092: Owner-approved focused Berkeley DB delivery validation

- Date: 2026-11-07
- Status: Accepted; focused native production and APT consumer gates passed H07
- Supersedes: ADR-0032's mandatory complete standard Tcl suite for this experimental delivery, and the dependent full-suite production gates in ADR-0069/0087/0090/0091 only

## Authorization and decision

The owner explicitly approved adopting focused validation for the delivery.
Use focused validation of the frozen Berkeley DB C production library and its
actual APT repository-cache consumer. This is a deliberate reduction of coverage,
not a passing full regression result. Compiler, libc, binutils, package ownership,
signed repository, recovery, ISO and G1 requirements remain unchanged. The H13
owner-review boundary before any B story also remains unchanged.

The corrected full standard run is cancelled with its raw logs and nonzero
terminal status retained. Earlier failed runs remain failed. Do not generate a
full-standard success/qualification receipt, remove existing assertions, or reuse
an incomplete run as evidence of complete upstream coverage. The optional full
suite and strict result verifiers stay available for future broader validation.

## Required focused acceptance

1. Verify frozen archives, maintained patch series, native compilation provenance,
   all configured CuTest results and the selected production C-only build flags.
2. Run real production-library version, transaction commit, aborted update,
   separate-process reopen and persistent-value checks. Add an abruptly terminated
   writer followed by recovery and verification of the last committed value.
3. Run actual apt-ftparchive with Berkeley caching: initial index, reuse/reopen,
   source-derived metadata/checksum comparison, changed package refresh, and
   interruption followed by cache regeneration. Cache corruption must be detected
   and disposable cache removal/rebuild must restore a correct index.
4. Run the configured APT unit tests and existing native signed-repository tests:
   dependency install, upgrade, conffile preservation, signature/index/payload
   tamper rejection, HTTPS trust/name checks, sandbox identity, removal/purge and
   recovery. Preserve the native installed package database during disposable tests.
5. Install through the existing guarded package dispatcher, preserve manifests,
   run installed postconditions and final dependency/ownership audits. Focused DB
   installation may precede APT consumer tests, but H07 cannot pass before both do.

## Sources and rationale

Frozen APT 3.0.4 archive SHA-256:
`e853aec49afbe520ebcd4dbcbc98e1c55262c6bf1c119cf43e6aec69752443c6`.
Its CMake/FindBerkeley.cmake and ftparchive/CMakeLists.txt require/link the C
library. ftparchive/cachedb.cc uses a local DB_BTREE metadata cache; the cache is
rebuildable from the original packages. doc/apt-ftparchive.1.xml documents --db,
BinCacheDB and APT::FTPArchive::AlwaysStat (default false). Explicitly enable
AlwaysStat when testing refresh; do not claim the default refreshes replaced
same-version package bytes. The maintained DB 5.3.28+dfsg2-12 production/test
build split and frozen patches remain as recorded in ADR-0032.

Alternatives: finish the complete suite (broader coverage, long remaining wait),
remove Berkeley/change APT source (unnecessary product/build divergence), or
skip all testing (rejected). Focused delivery keeps the actual required consumer
and its recovery tests, with less assurance for other DB access methods,
replication configurations and the full cross-product of library operations.
No replication service or agent-memory use of Berkeley is promised.

## Actual cancellation evidence

The owner stop targeted only the verified GNU timeout child 1107208 of driver
1107192 in /mnt/lfs/sources/recovery/db-standard-nfv62s4o. The driver remained
alive to preserve reports and capture the real test exit 143 and driver exit 1.
No live process remained in that test process group. Classification:
owner-cancelled-incomplete; full-suite acceptance is false.

- Stop report: `f42ea85a386390302ac0b123ce2b4f2d4e57c0108bd6588a8056ff3ade257cdd`
- Stop intent: `ee288982a8f80f9887cfd0099800a093b9503da3f8f3b469490e232b3f9e5e8c`
- Retained ALL.OUT: `017d559e0378ee46cd0f75add659727a9d3be607418f74efb64ab44773e0eea0`
- Retained CuTest: `51763da1955dcca28f53b8bc863cec7f834179ddd994beda4b55f1cc4ab025d2`

Focused acceptance remains pending; this approval alone earns no milestone credit.

## Measured focused behavior

The staged production C library passed commit/abort/reopen and abrupt writer
termination followed by DB_RECOVER, with the committed value intact. Native
report SHA-256: 7a1b35a45d4da9dd5711757648b8346e2efe47870e5c15361ca783226102d172.
APT's private native build completed 466 Ninja actions and 142 tests across 28
suites. Its observer used an incorrect binary location; the original failed
observer result is retained and corrected in code, with no repeated compilation.

The actual corruption experiment found apt-ftparchive can emit E:/BDB errors and
still exit zero: writer.cc's PackagesWriter constructor calls DumpErrors before
SimpleGenPackages checks PendingError. The focused cache test therefore rejects
diagnostic-bearing candidates even on raw exit zero and verifies package bytes
before replacing an index. Cache regeneration, not database repair or silently
accepting those diagnostics, is the recovery policy. This upstream behavior is a
release limitation for scripts that check only the command exit code.

## Accepted delivery profile

All required focused production/consumer checks and final native closure passed;
see [H07 acceptance](../evidence/H07.md) and its actual reports. The earlier
pending statements above retain the decision chronology. Full Tcl coverage
remains cancelled/incomplete and is not presented as passed.
