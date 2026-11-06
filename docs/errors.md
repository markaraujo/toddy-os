# Error and correction log

Record: date, story, symptom, evidence, root cause, correction, verification, remaining risk.

## Bootstrap — GitHub authentication

- Symptom: GitHub CLI rejected an expired/invalid credential.
- Cause: previously stored account authentication was no longer valid.
- Correction: owner completed the GitHub device authorization flow.
- Verification: authenticated account query returned markaraujo and private repository creation succeeded.
- Secrets: no device code, token or password belongs in this repository.

No OS build failures exist yet. Do not turn planning risks into invented test failures.

## 2026-11-05 — H01 QEMU drive serial syntax

- Symptom: the first QEMU process exited 1 before boot; SSH was refused.
- Cause: QEMU 8.2.2 rejects serial as a qcow2 block-format option in -drive.
- Correction: use separate if=none block drives and virtio-blk-pci devices
  with serial assigned to the device; retain explicit qcow2 formats.
- Verification: inspect the corrected guest startup and lsblk serial evidence
  in H01. The failed process did not write a successful checkpoint.
- Recovery: remove only the exited toddy-builder container and restart with
  scripts/host/vm.py start; persistent disk files are preserved.

## 2026-11-05 — H03 sanitized PATH and target identity probe

- Symptom: runner launch raised FileNotFoundError for runuser before a recipe ran.
- Cause: the deliberately minimal /usr/bin:/bin PATH excludes /usr/sbin/runuser.
- Correction: invoke /usr/sbin/runuser explicitly. Confirmed the probe file was
  absent and preserved the interrupted running record before retry.
- Verification: success, recipe-exit-42 and postcondition-exit-42 cases all pass;
  only success has a success marker. Logs are linked in H03 evidence.
- Separate read-only probe correction: virtio disk serial was queried initially
  at an absent sysfs device/serial path. Use lsblk's SERIAL column; the failed
  guard exited before changes. Target preparation uses the verified method.

## 2026-11-05 — H04 source-directory mode after transport

- Symptom: first H04 binutils attempt exited 1 creating sources/evidence.
- Cause: transporting the source cache with tar also applied the transport
  directory's 0755 mode to /mnt/lfs/sources, replacing required 1777 mode.
- Correction: restored sticky writable mode, verified access as lfs and added
  that postcondition to target preparation. Future source transport uses tar
  --no-overwrite-dir to preserve the target directory's metadata. Added guest
  swap to fstab so reboot retains the selected memory budget.
- Verification: failed attempt recorded zero changed installed paths and no
  success marker; prior logs/failed record preserved in runner history before
  retry. Corrected H04 executes with lfs and validated target guards.

## 2026-11-05 — Security-patch applicability experiment

- Symptom: initial Glibc security-patch validation could not find a relative
  input path, then a dry run reported later NEWS hunks failing.
- Cause: patch changes its working directory with -d; use an absolute input
  path. The patch is a sequence of commits; dry run does not apply the earlier
  NEWS changes required by later commits.
- Correction: verified baseline hashes, used absolute patch paths and actually
  applied the sequence to a disposable source copy, not the build root.
- Verification: all 49 patches applied with exit 0 and no rejected hunks.
  No package version or running build changed; final regression tests pending.

## 2026-11-05 — Xz security-input publication endpoint

- Symptom: multi-command retrieval attempts ended with HTTP 403.
- Diagnosis: archive and signature downloads had succeeded; the failing
  operation was the official signing-key endpoint, not the source artifact.
- Correction: inspected downloaded sizes and compared archive SHA-256 to the
  publisher's release-asset digest. They match. Retained signature, recorded
  PGP verification as unperformed and pinned the verified source hash.
- Verification: Xz 5.8.4 hash 4ce24038fd4221e0d13bc1a2de7a4db56e90b92b3bf75321f6c14be73f65de4b.
  No authentication bypass or global trust-store change was used.

## 2026-11-05 — Final Glibc staging and merged-/usr

- Symptom: package preflight rejected a real /sbin directory in staged Glibc.
- Cause: an empty DESTDIR lacks the book target's /sbin -> usr/sbin alias;
  Glibc placed ldconfig/sln there. Direct installation would follow the alias.
- Correction: canonicalize staged bin/lib/sbin payloads into /usr before
  ownership checks, preserving metadata and rejecting duplicates. Register
  staged /etc/rpc as a conffile too. Failed stage and attempt remain retained.
- Verification: first attempt had zero changed installed paths and no archive;
  critical suite remains accepted and unchanged. Retry result recorded in H07.

