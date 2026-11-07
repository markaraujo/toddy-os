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


## H07 Berkeley DB test142 environment isolation (2026-11-06)

The standard suite reached test142 under range partitioning and reported
BDB1540 configured environment flags incompatible with existing environment.
Frozen test139 closes a nontransactional environment but leaves its region
files. Test142 creates its own transactional environment before cleanup.
The same compiled native library and unchanged test139/test142 reproduce the
error in a separate TESTDIR; explicit prior environment cleanup lets unchanged
test142 complete its exclusive-handle assertions. Preliminary success sentinel
is preserved; a durable exit-captured focused correction test and complete
standard-suite rerun remain mandatory. Do not skip test142 or remove assertions.

The already-failed long attempt was stopped through its verified recipe PGID.
Runner result: recipe -15, postcheck not run, zero installed changes; package
manager driver exit 1. Original partial ALL.OUT, C tests, recipe/standard logs
and cancellation reason are preserved under builder /var/log/toddy/build/history/
berkeley-db-test142-20261106T161146Z. Failed recipe log SHA-256
8892e258779d037bc464117b638cb99b8e2be750196166f98f6a9b4b49c2cd57.
No production DB build/install occurred. Preserve the compiled test tree for
verified recovery; advance independent CPAN/Triehash/Which/Libseccomp/Tcsh work
before the corrected complete DB retest. APT still requires accepted Berkeley DB.

## H07 shared Perl installation journal ownership (2026-11-06)

HTML::Tagset passed 33 tests and installed with source-built native Dpkg routing;
its module-provider postcheck passed. Test::Warnings passed 89 tests, but native
ownership preflight correctly refused its generated shared perllocal.pod path,
already owned by the first module. No second-package installation occurred.
Native Perl 5.44 ExtUtils::MakeMaker documents NO_PERLLOCAL; its MM_Unix generator
omits all install-journal append rules when that configuration option is true.
Set NO_PERLLOCAL=1 at Makefile.PL generation, retain module-specific package/
packlist records, and require no staged shared diary. Correct the first package
through preserved-archive +toddy1 metadata, refusing modified live journal bytes.
Full source suites remain unchanged; native correction/retry acceptance pending.

## H07 Triehash installed CLI fixture (2026-11-06)

All seven unchanged upstream tests and default HTML coverage completed before
native installation. The postcheck failed because it piped words to a generator
whose frozen documented CLI opens an input filename. That invocation produced
an empty hash table, so lookup assertions correctly failed. Create an explicit
input file and pass its name; retain Alpha=3, Beta=7 and unknown-key assertions.
Actual corrected native generator/C compile/lookup postcheck exits 0. Preserve
installed archive/payload hashes, rerun all upstream tests and corrected postcheck
before accepting the installed package; no generator source change or assertion
removal. Original recipe exit 0/postcheck 1 remains historical evidence.


## H07 independent ownership prerequisite marker (2026-11-06)

The new ownership driver refused before dispatch/target mutation because it
looked only for h07-coreutils.success.json. The actual accepted final package
is recorded by h07-coreutils-recovery.success.json; its initial failed attempt
is correctly retained separately. Accept either actual successful runner path,
and additionally require installed native Coreutils 9.11-1 before the full ACL
retest. Never rename failed markers to success. Driver prerequisite failures
now retain exit status as well as PID/log. Retry after verified quiescent sync;
acceptance still requires the unchanged ACL suite including cp.trs PASS.


## H07 native spawn cache after Glibc overlay (2026-11-06)

Linux API headers and filesystem layout accepted. lfs-build-support 13.1-1
installed, then postcheck compilation correctly rejected unsuffixed POSIX spawn
actions. Frozen Glibc overlay patch 49 explicitly removes the header aliases
assumed by LFS 6.2 cache answers. Preserve failed marker/stage/archive; version
13.1-2 retains original cross template and enables direct native detection.
Require actual Autoconf no/no/yes/yes results and child directory-action behavior
before same-step acceptance. See ADR-0044; no libc upgrade or assertion waiver.

Verification of the spawn-cache correction: 13.1-2 same-step recipe/postcheck
0/0, direct native configure results no/no/yes/yes and both spawned-child
directory-action checks passed. Original failure retained; no libc change.


