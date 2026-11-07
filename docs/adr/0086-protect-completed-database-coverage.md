# ADR-0086: Protect completed native database coverage evidence

- Date: 2026-11-07
- Status: Actual native custody transfer and read-only verification passed
- Extends: ADR-0083 and ADR-0084

## Decision

The completed coverage witness has verified native bytes and actual exits zero,
but its source tree was still owned by tester. Protect that completed tree and
require a separate read-only custody proof during the later full-suite review.
Do not alter the running standard source, its test inputs, summaries or exits.
This is evidence preservation, not acceptance of the complete suite or package.

The measured source initially contained 361 directories, 10,240 regular files
and four symlinks below its top directory, with no external hardlinks or special
entries. Source ownership was tester UID/GID 101 and its top mode was 0755.
The actual full producer remained live in its separate source tree.

scripts/build/db_source_custody.py first uses the existing exact native witness
verifier: actual 0/0 exits, dead producer, frozen input/harness hashes, all 10,208
source entries, report hashes, standard pairing and native coverage observations.
It takes the normal dispatcher lock and refuses active dispatcher/input sync.
Before metadata changes, inventory the entire physical source tree, reject
escaping aliases, special files and regular-file hardlinks outside that tree.

Record an exclusive root-private intent, close pathname access with root-owned
0700 parent/source directories, and inspect actual process cwd/root/descriptors
and mapped inodes for remaining source references. Refuse if any remain. Only
then take root ownership throughout the tree without following symlinks and
remove group/other write bits. Recheck inode identities, actual references and
the complete native input/report bytes before writing a separate custody receipt.
Raw result.json, inputs.json, reports and test exits are not rewritten.

An interruption retains the original intent and closed access gate. Resume must
match the same witness, tree entries and device/inode/type/link identities;
completed receipts are reverified and returned unchanged. A read-only verifier
requires the existing protected receipt and actual current metadata; it never
creates a missing seal or grants suite/package acceptance. The complete review
now requires this protected coverage proof. Full-suite source custody and its
explicit diagnostic qualification remain pending actual full-run termination.

Alternatives: result flags alone do not protect tester-owned inputs; copying
another complete tree is unnecessary for this already terminal native witness;
changing test outcomes would destroy evidence. Protecting existing verified
inodes preserves both bytes and their relationship to the executed diagnostic.

## Actual checks and correction

The native custody transfer passed for all 10,606 source entries including the
top directory. The current tester identity cannot open the preserved coverage
record. Repeated sealing returns the identical receipt. A real child process
holding a source descriptor was detected; after it released the descriptor, the
same check passed. Using the active full-suite fixture as a coverage witness
was refused before metadata changes. Local filesystem tests also reject an
external hardlink, escaping symlink and FIFO while retaining source bytes/modes.

The first access-denial check assumed /usr/sbin/runuser, which is absent from
the frozen native installation. The seal itself had already completed. Correct
the check to use native Python, clear supplementary groups and switch to the
actual tester UID/GID before opening the file. This exercises the same real
identity without installing an unnecessary utility or changing the target.
The preserved failure report SHA-256 is
7d56b5d962e39121dcce7224a07c9413adae5fe787fa905356483e6710a6d294.

Final native transfer/repeat/read-only/access evidence SHA-256:
53ffee402c4dd2285469fbb2a563c9195445c2a78af274a54e96743c4d44c4c7.
Custody receipt SHA-256:
0a2b9b17cf57a0de76dc20ce426f784c4e92aa401d44a1d3f43817726e6dccb2.
Original intent SHA-256:
60243098616cb2f89c86c67775ee80b873d0be71e5260ce1be8de52a6bb3bd7f.
The original coverage result SHA-256 remains
25346654d8a206d28fe1a239247a0a730a119b2ef6493299ce0a017960119edf.

The integrated actual review still refuses the unfinished full suite; all prior
sixteen native negative cases remain passing, with unchanged evidence report
6839dcca04bc5db9e13b9a0097ec1724d7f9e3ba4d7d34f55ffe1cc3de3eb0e3.
165 local checks pass. No production nomination, package install, full-suite
qualification or additional milestone acceptance occurred.

Reproduce the current recovery-witness custody verification with
`python3 scripts/host/seal_bdb_coverage.py`. It is specific to ADR-0083's measured
recovery generation. Portable fresh-build diagnostic handling and the strict
production handoff remain required H07 work; this recovery receipt is not a
substitute for running tests on a fresh build.
