# ADR-0049: Separate optional CPython regression data from release runtime

- Date: 2026-11-06
- Status: Staging, marker audit and private unpack ownership transfer verified; configured target transfer and release exclusion pending

A bounded read-only audit found 15 private-key PEM fixtures in the installed
CPython test/certdata tree. Every byte matches both the own native package
record and the original frozen Python-3.14.10 source archive. They are public
upstream regression inputs, not owner/provider/OS identity credentials. No
material is printed, committed, embedded in project memory or trusted as an
OS identity. This scoped audit is not a whole-image credential scan.

Keep complete regression data available to the builder/QA environment but put
it in an optional python-test-support native package before release image
assembly. Exclude that optional package from both the normal root and on-medium
runtime repository; keep QA inputs separately for disposable test guests. The
main runtime retains SSL, unittest, compiled extension/runtime behavior and
normal application development support. No upstream tests or assertions are
removed or relabeled passed. Actual full source suites remain required.

The staged partitioner moves only the frozen main test and idle_test trees,
verifies bytes, links, ownership, modes and mtimes, preserves existing staging,
and refuses redirected/nested roots. Its production CLI refuses before target
changes unless H10 is completed/H11 in_progress. No package transfer runs while
the active H07 DB dispatcher owns the build lock. Current H07's 124/126 package
counts are unaffected; a later optional QA ownership split is not an additional
compiled upstream component or H07 acceptance credit.

Actual own native Python 3.14.10-1 archive experiment extracted into private VM
temporary staging, partitioned 5632 entries/5395 regular QA files, and verified
3943 retained runtime files/links unchanged. QA metadata/content also matched
exactly, including mtimes needed by bytecode. No installed changes, package
ownership transfer or image validation is claimed. Original archive SHA-256
ffb2baa6df3defc9122b3c7e35316afe2156fffab44f2f7ded2fdbbb51f3ad64.
Temporary extracted data is removed. Raw prefixes outside Git:
.local/logs/h11-python-qa-native-archive-probe and
.local/logs/h07-python-upstream-key-fixtures.json. Hashes are recorded in the
H07 evidence continuation; no key bodies are recorded. Four safety tests pass,
95 total local checks.

Next eligible implementation must transfer ownership through a new version of
our own preserved Python archive plus the QA package, preserving conffiles and
all runtime bytes. Install QA only after the core package relinquishes those
paths; never delete tracked files from an image while leaving Dpkg claiming
ownership. Verify exact original QA data, installed ownership, native SSL/test
operation, final root inventory and a complete image credential scan. Merely
hiding scanner findings or deleting source tests is not an alternative.


## Repeatable private-key-marker audit of the actual native archive

scripts/build/h11/audit_private_key_material.py now supplies one explicit
release audit component. It streams every regular file in a canonical private
staged tree, recognizes PEM/OpenSSH/OpenPGP private-key armor markers across
read boundaries, and emits only finding paths, reason identifiers and whole-file
SHA-256. Matched bytes are never printed. It does not follow symlinks, refuses
cross-filesystem traversal, does not read special nodes and propagates read
errors. The production CLI retains the H11 gate and accepts only a selected
root under designated target staging. This is a read-only check, not removal
of findings or a complete credential detector.

The alternative of treating all upstream QA keys as release-safe would leave
private-key-shaped material in an ordinary system image. A blanket grep with
matched lines could disclose actual credentials. Keep QA separately and report
only metadata. Arbitrary API tokens, passwords, identity state and unarmored
key/container formats still require their own image checks; zero marker
findings alone never means a credential-free release.

Reproduce the real native experiment with
python3 scripts/host/probe_python_qa_key_audit.py. It verifies the current own
Python archive hash, extracts through native Dpkg into a private guest fixture,
scans it, partitions QA with the existing helper, and scans both resulting trees.
The observed Python 3.14.10-1 archive is the same original archive cited above.
All 15 findings match their recorded package payload hashes and remain byte-for-
byte in the QA tree. The separated runtime has zero private-key-marker findings.

The scan covered 9,330 regular files and 293,207,634 bytes before partition:
3,935 files/126,608,219 bytes remain in runtime and 5,395 files/166,599,415 bytes
move to QA. Eight runtime symlinks were not followed. Both total file count
and total bytes are conserved; no QA test is changed or discarded. The earlier
3,943 retained-entry count included those eight links. The successful private
fixture is removed and the installed package/ownership database is unchanged.