## H07 staged paths in Perl install records (2026-11-06)

Native ExtUtils::Packlist parses 3210 entries across 17 installed records;
330 module entries retain the own DESTDIR prefix. Original module tests/imports
pass, but those records cannot enter final metadata closure unchanged. Prepare
canonical own-package paths in preserved-archive metadata upgrades, retaining
all original archives/records. A private native roundtrip of 16 corrected
fixtures passes all 330 entries; actual installed correction/zero-findings
acceptance remains pending. No active BDB inputs were changed. See ADR-0045.


### Prepared Python metadata retry rejected its own canonical alias

- Symptom: code inspection plus the actual installed interpreter audit showed
  the full closure would need bash/coreutils edges after the early alias-only
  generation, but its next extraction would already contain python -> python3.
- Cause: the alias creation path treated every existing link as unexpected,
  including the exact previously accepted link in our own predecessor archive.
- Correction: retain only that canonical link; refuse other links/regular files.
- Verification: actual native Python/SSL execution through the twice-processed
  private stage passed; two boundary tests and all 97 local checks pass. No
  failed installed upgrade is claimed; this defect was caught before dispatch.
  See ADR-0036 and its raw evidence hashes. Full metadata acceptance is pending.


### Prepared kernel recipe queried a stale release string

- Symptom: actual native configuration resolved all 139 fragment options, but
  make -s kernelrelease printed 7.1.8 instead of the requested 7.1.8-toddy.
- Cause: Linux 7.1.8 excludes kernelrelease from automatic config sync;
  setlocalversion reads the stale generated auto.conf left by defconfig.
- Correction: make prepare before the exact release assertion, after setting
  the build identity. No changed kernel version or weakened assertion.
- Verification: private native preparation exited 0, returned 7.1.8-toddy and
  retained the exact resolved config hash. See ADR-0046. No kernel image,
  installation or native boot acceptance is inferred from preparation.


### Python QA handoff import collided with an external package name

- Symptom: a fresh-interpreter regression with an unrelated regular h11 module
  failed to import the project's h11.python_qa layout (ModuleNotFoundError).
- Cause: the phase directory was treated as an implicit Python namespace; an
  installed regular HTTP package with the same name can take precedence.
- Correction: load the known project layout by its explicit sibling file path;
  keep both external dependencies and the frozen build inputs unchanged.
- Verification: the collision regression now passes, and a private physical
  source mirror repeats the actual native preflight on all 5,395 QA files.
  See ADR-0049 for failed/corrected evidence. This was caught before dispatch
  of the new production mode, not a failure of the active DB recipe.


### Prepared Python QA omitted direct executable providers

- Symptom: the native executable audit found env/python3 and Bash fixtures,
  while the proposed QA control declared only the exact Python dependency.
- Cause: preserving the Python edge alone did not satisfy the project's direct
  interpreter-provider closure; transitive availability is insufficient.
- Correction: require bash and coreutils alongside exact successor Python in
  the archive preparation and native ownership experiment.
- Verification: native negative missing-provider preflight is rejected; the
  positive complete 5,395-file preflight and interrupted ownership recovery
  pass. See ADR-0049. Caught before production dispatch; no DB test change.

### Live account probe expected the wrong number of book groups

- Symptom: the private native account probe failed its group-count assertion
  after pwck and grpck had both returned 0.
- Cause: the test expected 33 groups; the frozen LFS 13.1 section 7.6 block
  contains 34, including the documented service and unmapped-ID groups.
- Correction: correct the probe count from the exact frozen block and retain
  native checker logs before subsequent assertions. Account data was unchanged.
- Verification: repeated actual native checkers pass, all locks/metadata and
  three preservation/refusal cases pass, and installed accounts are unchanged.
  Original failure and corrected evidence are retained in ADR-0055.

### Fresh image account preflight rejected the owned DBus identity alias

- Symptom: a private fixture including the actual DBus package link was rejected
  before generating account files.
- Cause: the prepared account helper treated every DBus machine-id path as
  inherited identity bytes, including the root-owned /etc/machine-id symlink.
- Correction: retain only that canonical root-owned link under physical parents;
  continue requiring absent /etc/machine-id and generate it empty. Preserve and
  reject a regular identity file or another link target.
