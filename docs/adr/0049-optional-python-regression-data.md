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
plan and checks: .local/logs/h11-python-qa-handoff-plan-probe.json SHA-256
`0e75b331a1c7036ca379bcd61d6387c794cd1615bd1f6d75a41d899b242e0679`.
Tested handoff helper SHA-256:
`ea006cf7bc41824db4948ba6049870bf022239e010d5940872d2d59cd4ff634f`;
tested packager SHA-256:
`cff8a4469f412ae218536a249324ae5d2b51f06efe9bafa19cd9697802b0ca50`.
The private fixture was removed. No active DB recipe input was synchronized.