Raw report .local/logs/h11-python-qa-key-audit-probe.json, SHA-256
`10ebd9a0c6d58e448afd9e8e931396e4ead5e8439e2baaf5dd22d38cbfb4ff76`,
also retained under a content-addressed filename. Audit helper SHA-256:
`7c97e36417a150866a04b9d87bceb60419c56ee96b815999cd1abec65d9c64b6`.
Three local tests cover all recognized headers, chunk-boundary matching,
no matched-content disclosure, public certificate/key handling and link safety.
Native package ownership transfer, normal image exclusion and complete image
credential inspection remain pending.


## Actual native Dpkg ownership-transfer experiment

scripts/host/probe_python_qa_ownership.py now verifies the handoff using real
source-built Dpkg 1.22.22 and the actual own Python archive in two private
package roots. Its --root and --admindir behavior follows the frozen
dpkg-1.22.22/man/dpkg.pod. --unpack deliberately does not configure dependencies;
these results are ownership evidence, not a configured Python/QA installation.
No force-overwrite, force-depends or Replaces exception is used.

The probe verifies the predecessor archive against its native record, extracts
its data/control, applies the existing staged QA partition, increments the
private package generation and builds two native archives. The runtime retains
its exact predecessor Depends field and conffile list. The QA package depends
on that exact new Python version and retains the original copyright notice.
Compression is bounded by DPKG_DEB_THREADS_MAX=2, documented by the frozen
dpkg-deb manual. These private archives are not distributable release packages.

In the negative root, unpacking QA before upgrading Python is rejected by
Dpkg's ownership conflict check. All original QA file bytes/links remain
unchanged; the rejected root may contain partial package state and is never
used as the positive result. In a separate fresh root, the original Python
first owns the complete QA set. The runtime upgrade then removes its QA
ownership and payload. At this interruption boundary, the original archive
and both new archives remain available for recovery. Unpacking QA afterward
assigns all 5,395 files to python-test-support with no duplicate Python owner.
Every transferred file's bytes, type/mode, UID/GID and mtime are preserved.

Both private final package states are install ok unpacked, explicitly not
configured. Native installed /var/lib/dpkg/status is unchanged by SHA-256.
No system package files, running DB sources or actual test coverage change.
Successful fixtures are removed; failure fixtures are retained with exact
paths and content-addressed reports.

Final raw report .local/logs/h11-python-qa-ownership-probe.json SHA-256:
`25138b993d255f866d061eab20a6e13bbfdc86eee3aebe54b6386b920941be45`.
Tested host probe SHA-256:
`d9fbb7739c6c741af5b2b1a02cfc2ccd9719c059c85f5a83368134e8c0f97c06`.
The observed predecessor was 3.14.10-1; the private successor was
3.14.10-1+toddy1. Production must derive its next generation from the accepted
current package after H07 closure, not reuse this experiment's version.

The production transfer must prepare both provenance-backed package archives
and recovery state before removing the original owner, then install/configure
the runtime first and QA second. The general packager retains its default cross-package conflict refusal.
The narrowly checked archive-only preparation below addresses the need to
prepare QA before the original owner relinquishes it; no force-overwrite or
untracked deletion is introduced. A durable production transfer/installation
recipe, configured dependency/runtime checks, complete package audits and final
image exclusion remain required.


## Narrow archive-only preparation in the native packager

stage_package.py now accepts --prepare-python-qa-handoff only for
python-test-support, without --install, after the H11 gate. Ordinary calls
retain the original ownership-conflict refusal. This flag is not a general
conflict bypass: python_qa_handoff.py requires the complete unchanged QA trees
from the current configured Python's own recorded payload, unique Python file
ownership, the same architecture/source set and an exact dependency on the
newer successor Python version. Other payload is limited to QA documentation
and reviewed shared parent directories. Missing, modified or unrelated files
are refused. The current predecessor archive must match its recorded SHA-256.

For every transferred file, the preflight also checks the actual installed
bytes/link, mode, UID/GID and timestamp against the staged copy and predecessor
record. It records the predecessor version/archive/record hashes and complete
path list in prepared_ownership_handoff. The resulting archive record remains
installed=false and the plan does not permit installation. The eventual
installer must independently confirm that the original owner has relinquished
the paths; standard Dpkg conflict/dependency checks still apply.

