# ADR-0049: Separate optional CPython regression data from release runtime

- Date: 2026-11-06
- Status: Staged partition implemented/verified; native package transfer and release exclusion pending

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