## 2026-11-05 — Glibc container-test UNSUPPORTED diagnosis

- Symptom: many container-backed tests returned UNSUPPORTED with EPERM and a
  generic hint suggesting changing Ubuntu's namespace sysctl.
- Investigation: a temporary named test-job AppArmor profile did not change
  the result. It was unloaded immediately; sysctl remained 1. A direct
  comparison passed unshare -Ur in builder root and failed inside LFS chroot.
- Cause: Linux unshare(2) documents EPERM for CLONE_NEWUSER inside chroot when
  process root differs from mount-namespace root. The harness's AppArmor hint
  was not a reliable diagnosis. No global policy was weakened.
- Next verification: repeat container-backed unsupported tests after actual
  native target boot (H12), preserving original suite outputs. Unsupported
  hardware/hugepage/optional-tool cases remain explicitly reported. No failed
  test was removed or marked passed.
- Primary source: https://man7.org/linux/man-pages/man2/unshare.2.html, EPERM
  chroot condition (since Linux 3.9), consulted 2026-11-05.

## 2026-11-05 — Readline shared Info index

- Symptom: preflight rejected /usr/share/info/dir already owned by Glibc.
- Cause: each staged manual installation generates a whole shared index.
- Correction: omit staged copies of the generated index and register primary
  installed .info manuals through the target install-info utility. Preserve
  the existing index as derived shared state and reject other file conflicts.
- Recovery: first attempt changed zero installed paths; preserve its stage and
  source tree, rebuild cleanly with corrected package integration and verify
  Readline runtime plus Info lookup. No forced ownership overwrite.

## H07 M4: inherited ignored SIGINT in detached runner (2026-11-06)

Symptom: GNU M4 1.4.21 `make check` reported 333 PASS, 48 SKIP and one
FAIL (`test-execute.sh`, case 5). Recipe exited 2 and changed zero installed
paths. The child explicitly raises SIGINT; the parent expects signal exit.
Cause: launching a noninteractive driver in the background inherited ignored
SIGINT. `start_new_session=True` does not reset ignored dispositions on exec.
The identical compiled test failed with SIGINT ignored (exit -6) and passed
with SIGINT default (exit 0) inside the same target.

Correction: the runner invokes GNU env `--default-signal=HUP,INT,QUIT,TERM`
before Bash, for recipes and postconditions. No test or package was weakened.
A regression test starts the real command under an ignored launcher SIGINT
and verifies that the recipe terminates from SIGINT. The first source tree
and suite report remain in target recovery/evidence directories; the full
clean-source suite retry passed: 334 PASS, 48 SKIP, zero FAIL; recipe and
postcondition exit 0. Its full log SHA-256 is
bbadb5da2e6d3de7eb237250f24b0849aecd3a0f8e728cd7dd5027099f475f29.

## H07 Tcl optional database clients and Expect PTY input (2026-11-06)

Tcl's make test exited zero; independent summary parsing verified core
47159 total/43704 passed/3455 skipped/zero failed. It also exposed test-file
load errors for absent MySQL/ODBC/PostgreSQL client libraries. ADR-0011 records
these specific unavailable optional integrations separately; unknown errors
remain rejected. Future recipes retain the raw test stream and classify it
before native package installation. Current full raw output and classification
are retained under sources/evidence/h07-tcl and .local/logs/h07-test-tools.

The first Expect wrapper reached the PTY probe but did not build: Python
pty.spawn read the remaining recipe from streamed Bash stdin and sent it to
the echo child's pseudo terminal. Staging was absent, so the packager rejected
the attempt with zero installed changes. Redirect only the probe's stdin from
/dev/null; preserve the original unmodified source tree in recovery and retry
from verified archive. This fixes recipe transport, not upstream source/tests.
The failed marker/log is archived by the durable runner on retry.

## H07 GMP result-format assertion (2026-11-06)

The complete GMP 6.3.0 make check passed, but the recipe's follow-up count
looked for ^PASS: in per-test logs. Those logs contain bare PASS; the frozen
LFS 13.1 section 8.23 explicitly uses ^PASS. Direct inspection found 199
^PASS and zero ^PASS: lines. The recipe therefore exited 1 with zero target
changes, despite passing tests. Correct the assertion to the book expression,
preserve the original log/failed marker and resume the built tree with an
explicit gmp-install step. That step repeats the full suite, requires >=199
passes, archives reports and only then stages/installs. Do not re-extract or
rebuild already verified compilation just to correct log parsing. Apply the
same format correction to the prepared MPFR count. Acceptance thresholds
are preserved.