A private native preflight against the real 3.14.10-1 package verified all
5,395 files. Explicit install mode and changed staged bytes were rejected;
restoring the exact bytes/timestamp restored acceptance. Installed Dpkg status
and native package cache were unchanged. This probe invokes the preparation
function on real data, not the gated production CLI, and does not claim the
production archive/transfer recipe has run. Four local regressions cover
complete/equal data, installed-owner uniqueness, partial/extra/modified data,
source/architecture/dependency mismatches and install/bootstrap refusal.

Reproduce with python3 scripts/host/probe_python_qa_handoff_plan.py. Raw full
plan and checks: .local/logs/h11-python-qa-handoff-plan-probe.0e75b331a1c7036ca379bcd61d6387c794cd1615bd1f6d75a41d899b242e0679.json SHA-256
`0e75b331a1c7036ca379bcd61d6387c794cd1615bd1f6d75a41d899b242e0679`.
Tested handoff helper SHA-256:
`ea006cf7bc41824db4948ba6049870bf022239e010d5940872d2d59cd4ff634f`;
tested packager SHA-256:
`cff8a4469f412ae218536a249324ae5d2b51f06efe9bafa19cd9697802b0ca50`.
The private fixture was removed. No active DB recipe input was synchronized.


A portability regression reproduced a collision with an unrelated regular
Python package named h11: importing h11.python_qa can resolve to that external
package instead of this repository's H11 directory. The helper now loads the
project layout from its explicit sibling file path. No third-party HTTP package
is installed or removed. The regression supplies an isolated unrelated h11
module and requires successful project-layout loading in a fresh interpreter.
The native probe now uses a private physical mirror of the three public source
files, so its import path matches the corrected production behavior.

Original collision evidence .local/logs/python-qa-h11-namespace-collision.json
SHA-256 543cfcca0c7b0d34c87a4516e86127ae6d8c1d6ba9d5d99b6ac82d69f1c7bd8f.
Repeated native preflight passed all 5,395 files and both rejection/restoration
cases; current full report SHA-256
`c62754d54b2904231aa7714350cd2b3a19ad3fd7879366e3be7478c3054921a3`
at .local/logs/h11-python-qa-handoff-plan-probe.json, with an immutable
SHA-256-suffixed copy. Corrected helper SHA-256:
`0684d5d276786d5fa23705be1996b9a7f8ef3355f3cdbb489ac5db1b2161167b`.
Installed state/cache and active build inputs remain unchanged.


## Direct interpreter dependencies and actual interrupted unpack recovery

The native QA executable audit found six env/python3 and three Bash shebangs
among 13 executable fixtures. Native owners are coreutils for /usr/bin/env,
bash for /usr/bin/bash and python for /usr/bin/python3.14. The prepared QA
package therefore requires python (= successor), bash, coreutils explicitly.
A Python-only dependency would fail the project's direct-provider audit even
if those tools were present transitively. The preparation helper and private
ownership probe now use that closure. A negative native preflight rejects the
missing direct providers, and the complete 5,395-file positive plan still passes.
Installed state/cache and active build inputs remain unchanged.

The native ownership probe additionally creates a third private Dpkg root,
unpacks the original Python and deliberately SIGKILLs a new process group
while unpacking its replacement. No signal targets the installed target or
active build process. Dpkg exits -9 and reports the OLD version 3.14.10-1 as
install reinstreq half-installed. This proves version equality alone cannot
identify a safe starting state. The preserved archives allow reapplying the
core followed by QA; both recover to install ok unpacked, with all 5,395 QA
files verified for bytes, ownership, mode and mtime again. No force-overwrite
or dependency bypass is used. This verifies unpack recovery, not configured
runtime acceptance. The unchanged installed Dpkg status hash is checked.

python_qa_transfer.py selects a next action without executing it. A matching
validated transaction is mandatory before repairing partial state; an old
version half-install is retried from the preserved successor core archive.
Unpacked/half-configured core must be configured before QA installation. A
fully configured pair requests verification without reinstalling. Unexpected
versions/states are refused. Native replay of the actual current, interrupted
and recovered observations passes, including refusal without a recorded
transaction. Seven local regressions cover these boundaries and JSON input.
The production controller must still validate archive/record identities, persist
intent before mutation, run each action and verify ownership, dependency and
runtime postconditions. No production transfer is claimed by this policy.

