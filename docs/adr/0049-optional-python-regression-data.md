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