- Verification: actual native Shadow checks pass with the owned alias; all five
  refusal/preservation cases pass. Original and corrected reports are in ADR-0055.

### Rejected Dpkg writer changed empty lock-file timestamps

- Symptom: the private database-copy probe observed the expected native Dpkg
  lock refusal, then failed an assertion that all lock metadata was unchanged.
- Cause: frozen Dpkg 1.22.22 opens both empty lock files with O_TRUNC before
  acquiring its POSIX write locks. That updates their mtimes even when locking
  fails; it does not mean the protected package data changed.
- Correction: exclude only these two empty lock-file mtimes from the snapshot;
  preserve file type/ownership/empty-content checks and every DB data check.
  Do not reopen/close a locked inode, which would release POSIX read locks.
- Verification: repeated native writer exits 2 while the read lock is held;
  DB data is unchanged, a held writer refuses the component, both fresh and
  preexisting owned-empty destination layouts pass, and nine negative cases
  preserve inputs. Failure and final evidence are retained in ADR-0059.

### Prepared H08 service check misclassified DBus's static socket

- Symptom: native is-enabled dbus.socket returns static, while the prepared
  postcheck required enabled.
- Cause: DBus supplies no [Install] section for that socket; its owned vendor
  sockets.target.wants link already provides activation.
- Correction: stop trying to enable the static unit; verify static state plus
  the exact owned vendor link, retaining the unchanged native unit.
- Verification: native private-root configuration, repeated checks and preset
  application preserve correct DBus activation metadata (ADR-0060). Runtime
  service activation remains pending; this was not a current H07 failure.

### Native preset application re-enabled network wait despite disable policy

- Symptom: after native preset-all, wait-online changed from disabled to enabled
  in a private fixture, failing the offline policy check.
- Cause: networkd's Also= installs wait-online indirectly despite the earlier
  Toddy disable preset. The actual source parser does not clear Also= on an
  empty assignment, so that drop-in approach cannot remove it here.
- Correction: retain the book's disable step and explicitly mask only this
  service in the Toddy target/image; document owner reversal and narrowly audit
  the generated link. Do not modify upstream units or workstation services.
- Verification: native configure/repeat/preset/readback checks pass with required
  services enabled and wait-online masked. Six configuration refusals and five
  audit boundaries pass. Failure fixture and both report hashes are in ADR-0060.


### Private loader-cache probe assumed the initramfs library layout

- Symptom: the first loader-cache probe refused with Foundation library alias
  differs before generating a cache.
- Cause: the helper assumed /lib64 -> usr/lib from the minimal initramfs profile;
  the actual full LFS package owns a physical /lib64 and two loader links.
- Correction: inspect frozen LFS/actual package records, preserve the full-system
  directory and links, and include those owned paths in the private fixture.
- Verification: two cache generations are byte-identical, native Bash uses the
  image cache/libraries, and twelve refusal cases pass. Installed caches/package
  state are unchanged. ADR-0064 retains original failure and final evidence.


### Fresh image account baseline omitted the selected APT sandbox identity

- Symptom: source/configuration review found the image account generator retained
  only LFS book accounts while the selected APT profile requires _apt. This is a
  future image defect; actual APT acquisition has not run yet.
- Cause: the build recipe creates _apt separately, but fresh image generation
  deliberately excludes inherited passwd/shadow state. APT's frozen missing-user
  branch clears the sandbox username and warns instead of failing the command.
- Correction: add the documented reserved image identity, require it during
  generation, and make prepared APT acceptance reject root-fallback diagnostics.
- Verification: native Shadow checks, Glibc identity lookup, Coreutils UID/group
  drop, partial-download write and root-only read denial pass. Native console
  regressions pass; actual APT worker/network checks remain pending (ADR-0065).

The first expanded account probe requested setpriv, disabled by the frozen
Util-linux profile. It refused before creating the account fixture. Reused the
accepted native Coreutils chroot --userspec/--groups instead; no host substitute,
new dependency or altered package build was needed. Failure evidence is in ADR-0065.


### Native ACL filename capture passed a bytearray to fsdecode

- Symptom: the first sidecar probe raised TypeError before writing its output.
- Cause: the escape decoder accumulated a bytearray, while os.fsdecode accepts
  bytes/string/path-like input.