Evidence (raw reports and immutable SHA-256-suffixed copies under .local/logs):

- h11-python-qa-interpreter-providers.json:
  ee3ff40f65c60eee24e94d4c448583b06a0f2533721bf50f1424fe1f97fb48c8
- h11-python-qa-handoff-plan-probe.json:
  b500a78e73829f8d039e03da51966d85db96edbb8e3d4997cfc442c684ba3152
- h11-python-qa-ownership-probe.json:
  94316e1bdd653440e5e8e84f1d1868dd48c03011cf9bd85d96df9b972afcd44d
- h11-native-python-qa-transfer-policy.json: b73d3ef1e938942b6503cbde166e76b1a4447030b7bcc4cd90785a25b4e7c517

Frozen Dpkg 1.22.22 man/dpkg.pod distinguishes unpack from configuration and
defines the private --root scope; man/dpkg-deb.pod documents bounded compression
threads. The probe continues to cap compression at two threads. Reproduce
with scripts/host/probe_python_qa_ownership.py and
scripts/host/probe_python_qa_handoff_plan.py in the designated builder. On a
failure, preserve the reported private fixture and logs; do not retry against
the installed database or delete partial state as a substitute for recovery.

## Complete pair validation and gated archive preparation

Added prepare_python_qa.py, an archive-only production recipe guarded by the
existing H11 prerequisite and actual native Dpkg acceptance. It derives the
successor generation from the configured predecessor, verifies its own archive,
extracts and partitions that preserved payload, retains the runtime dependency
and conffile contracts, and prepares core then QA through stage_package.py.
Both archives are prepared before any ownership change. The final prepared.json
records identities, archive hashes and the unchanged installed status hash.
Existing stages/artifacts are preserved for diagnosis rather than overwritten.
The complete production CLI has not run: H11 remains gated.

python_qa_bundle.py adds a whole-pair boundary: runtime must equal every original
non-QA payload entry, while QA must contain every original QA entry and only
reviewed parents/notices. It checks the predecessor record/archive identities,
complete transfer list, exact source rows, actual archive identity/architecture,
unchanged runtime Depends and complete QA direct dependencies. Validation alone
cannot authorize installation. The caller must hash archives, read their actual
controls and compare extracted payloads, then retain normal Dpkg checks.

The private native preflight now builds both actual native archives with two
compression threads, re-extracts each, compares the complete data manifests and
runs the pair check against controls read by native dpkg-deb. It passes for
5,395 QA files and 3,943 retained runtime files/links. A changed retained ssl.py
hash is rejected; all earlier missing-provider, install-mode and modified-QA
negative cases still pass. Installed status and package cache are unchanged.
These experimental archives are not release candidates; their successful
private fixtures are removed. Four local regressions cover runtime loss/change,
QA loss/injection and source/control/transaction identity differences.

Native raw report .local/logs/h11-python-qa-handoff-plan-probe.json SHA-256:
`5cbbcd25aff0b5a0755da4dab7576f9745e6407930172163e001cf45333c6c24`.
An immutable SHA-256-suffixed copy retains this result. Pair validator SHA-256:
`ac2b1067195b9bb6c5b61872ea5b6da2f139bfa9f06749ac6ac55479ac61d094`.
Prepared production recipe SHA-256:
`9b8089620b34d64f8624a0fe74062b28cdb41b01d8c8fbab491eb2d4ebacefff`.
Only its reusable archive-control reader was executed by the private probe;
no claim of full gated recipe execution or installed transfer is made.

The native backend intentionally runs env -i, so an outer compression environment
variable would not reach dpkg-deb. The packager now accepts an optional explicit
--compression-threads budget, passed as native --threads-max=N; other recipes
retain their previous default. Frozen Dpkg 1.22.22 man/dpkg-deb.pod documents this
option since 1.21.9. The prepared recipe and successful private native builds
request two threads explicitly. Active build inputs have not been synchronized.

## Durable native installation and configured recovery probe