## H07 Shadow account audit after builder reboot (2026-11-06)

Native Shadow installation/configuration exited zero; its postcheck exited 2
because pwck found messagebus's /run/dbus home absent in the fresh /run tmpfs.
The essential messagebus account and path are exactly those in frozen LFS
13.1-systemd section 7.6; no password or package build failure occurred.
Create the runtime directory with that account's ownership before auditing.
H08 must provide persistent boot-time tmpfiles/service setup. Root remains
locked; no shared login password was introduced. Preserve the original failed
marker, verify the installed Shadow package unchanged using dpkg --verify,
and run a separate shadow-audit step instead of reinstalling. That step and
its full account creation/unprivileged shell/removal, pwck/grpck postcheck
passed with zero installed-file changes.


## H07 empty-stage documentation prerequisites (2026-11-06)

Final GCC staging reached the runtime splitter without a retained copyright
file. The splitter rejected it before installation; the failed manifest has
zero changed installed paths. Copy all five upstream GCC license notices
before splitting. Explicit gcc-install-resume verifies that failure, the
complete critical classification and existing stage, adds the notices and
packages without rebuilding. Native compiler/runtime install and C/C++/linkage
postchecks then passed (h07-gcc-install-recovery).

Ncurses copied its documentation into an empty DESTDIR without first creating
usr/share/doc. Unlike the book's live root, that parent did not exist. The
failed attempt changed zero installed paths. Create that parent explicitly;
ncurses-stage-resume verifies the original failure and existing stage before
copying documentation and packaging. Recovery recipe/postcheck passed,
including all four standalone setupterm cases. Neither correction changes
upstream sources, test thresholds or critical result classification.


## H07 Psmisc version stream (2026-11-06)

Psmisc compilation, suite and installation passed; its first postcheck exited
1 because killall --version writes its successful version output to stderr,
while check_native filtered stdout. Capture both version streams explicitly
for this program. A separate psmisc-audit verified installed files with dpkg
and passed version, process-tree and signal-list checks without reinstalling
or changing installed files. The original failed record remains intact.
A mistakenly targeted sed-audit failed its missing-record precondition with
zero installed changes; Sed itself had passed all along. It was removed from
future recipes; actual per-step identity is checked before interpreting driver
output, whose final record can belong to a later package.


## H07 Bash PTY descriptors and source-known differences (2026-11-06)

All 86 initial groups ran, but the independent classifier correctly rejected
ten diff lines despite upstream run-all's unconditional zero. No installation
occurred. Focused testing found Expect's inherited pipe at FD 4. Serial make
alone retained it; closing FDs 3/4 in the spawned child eliminated the exec17
and BASH_XTRACEFD errors. The first focused wrapper omitted run-all's TMPDIR
initialization and produced unrelated denied writes; that log is retained,
and the corrected wrapper uses /tmp. No test fixture was edited.

The remaining four signal-order diff lines and three extreme-precision printf
diff lines exactly occur in the official pinned LFS 13.1 Bash log. ADR-0016
records their semantics, scope and strict group-specific classification.
A complete corrected-PTY retry is running; no acceptance is inferred from a
running process. Configured exceptions reject all unexpected additions,
partial matches, wrong groups, truncated/duplicate coverage and fatal output.
Normal finite printf/signal behavior is separately checked natively.


Bash correction outcome: full 86-group retry accepted only the seven exact
ADR-0016 reference lines, zero novel differences. Native install/postcheck
passed; the separate finite printf/SIGUSR1/package-integrity audit also passed
with zero installed changes. Original rejection remains preserved.


## H07 Gperf generated-code fixture (2026-11-06)

The upstream suite/build/install passed, but the original generated-code
postcheck omitted size_t/strcmp declarations. GCC correctly rejected the
incomplete caller. A first audit fixture also omitted Gperf's declaration/
keyword separator and was rejected before compiling; its failed record is
retained in history. Use the installed tool's documented --includes option
to emit the required string.h declaration, then compile/run lookup of one
present and one absent key. Separate gperf-audit passed package integrity,
recipe/postcheck zero and zero installed changes; no package reinstall or
upstream/test modification was needed. Original failure remains preserved.


## H07 Python sequential patch/context preflight (2026-11-06)

The first Python recipe stopped before configuration with zero installed
changes. A single --dry-run cannot carry dependent modifications between the
five concatenated patch sections and reported extra failures. Actual application
in an independent source-verified probe reduced those to one real rejected
SSL test insertion: 3.14.10 introduced callback assignment/deletion assertions
inside the original hunk context. ADR-0018 updates only that context, retains
all five changes and all newer assertions, and pins the derived source input.

