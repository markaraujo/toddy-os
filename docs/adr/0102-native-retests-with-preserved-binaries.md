# ADR-0102: Execute preserved upstream test commands with complete native evidence

- Date: 2026-11-07
- Status: Cause and evidence recovery verified; corrected complete retest pending

The first H12 native retry ran Systemd test-namespace successfully. All 49 Glibc
cases failed through the test driver: make test tries implicit rebuilds using the
bootstrap-era AR path, which final package quarantine correctly removed. Do not
restore that obsolete toolchain path, rebuild installed libc, skip the cases or
count stale .test-result files as successes.

Frozen Glibc 2.44 Rules lines 411-436 and Makeconfig define the original ordinary
and test-container command/environment/loader prefixes. Makefile lines 982-988
implements the convenience target. scripts/evaluate-test.sh writes TWO result
lines, including original exit status. The first profile's one-line expectation
was also incorrect and has been corrected without accepting any failed result.

Use make -n -W BUILT_TEST test t=SUBDIR/TEST only to expand the exact frozen rule.
Select its unique expected output-redirection line, parse the command as argv,
require env plus the exact chosen test, and reject shell control/expansion syntax.
Execute that argv directly in the original source subdirectory, with the frozen
loader/library paths and all per-test arguments preserved. No diagnostic text
or arbitrary log command is executed. The 49-command native survey found exactly
47 test-container invocations and two ordinary tests; tst-vfork3's test-directory
argument is retained. Original source/build/test artifacts remain preserved.

Before execution require the preserved build libc and loader to be byte-identical
to the installed runtime. This was measured in the native builder: libc SHA-256
b17c378fe6f0b34354be1a5c850b8397f3582047875576c1e2b27a71a0a5bd25;
loader 3e7c5a6d36928914ba6e19b298fbe8aa2e0c0c4dbe122c1dc06021bb4edaee68.
Hash every selected test, the container helper and core runtime before/after.
Run the upstream evaluate-test script on the ACTUAL exit, requiring exit zero,
PASS and original exit status zero. Exit 77 remains unsupported; timeouts fail.
Exact core hashes must also match the final ISO's image manifest before G1.

Sources from the frozen source archive:
- Rules SHA-256 3b5904dd3339ac8e8254cad0a2d7cd03c9b56396774cdf8e4df9caf5c180d278.
- Makeconfig SHA-256 afbd9091d1e0a4200a7433670035f4f660da515070596371090309d91766c8be.
- evaluate-test.sh SHA-256 14bd21815cc132cf151ed1cf68f44cfe7cf23cdaa397af3b33fdc8dfc3352752.

## Evidence transport and recovery

The first journal/console export lost chunk 67 of 112; its parser correctly
refused acceptance. Copy its stopped writable overlay, preserve the original
SHA, boot only that copy with the same read-only backing, and export its retained
raw report through a dedicated second UART. This actual recovery passed and
reproduced the original report SHA-256
369ba282c246707b545fff696c79c5c36045316447aff1fbddd7e77655b23a2b.
The original overlay stayed unchanged; the recovered report still says 1/50.
See docs/evidence/H12-native-first-retry.json. No failed execution became a pass.

New native runs send numbered, hashed compressed evidence through ttyS1, separate
from the getty/kernel/journal ttyS0 stream. The host keeps both files, validates
all chunks and the complete digest, then applies unchanged 50/50 criteria.
The real recovered-report transfer validates this path; tests still reject
missing, conflicting and corrupted chunks. Only disposable guest serial settings
change. No workstation security policy or global runtime restriction changes.

## Actual second run and unprivileged RLIMIT fixture

The second complete run retained unchanged binaries and delivered all raw bytes
through the dedicated UART. **49/50 passed**, including io/tst-lchmod. Only
stdlib/tst-system returned 77 at frozen tst-system.c:206: its root-only branch
requires getpwnam("nobody"), but upstream testroot.pristine intentionally contains
no passwd database. test-container.c:1254-1289 maps only the original caller UID
and GID, so merely adding nobody would still leave that UID unmapped. Preserve
this exact unsupported result in H12-native-second-retry.json.

Execute this unchanged test as existing unprivileged tester (UID 101) so its
RLIMIT_NPROC assertion actually applies. Preserve the previous generated mutable
container root, create a fresh one owned only by tester, and temporarily grant
that user ownership of the existing private container lock. Restore lock ownership
and verify its bytes afterward. No installed account, source, binary, test result,
resource-limit assertion, namespace mapping or host policy is modified. The
regular test-container runtime still isolates filesystem/mount/user state.
A nonzero/unsupported result still fails the unchanged 50/50 gate. Full corrected
positive execution remains pending. This is not an exception for the syscall.