Added python_qa_transaction.py and the H11-gated install_python_qa.py entry.
The executor independently rehashes all three retained archives, re-extracts
and compares their complete payload manifests, refuses unexpected maintainer
programs, preserves the original conffile contract and checks the whole pair.
It binds a private locked journal to the exact target, archive identities and
record contents (only the installed bookkeeping flag is mutable). Initial
installed predecessor files and unique ownership must match before any action.
Missing/mismatched transaction state is not treated as permission to resume.

The journal uses an atomic same-directory replacement, file fsync and directory
fsync before every native Dpkg mutation. Actions are selected from actual
version/status pairs, bounded to eight transitions per invocation, and stop on
failure or an unchanged state after a reported success. Normal native dependency
and ownership checks remain active. Core configuration precedes QA installation;
QA paths must be released, with no unexplained unowned files. Completed state
requires exact file bytes/links/modes/UID/GID and unique ownership, a clean native
Dpkg audit and actual Python, SSL, SQLite and QA-support imports. The separate
entry marks successor provenance installed only afterward. A repeated completed
transaction verifies again without reinstalling. It preserves the predecessor
archive and does not infer any image/ISO acceptance.

Alternatives rejected: version-only restart detection misses the observed old
half-install; clearing partial package state destroys recovery evidence; global
force-overwrite hides ownership defects; treating prepared.json as installation
success skips native configuration/runtime checks. Frozen Dpkg 1.22.22's
unpack/configure and status semantics remain the authority. The tradeoff is
additional retained artifacts and journal I/O; those support deterministic
recovery and diagnosis instead of silent reconstruction after a partial install.

The configured private probe used 22 actual own source-built dependency packages
(135,934,568 archive bytes), unpacked and configured with native Dpkg in a fresh
private root. It interrupted the executor after real core installation and
configuration but before capturing that action's exit in the journal. The
journal therefore honestly retains exit=null for that action. An attempt to
continue without this journal was rejected. Resuming with the original journal
installed/configured QA, verified all 3,943 runtime files/links and 5,396 QA
package files (5,395 transferred fixtures plus its copyright notice), passed a
clean Dpkg audit and executed Python with OpenSSL 4.0.3 and an in-memory SQLite
query returning 42. A repeated run added no Dpkg actions and left package status
unchanged. This is real configured recovery, not a mock native package result.

The earlier separate native SIGKILL experiment covers Dpkg half-installed
recovery; this full controller probe covers interruption after core
configuration. Do not claim that every possible crash point was exercised.
Four local boundary checks cover modified/ambiguously owned files, parent
redirection, durable journal replacement and refusal of a redirected journal
before package operations. The final target still requires gated execution,
final image QA exclusion and all release audits; neither H11 nor G1 is accepted.

Raw report with complete dependency install output, native action logs, durable
transaction, rejection cases and runtime postconditions:
.local/logs/h11-python-qa-transaction-probe.json, SHA-256 dffbf0fc3c76a0e600d064538e1e21a63c6ebd31f5c0c2b729980ed6b09ea645.
An immutable SHA-256-suffixed copy is retained. Tested executor SHA-256:
589d855704da606f82659004b549e30e4762f045ccc797709d5b547b79098764.
The gated production entry has not executed; SHA-256:
e49ff36842f00c367060053e9e5a7e4ce63ce7cc5d48f3d225521e1f9fce77e1.
Reproduce with python3 scripts/host/probe_python_qa_handoff_plan.py --transaction.
Successful private fixtures are removed only after retaining their logs in the
report. Failures preserve the exact printed fixture. The installed target status,
package cache and active DB source inputs remain unchanged.

## Actual H11 production transfer accepted (2026-11-07)

After actual H10 live acceptance, the production dispatcher prepared both
archives and completed the configured native transaction. Python moves from
3.14.10-1+toddy1 to 3.14.10-1+toddy2, with python-test-support at the matching
revision. Exactly 5,395 QA files move and 3,980 runtime files/links remain
unchanged (the final metadata payload includes retained legal notices beyond
the earlier private fixture). Native SSL/SQLite runtime, Dpkg audit and APT
check passed; recipe/postcheck are 0/0. Complete builder tests remain available.
See docs/evidence/H11-python-qa.json. Actual final-image exclusion and full
credential review remain required; this transfer alone does not accept H11.