The adapted probe applies with --fuzz=0 and exit zero/no rejects. Its four
runtime/tool files exactly match the original series' applied result. AST
inspection preserves all 207 original SSL methods and adds both upstream
regressions (209 total). Full original/dry-run/adapted logs and preimage/runtime
hashes are in .local/logs/h07-python-compatibility. Native Python compilation
and complete tests are still pending; patch applicability is not acceptance.
Resume only the verified untouched original main tree after checking its failed
record, absence of configuration/stage artifacts and every archived regular
source file. Do not re-extract over it or install the partly patched probe.


## H07 native continuation corrections (2026-11-06)

Python's full initial suite failed two network cases: missing target resolver,
not an SSL patch defect. A guarded temporary build-only resolver repaired DNS;
all full-suite retry results and the initial failure were retained. H08 must
replace it with runtime configuration. Coreutils patch context correction is
ADR-0019; Findutils' supplied-regex selection and complete regression proof are
ADR-0020. Both original failures changed zero installed files. Groff's initial
neqn smoke failure is a missing build-directory PATH entry; focused reproduction
passes after that correction, with full-suite recovery required before install.


## H07 Kbd and Tar diagnostics (2026-11-06)

Kbd's two Turkish patch hunks had obsolete Meta_Tab context; the frozen source
has Backtab. ADR-0022 updates context only and proves all 1327 regular postimages
match book-default application. Rebuild/full suite/native parser passed.

Tar's only full-suite failure is a getcap display difference, not lost capability
bytes: 223 PASS/20 SKIP/group 233 FAIL, raw make 2. Independent compiled-Tar
roundtrip preserved security.capability exactly. ADR-0023 and strict classifier
retain the failure and require installed binary-xattr plus ACL checks. Do not
use the book's generic SELinux explanation as the measured cause here.


## H07 service/filesystem environment and source transport (2026-11-06)

Systemd's four POSIX-locale ellipsis/help-width failures pass in UTF-8. Complete
retry is 1828 OK/33 SKIP/one exact book-known namespace EPERM; raw exit retained,
H12 native retry mandatory (ADR-0025). First collector retry used a duplicate
build/ path and stopped before staging; corrected full repeat/collector passed.
E2fsprogs' only failure is 232 versus 224 allocated sectors in the book-known
prezeroed fixture. Strict classification and actual installed ext4 write/remount/
fsck/persistence passed (ADR-0027); installer must use normal initialization.
GnuPG primary hostname timed out and mirrors were stale. The official FTP
hostname exposes the same website at /ftp/gcrypt/; all six archives and both
published signing fingerprints verified there (ADR-0026), with no trust downgrade.


## H07 Libuv test fixture group ownership (2026-11-06)

The first complete 507-case run fails only fs_copyfile and fs_copyfile_iouring.
Both assert destination GID equals the archived root-group fixture, while the
unprivileged tester creates files with GID 101. The source tree had been chowned
to tester without changing GID, leaving that fixture group root. Change only the
build/test tree to tester:tester, retain initial logs and repeat the full suite;
no privileged group membership, test/source change or global permission change.
Installation remains gated on the complete retry and native libuv API probe.


## H07 GnuPG disabled-CMS profile (2026-11-06)

OpenPGP reports 65 successes/one skip, but unchanged make check unconditionally
enters CMS and cannot find disabled Gpgsm. No package was staged/installed.
ADR-0030 enables the local component using already accepted libraries, preserves
the first build and requires an original-source-byte-verified fresh rebuild plus
complete retry. No CMS test is removed; external keyservers remain disabled.


## H07 Vim interactive test stdin (2026-11-06)

The complete initial suite inherits /dev/null stdin and reports premature exits
in many input tests. Actual focused getchar/Ex-mode tests pass under a tester-
owned PTY. The first regex probe matched no tests and was explicitly rejected as
acceptance evidence; corrected probes execute one test each. Preserve all first
reports/tree, fresh-extract source and repeat the entire unfiltered suite under
native Expect (ADR-0031). No installation occurs before full success.

- H07 Dpkg: safe extraction refused three authenticated FIFO test fixtures,
  before compilation/installed changes. Exact archive/name/type allowance plus
  standard path/mode/ownership checks added; all members prevalidated. Partial
  tree/failure preserved; filter regression tests pass, native retry initiated.

- H07 Berkeley DB test build: upstream Tcl bindings require DBM/compat185 even
  for C-library tests. Enable in the disposable test build only; production
  profile still disables both. No installed changes; fresh verified retry.