- Correction: convert the decoded accumulator to bytes explicitly; preserve
  the exact upstream quoting rules for newline, carriage-return and backslash.
- Verification: native capture/restore, empty capture, access/ownership/mode,
  hardlinks/default ACLs and negative boundaries pass; local filename regression
  checks cover the original path. Failure and success hashes are in ADR-0048.


### Mutable image directory copy would preserve builder service ownership

- Symptom: integration review found cache/log directories still selected for
  actual-metadata copying despite fresh image service IDs.
- Cause: only mutable files were refused; owned directories remained in the
  copy namespace and could carry runtime ownership/ACLs.
- Correction: move these trees into explicit fresh-directory generation; apply
  APT's frozen sandbox UID/root-group directory policy.
- Verification: native UID 100 writes, UID 101 denial, fresh ACL isolation and
  seven pre-mutation refusals pass (ADR-0066). Full payload preflight still
  rejects the known shared Info index pending final H07 metadata closure.

The first directory probe tried to remove a nonempty minimal-runtime dev
directory. It now verifies and removes only its own console/null fixture nodes
before testing fresh full-root directories. No installed target path was changed.


### Nested image database copy released the outer POSIX lock

- Symptom: the native private Dpkg writer succeeded after an inner read-lock
  context ended although its outer context was still active.
- Cause: POSIX process locks are released when any descriptor for the locked
  inode is closed; each nested context had opened its own descriptor pair.
- Correction: reuse a process/database descriptor pair with reference-counted
  lifetime and check path identity without reopening.
- Verification: actual native writer exit 2 while nested, after inner exit and
  inner exception; exit 0 only after final release. A real native database copy
  nested in an outer transaction preserves both source locks. Full database
  copy checks pass and installed state is unchanged. See ADR-0059 for hashes.


### Berkeley DB repmgr007 asynchronous diagnostic and absent db_repsite

- Symptom: standard group 21 fails repmgr007 errchk (expected 1, got 0); group
  22 fails repmgr100 because db_repsite is absent.
- Causes: immediate log read races with the replication input thread; the
  multi-process helper source itself is absent from the published 5.3.28 tree.
- Correction verified so far: bounded repmgr007 diagnostic reread, preserving
  the original assertion, passes three complete native repetitions.
- Remaining: all other_repmgr cases and actual multi-process helper resolution.
  Enabling C++ alone failed on missing test/repmgr/db_repsite.cpp; do not repeat
  that approach or remove the group. Preserve the current suite's full result.
- Evidence: ADR-0067 records exact pre/postimage, original/corrected/compile logs
  and primary upstream/distribution source evidence. No runtime C code changed.


2026-11-07 — Prepared Berkeley DB recovery provenance omitted the newly frozen
repmgr007 patch from the package source list and excluded external C/Tcl files
from supporting recipe enumeration. Detected by reviewing the actual package
wrapper and provenance.py before any production installation. Corrected the
source list and supported input types; added a regression showing that C/Tcl
changes alter provenance independently of the shell wrapper. Existing accepted
records are preserved. The native helper itself remains pinned and test-only;
production staging now refuses its accidental inclusion.


2026-11-07 — The first parallel DB test view bind-mounted an ext4 directory
onto dev/shm. A mount audit identified the mismatch with the original tmpfs;
only that private process group was stopped (test exit -9, driver exit 1), with
all 10,208 input hashes unchanged and logs retained at db-standard-yc87i9pi.
Corrected setup mounts a private tmpfs before binding it. The first corrected
preflight refused because findmnt returned two stacked tmpfs rows; changed the
probe to native stat -f of the effective mount. Corrected preflight passed and
the fresh complete suite started at db-standard-nfv62s4o. The original full run
was not stopped or altered. See ADR-0069 for evidence and acceptance boundaries.


2026-11-07 — Prepared APT runtime sandbox gap (before native installation).
Symptom: HAVE_SECCOMP was required, but neither vendor nor fixture configuration
enabled APT::Sandbox::Seccomp. Cause: frozen APT 3.0.4 defaults that runtime flag
to false. Correction: explicitly enable it and require measured HTTPS worker
IDs/groups, zero capabilities, no_new_privs and an additional kernel filter.
Verification: eight native observer cases and the revised native TLS fixture
passed; actual APT execution is still gated on Berkeley DB. See ADR-0070.
