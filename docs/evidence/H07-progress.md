# H07 — In-progress final package evidence

Updated: 2026-11-06. H07 is NOT complete. Critical compiler/libc/binutils
results are recorded below; remaining base and package-manager closure are pending.
Appended entries supersede earlier running-state descriptions.

The first two final packages follow frozen LFS 13.1-systemd sections 8.3/8.4.
Their installs were redirected into DESTDIR staging, inspected for ownership
conflicts and archived as original native .debs before touching the target.
Builder dpkg is infrastructure; no Ubuntu/Debian binary package was imported.
Per-file payload hashes, modes, numeric ownership, recipe hash and frozen
source URLs/hashes are in /var/log/toddy/packages/. Component copyright and
license notices are retained in each installed package. No private data is
included. Native dpkg/APT source builds and signed repository remain pending.

| Step | Recipe/postcheck | Changed paths | Full log SHA-256 |
| --- | --- | ---: | --- |
| man-pages 6.18 | 0 / 0 | 3149 | 83a3821713a820119d6c6a82d0cad0d2e4fe38a2e9752d5a50741f836975435d |
| iana-etc 20260805 | 0 / 0 | 9 | c4232aac759363883ceb0f0bd3c5ae486d65566dd21c7945af7d21799373d51c |
| ownership rejection probe | 0 / 0 | 0 | 7ca5895a8304baa49b4daab6c8e2f8ff68eff4433f210837a5862a3cee33ae4e |

Actual database query reports man-pages 6.18-1 and iana-etc 20260805-1 both
install ok installed. The man page exists, IANA TCP/SSH records match expected
numbers, and /etc/services plus /etc/protocols belong to iana-etc. The latter
are registered conffiles. Archives stay at /var/cache/toddy/packages/.

A staged conflicting package attempted to own /usr/share/man/man2/open.2.
The ownership preflight identified man-pages as owner and rejected it before
building or installing the conflicting archive. Its manifest recorded zero
installed-path changes; the original file hash and owner remained unchanged.
No --force-overwrite was used.

Full local evidence: .local/logs/h07/. Recovery checkpoint before final base:
h06-ready. Security overlay and actual critical suite results must be recorded
before the final libc can be accepted. No G1 or release claim is made.

## Critical Glibc result and installed first base slice

Final Glibc 2.44 with selected stable patch completed its full critical suite:
6779 PASS, 16 XFAIL, 583 UNSUPPORTED, 1 FAIL. The sole failure is io/tst-lchmod,
documented by frozen LFS section 8.5 for chroot. Its output shows descriptor
path comparisons changing from /sources to /mnt/lfs/sources while retaining
the same device/inode. No unexplained failure was accepted. Raw suite exit 2
is preserved; it is not rewritten as a zero-exit suite.

Original summary, raw log, classification and all per-test outputs are copied
to .local/logs/h07-glibc-tests/. The 29 MiB per-test archive is also retained
in the target source evidence directory. Some UNSUPPORTED cases are normal
hardware/hugepage/optional-tool limitations. Container tests hit the documented
Linux CLONE_NEWUSER-in-chroot EPERM condition, confirmed by an outside/inside
comparison; a temporary job-specific AppArmor experiment was ineffective and
removed. No global sysctl changed. H12 must repeat container cases in the
actual booted native target before G1, retaining both original and new results.

Glibc native package installation passed after staging was canonicalized to
the book's merged-/usr aliases. Target C execution, libc linkage, no runtime
RPATH and localhost lookup passed. Locales, tzdata, Zlib, Bzip2 and Xz then
passed native package installation and postconditions. H07 remains incomplete:
final compiler/binutils suites and the remaining chapter 8 sequence are still
required. Current source-based archive/component metadata is outside Git.

## Additional verified native packages

The compression-library block completed with driver exit 0. All listed
recipes and runtime postchecks returned 0; Readline retry preserves its first
zero-change ownership failure and corrects shared Info index integration.

| Package | Full log SHA-256 |
| --- | --- |
| glibc-install | b2434919fbc875c67e9524bd348cb640b3f58b8624b47d5d1860b6a42580a18d |
| glibc-locales | c98edf508496d146d5ad90cbd814a54d2c7eaeca598fcc6c462edd43d8e5e58a |
| tzdata | 09829ff795b273a371ac1252b69c5a33489f8f0e8b96a991cfdc822868c0482f |
| zlib | c7ed8b369a5d39bd6e2f5bc80f07dc071f642f965e920af042bddbe81771f320 |
| bzip2 | f98a1d176ac908096889f118172a9312d5260957c83099dd49698187a994f897 |
| xz | 2f360e15c5427e3ee47321a8d7683422e99fc94264f0422f258016b0e6d29c08 |
| lz4 | 0a3c04bd1120068b0c9c6d26f2292bd0ccb59f3526aeb17467c3b7e8ddea3439 |
| zstd | 97da2d226acd26c5fd63617f4f1802d3c8c17136350dc8c775bba245c56a6e57 |
| file | a2e1d1cff336868b4c29677bc6568a7848e3ddfef505f69ddc8bc4de55d3c3a5 |
| readline | 7d8bee39e82683494a6491d7cc58126eedf093a77fdbd70ae6079790cf09aef5 |
| pcre2 | fc836450db42140e94a077c87ce6c7c42b44d3272a63a493ad919eeebd368b41 |

Readline's C API returned version 8.3; target Info located readline.info.
PCRE2 10.49 passed its full make check and UTF-8 property smoke test. Native
database currently contains 13 packages. The paired checkpoint h07-early-base
passed image consistency and copy SHA-256 verification with the VM off. It
is a partial-H07 recovery point, not a passed G1 or complete final base.

## Native test-tool prerequisites (2026-11-06)

M4 1.4.21, Bc 7.0.3 and Flex 2.6.4 passed native recipe and
postcondition checks. M4's first full suite exposed inherited ignored SIGINT
from detached execution, corrected in the runner and regression-tested without
changing package tests. Its clean retry produced 334 PASS, 48 SKIP, zero FAIL.
The original failure had zero installed changes and remains archived. Bc and
Flex full test output is retained with their successful build logs.

| Package | Full successful log SHA-256 |
| --- | --- |
| m4 | bbadb5da2e6d3de7eb237250f24b0849aecd3a0f8e728cd7dd5027099f475f29 |
| bc | e581021661a19ec76647fa8bcc83ecb894afe1cd05093d03278cd9972cd27c94 |

Local evidence copy: .local/logs/h07-test-tools/early-tools-and-history.tar.gz.
The copy includes original runner failure history. Tcl is still running;
Expect/DejaGNU/Ninja/Pkgconf recipes and the critical Binutils build recipe are
prepared but not yet verified. H07 and all release gates remain incomplete.

## Complete native test harness and Binutils build started

Tcl 8.6.18 core: 47159 total, 43704 passed, 3455 skipped, zero failed.
Bundled TDBC database-client tests are explicitly unavailable as classified
in ADR-0011; they are not claimed passed. Full stream/classification retained.
Expect's full suite has 29 PASS, zero skipped/failed; PTY spawn/runtime passed.
DejaGNU passed its make check. Ninja bootstrapped itself and built an actual
small graph; the frozen book notes its full suite requires CMake unavailable
at this stage. Pkgconf passed 32 tests, zero failed, and queried installed
Zlib/Xz metadata. All four package recipe/postchecks exited 0. The first
Expect transport error had zero changes and was corrected before retry.

| Package | Full successful log SHA-256 |
| --- | --- |
| flex | 4212656772c7ad7005a5f4a43a9519ab3cd9b5c9302ecaf2761cc2244c0cf9b9 |
| tcl | 57669c6cad2bdb4bc5f095d4b5b17439c848bcf69909a17e55d6d3f678336c80 |
| expect | 825f058f28ab60b2a529985d88f0316f366a589dda99b98d92b8defc143cbc47 |
| dejagnu | a54b07b89e7d5599805310eba9986d0deb439277a389e1a102d96e653544bd0f |
| ninja | 83ec4d21e502f0c2413cad52092d32eaffbd41c94a4995df84dbccdfecf7dfb7 |
| pkgconf | 4e3e5b5f8c00103da1b370a693816349290310b0d07515e0ec1046729df39862 |

Native package database now has 21 packages. Final Binutils 2.47 is building
from the frozen source with system Zlib and the book flags. Its mandatory
make -k check runs before installation; exact exit and .sum/.log archive are
retained for classification. It is not accepted or installed yet.

## Critical final Binutils accepted and installed

Frozen Binutils 2.47 completed mandatory make -k check with original exit 2:
351 binutils PASS, 2098 assembler PASS, 3304 linker PASS/59 XFAIL,
168 libsframe PASS, 40 libctf PASS, five gprofng PASS and three gprof PASS.
Only FAIL is gprofng tmpdir/gp-gmon, matching both frozen LFS 13.1-systemd
8.22 and the exact official x86_64 reference test log:
https://www.linuxfromscratch.org/lfs/build-logs/13.1/i7-14700K/test-logs/820-binutils-2.47
Reference SHA-256: 696419ce06c5a849c2724ff7d6c0a04456963ff4eb529fd4900e4b0013f16e78.
Unsupported/untested cases remain explicitly reported, not counted as passes.

Strict classification rejects missing/truncated suites, other FAIL/XPASS/
ERROR/UNRESOLVED cases and interrupted exits. Unit regression tests exercise
these rejections. Original build failed marker is preserved with zero changed
installed paths; separate classification accepts the documented outcome
without changing the original exit. Native installation is a separate step.
Its recipe and postcheck exited 0, including C execution and linker path audit.
Successful installation log SHA-256:
0be884559b193ee452c365f4eabe1bbdb9fbea4776986868b6b5c04413d46287.

Raw critical check log SHA-256:
efb867b05bcea9ac36e74d9255e1efca9a995802aacd8e2c1990eae291ca39c9.
All per-suite reports archive SHA-256:
4917bafd33c69b6b90e1b6f812057226c706e02a82633be97721d9282dfb493d.
A full evidence copy is in .local/logs/h07-binutils/evidence.tar.gz.
GMP/MPFR/MPC and the final compiler/base sequence remain required.

## Compiler mathematics libraries and cold checkpoint

GMP 6.3.0 completed the corrected >=199 PASS assertion after a full suite
repeat; generic --host=none-linux-gnu follows the book's portable-library
option. MPFR 4.2.2 passed all 198 tests; MPC 1.4.1 passed all 75 tests.
Each native package recipe and runtime metadata postcheck exited 0.

| Step | Successful full log SHA-256 |
| --- | --- |
| gmp-install | f91fa6a72cb180b15ca6a9c618319f076dc9e5ea81603d977cc945eb9e2322c1 |
| mpfr | 740139826e921d7b644d759c7ef723eb72c71a88881a627a838087d7b00c2b00 |
| mpc | 1535e82fb26373c6c94e58396b798fd4ad3be8567cef6e07fe08a2e6a33c895c |

Raw math suites/report archives copied to .local/logs/h07-math/suites.tar.gz.
The paired cold checkpoint h07-native-math passed disk consistency and copied
image SHA-256 verification, with QEMU off; its manifest is under
.local/vm/checkpoints. The VM restarted and pseudo filesystems remounted.
There are 25 native packages; Attr/ACL are now running, final GCC and all
remaining base/release acceptance still pending.

## Extended attributes, capabilities, password libraries and accounts

Attr 2.6.0 passed its suite and real ext4 user-attribute roundtrip. ACL 2.4.0
had 13 PASS, two XFAIL and the book-documented cp.run FAIL because temporary
Coreutils lacks ACL support; no other failure accepted. A file ACL granted
read access to the real unprivileged tester account, verified after dropping
UID/GID/groups. Repeat ACL-preserving copy after final Coreutils is built.

Libcap 2.78 passed make test plus actual setcap/getcap on a disposable target
file. Libxcrypt 4.5.2: 38 PASS, 14 SKIP, zero FAIL; native C Yescrypt hashing
passed without emitting password hashes. Shadow installed and configured
YESCRYPT with root locked. Its initial pwck found the missing volatile
/run/dbus directory; a separate audit verified the package unchanged and
passed after creating the essential account's runtime home. H08 must create
that directory at boot. No shared account credential is embedded.

Gawk 5.4.1 passed its complete suite as tester and actual arithmetic runtime
check. Native package count is 31. GCC 16.2.0 final build/critical suite is now
running under the accounts driver; no GCC install or acceptance is claimed.

| Step | Full successful log SHA-256 |
| --- | --- |
| attr | 19ce155e3d3b8ac70c84fcadead0d17a9a202ec3b782beba461e93529e698945 |
| acl | 8612bb48fa24f57b48b5f0c72294b3b677a79c72621767448c13b32dcbc45665 |
| libcap | b04c6384c606f53cfafbc359dcae01df90909b99ecf0d2e521403dd8e7a2992a |
| libxcrypt | c445a671446b2e9ea24b7fac3035fc00caa5989369138d56cf6c18f60277783b |
| shadow-audit | 9bdedf14c86b20b273dce36fe0d21e5d52fa5b1058eaa498fdad8abd15f3333d |
| gawk | 53915c81ab7e03fc6c7d586db6dcf418264c3bb9622c7370b7c42ec72e90b854 |

## Partial ELF audit and compiler source signature

A read-only actual-target audit inspected 445 ELFs in 31 native packages.
It found 20 references to still-unowned temporary C++/terminal providers and
eight missing direct dependency declarations across four consumer/provider
pairs: Bc -> Readline, Binutils -> Flex, Gawk -> Readline, Shadow -> ACL.
These are pending final native dependency updates; no closed runtime graph
is claimed. Glibc gconv's private $ORIGIN libraries resolve correctly and are
owned by Glibc. The auditor resolves absolute symlinks inside the target
namespace, not against builder /usr. Full output is retained at
.local/inventories/h07-native-elf-partial.json. Optional dlopen/tool/data/plugin
and version-policy checks remain separate obligations.

The unchanged GCC 16.2.0 source archive also passed gpgv signature verification
with the official GNU keyring obtained through its kernel.org mirror, signer
7F74F97C103468EE5D750B583AB00996FC26A641. Source hash/version did not change;
this additional authentication does not rerun unchanged compilation/tests.
Signature output is retained outside Git in .local/upstream-verification.

## Complete final GCC critical suite accepted (2026-11-06)

The guarded build/collection step ran 03:28:15–04:39:44 UTC and exited zero
for both recipe and postcheck, with zero installed changes. Independent strict
classification then accepted all six complete merged reports against the
hash-pinned official LFS 13.1 GCC 16.2.0 reference. No novel unexpected result
was accepted. Raw make exit zero is preserved, not described as all-pass.

| Suite | PASS | XFAIL | UNSUPPORTED | FAIL | XPASS |
| --- | --- | --- | --- | --- | --- |
| gcc | 218832 | 1569 | 3992 | 39 | 2 |
| g++ | 267590 | 2373 | 2023 | 33 | 0 |
| libatomic | 54 | 0 | 0 | 0 | 0 |
| libgomp | 6123 | 46 | 487 | 0 | 0 |
| libitm | 44 | 3 | 1 | 0 | 0 |
| libstdc++ | 18597 | 122 | 478 | 0 | 0 |

Total 511240 PASS. The 72 FAIL and two XPASS outcomes exactly match known
lines in the pinned official reference; zero unexplained outcomes. The C
suite has one additional PASS and one fewer FAIL than the reference:
gcc.target/i386/shift-gf2p8affine-2.c now passes on this target. This is not a
claim about support for any unmeasured CPU instruction set. All other suite
pass counts match the reference. Original parallel .sum.sep/.log.sep files
are archived in addition to the complete merged logs.

| Artifact | SHA-256 |
| --- | --- |
| full runner log | a9043fecbd7490ca284b76e18d498373b49ed3e1c91b217c81f72113a240f0cc |
| raw check.log | 32fc2c62803fcbd07ac4368595a8939cab87c44db6540eedf28ec7b157cb79d1 |
| merged reports archive | da2523dfb354130c3dfa5d6310b7b0de8fd302f41efba2e9801db5bff5fb04d6 |
| parallel raw reports | 5afd336d93a30d45ed9b8c0ba92db05330008d652ad5d12937f9f6439b6b2e73 |
| classification | 81920cfcc2063a5058512077299fa394c08ef2d754ed14daef64031194b78375 |

Evidence copies: .local/logs/h07-gcc/evidence.tar.gz and runner.tar.gz.
Reference URL/hash and minimum counts: config/compiler-test-reference.json.
The printed upstream mail-report script remains unexecuted data only.
Final GCC/runtime installation subsequently passed as recorded below; H07 is not complete.


## Final compiler installation and Ncurses (2026-11-06)

The h07-gcc-tested paired cold checkpoint passed SHA-256 and qemu image checks
before installation. Final GCC/runtime split installation then passed the
explicit h07-gcc-install-recovery recipe and postcheck (both zero), changing
1031 installed paths. Native C and threaded C++ executed; loader, startup files,
header ownership and search paths passed, with no temporary toolchain leakage.
The original failed attempt changed zero installed paths (missing staged
copyright); it is preserved, not reclassified as passed.

| Artifact | SHA-256 |
| --- | --- |
| GCC installation recovery log | 3e0f609c9ae65c79450c17e143c13f5560f303536333446273c00c7e7a9cbb61 |
| gcc-runtime native archive | 107013667956ccac7fdb840c7d62b24332da6e7ab74383ae6c1099358d296c60 |
| gcc native archive | 13bbd31ca0815748db0dc070e2b763ca242c97b5a6d0a1d23a7ba6f7cf050c29 |

Ncurses 6.6 staged documentation needed an explicit parent directory in an
empty DESTDIR. The original failed attempt changed zero installed paths.
Explicit stage recovery passed recipe/postcheck, including four upstream
standalone setupterm cases and native terminal output. Current 34 packages
include GCC/runtime and Ncurses. Sed onward is running; no later acceptance
is inferred. The native ELF/dependency graph still requires metadata repairs.


Sed 4.10 passed both test groups: 66 PASS/9 SKIP and 241 PASS/46 SKIP,
zero FAIL, then native substitution. Psmisc 23.7 reported 66/2/9 expected
passes across its three reports. Its first version-stream postcheck failed;
separate unchanged-package audit passed the corrected version and process/
signal checks. These bring the installed native count to 36. Compiler,
Ncurses, Sed and Psmisc records/logs are copied outside Git to
.local/logs/h07-native-compiler-install/records.tar.gz. Gettext onward is pending.

Recipes for frozen LFS 13.1-systemd sections 8.40–8.45 (Libtool, GDBM, Gperf,
Expat, Inetutils, Less) are prepared and syntax-checked, not yet accepted in
the target. Expat uses the explicitly frozen 2.10.0 security overlay from
ADR-0013. The native-tools driver requires final Bash success before starting.


## Post-Bash recipe preparation and Gettext acceptance

Gettext 1.0 passed make check with no FAIL/ERROR in its automake summaries,
then installation and a native PO -> MO -> PO translation round trip. Native
count is 37; Bison is running. Full Gettext nested .log/.trs reports were
collected after completion, in addition to check.log. Future recipes collect
them directly before staging; the running Bison recipe is preserved unchanged.

Frozen chapter 8 recipes through Meson are now prepared, syntax checked and
reviewed against their frozen book sections. These remain unvalidated until
actual guarded target execution. OpenSSL is the selected 4.0.3 overlay.
Python 3.14.10 source inspection still finds pre-OpenSSL-4 API/tests, so its
recipe verifies and dry-runs the frozen book compatibility patch with zero
fuzz before applying. Full Python tests remain mandatory. Optional 3.14.7 HTML
docs are not presented as 3.14.10 docs. SQLite's autoconf distribution has no
suite per section 8.52; its postcheck exercises persistent transactions,
FTS5, integrity and no rpath. Python packaging wheels build/install offline
from frozen sources. Libffi's explicit generic-CPU choice is ADR-0015.


Bison, Grep and the two legacy-encoding test locales passed recipe/postcheck,
bringing the native count to 40. Bash initial full suite was rejected before
installation; all 86 groups were visited but ten diff lines needed diagnosis.
The FD-isolation experiment and exact official-reference classification are
ADR-0016. The complete corrected suite is running; Bash is not yet accepted.
The pinned official reference is fetched as data by fetch_bash_reference.py;
sync_build verifies its hash and transfers it before target use. Regression
checks now total 36 tests. New system-utility recipes through Texinfo are
prepared and syntax-checked, not claimed validated. Kmod/GRUB native boot and
module acceptance remain H09 obligations; their chapter-8 build checks do not
substitute for boot. Full source-known Groff/Tar test failures, if observed,
will stop the driver for diagnosis rather than be suppressed.


## Bash corrected-suite and native acceptance (2026-11-06)

The full corrected PTY retry completed all 86 groups once each, with zero
unknown differences and zero fatal diagnostics. Seven diff lines remain,
exactly the two qualified groups in ADR-0016; this is not an all-pass suite.
The descriptor-related differences disappeared without editing tests. Final
Bash packaging/installation and native arithmetic/process-substitution checks
passed. A separate unchanged-package audit verified finite-precision printf
and actual SIGUSR1 trap delivery; recipe/postcheck zero and zero installed
changes. Current native count is 41; Libtool-through-Meson driver is running.

| Artifact | SHA-256 |
| --- | --- |
| Bash full recovery/install log | 06330fdde572f3c0367eaafe8bdc1f449baf21bad0d98fd0d898e58eb4897088 |
| Bash native .deb | 46f38ed4aa6fd9069c61f8187d1ed200712636b918495d53be4210366109edd0 |
| Separate native semantics audit log | 1b2e540e34c5f9f4f5874742e075c475d89388a56c2a9515589c17e97cfbfb5c |

Bison's suite reports 712 successful/64 skipped cases plus 13 passing unit
tests. Grep reports no FAIL/ERROR across its complete suites. Original and
corrected Bash reports, focused probes, reference, classification, nested
Gettext/Bison/Grep reports and terminal runner records are copied to
.local/logs/h07-post-compiler/evidence.tar.gz. Original rejected Bash record is
preserved; h07-bash-recovery.success.json is the separate installed acceptance.


## Native tools through Perl and recovery cache

Libtool, GDBM, Gperf, Expat 2.10.0, Inetutils, Less and Perl passed their
applicable full suites and native postconditions. Libtool reports 148 expected
outcomes/39 skips plus a 4 PASS/2 SKIP gnulib group; this includes upstream
expected failures, not 148 unconditional passes. GDBM reports all 38 successful.
The Gperf caller-header fixture was corrected and verified through an explicit
unchanged-package audit (docs/errors.md). Expat rejects malformed XML; its
unfixed upstream exposure from ADR-0013 remains an open release consideration.
Inetutils successfully queried loopback and exchanged an actual ICMP echo in
the disposable guest. This is not a target boot/network-configuration claim.

Perl 5.44.0 reports All tests successful: 2942 files, 1392301 tests. Native
compression/GDBM modules, shared libperl and thread configuration passed.
Current native count is 48; Autoconf onward is running.

The read-only host collector verified and copied 47 prior installed native
archives plus their full component records to
.local/native-package-snapshots/20261106T053457533866Z. Both guest source/
notice/archive checks and independent copied-byte hashes passed. Inventory
SHA-256 da71b23c4015f130dd5a8a5afd3d1969fd0d497bd6c9421344a2e7a525427ecc;
cache archive SHA-256 5ba7e3aed78364aa2806382f2da172ea08882cf0bf798d4daa3f48528d15249a.
This is a partial package recovery cache, not a bootable checkpoint or a
completed dependency/license audit. Perl was installed after that snapshot.

ADR-0017 freezes five verified CMake support inputs for later native package-
manager work. Known-vulnerable old Curl/Libarchive book candidates are not
selected; no support library was built or silently substituted in this run.


## Native crypto/FFI base and Python source recovery

Autoconf and Automake full suites and actual generated configure/distribution
projects passed. OpenSSL 4.0.3's complete configured suite reports All tests
successful, 368 files/4413 tests; native SHA-256 and entropy API execution passed.
Libelf's final test group reports 251 PASS/9 SKIP/zero FAIL/ERROR, and its native
ELF-reading C program passed. Generic Libffi reports 2564 expected passes and
its actual ffi_call add(20,22) returned 42. SQLite persisted an FTS5 transaction,
passed integrity_check and had no rpath. Mpdecimal's local suite and native
exact 0.1 + 0.2 == 0.3 probe passed. Current installed native count: 55.

Python's initial dry-run failed before compilation with zero installed changes.
ADR-0018 records the controlled context-only adaptation and complete test-
preservation proof. Derived patch is published at immutable commit
f54be82efbf8d9b9765f1859d4b38651536594fe, hash-pinned as a supplemental source.
The Python/OpenSSL source versions are unchanged; full native tests remain next.

A verified 55-package cache is at
.local/native-package-snapshots/20261106T055826657515Z. Inventory SHA-256
9980e36d760435e34aec6909d2a8600f82e910a48cff4ddcd029a3084514c983;
cache archive SHA-256 7630224b9adb8d8500e76ad463edfae0e8a60ed7ffb0108370da36f81a30a5b9.
Current raw runner/nested reports are additionally copied to
.local/logs/h07-native-tools-55.tar.gz. Actual active OpenSSL recipe inputs,
including then-uncommitted diagnostic helpers, were captured in
.local/logs/h07-inputs-482560f.tar.gz; its recipe-set hash exactly matched the
running record, 197ba9d27a767b04e0e89e7baf4a0bf797d3bb379db8b8661b6334f477d228f2.
Its archive SHA-256 is 00a7ffc9fed95ad2ae4b2b2b2678a117749ca48eac5be0e40c243334ebe57fa0.
Guest-only diagnostics were preserved outside the recipe search path after all
jobs stopped. A new cold checkpoint is being prepared, not yet claimed saved.

Vim/MarkupSafe/Jinja2 recipes are prepared, not target-accepted. Vim retains
all upstream tests; unlike the book's downloader-test exclusion, a missing
prerequisite will stop for investigation. No unavailable plugin test is silently
removed. The remaining service/filesystem/native package-manager recipes and
all release gates remain incomplete.


The h07-native-crypto cold paired checkpoint has now passed both SHA-256 copy
comparisons and qemu image checks; save exit 0 is retained in
.local/logs/h07-native-crypto-checkpoint.{log,exit}. VM restart/remount and full
input sync passed. Python recovery verified all original archived source bytes
and applied the complete adapted series before starting its PGO build/full
standard suite. Test parallelism is explicitly capped at eight with the book's
120-second timeout; no test selection changes. A durable gated continuation
waits for its dispatcher, requires actual success, then continues through
Meson and the utility driver. Python remains unaccepted while running.


## Native continuation through Findutils: 65 accepted packages

The full Python retry reported Result SUCCESS, 48,840 tests with 2,159 skips;
these are reported totals, not 48,840 unconditional passes. The first run had
only two networking failures because the target lacked /etc/resolv.conf. A
guarded build-only resolver step uses the existing QEMU uplink 10.0.2.3, verifies
native resolution and a real HTTP 404, then repeats the entire compiled PGO
suite with unchanged selection and timeout. Original failed logs are retained.
H08 must replace this temporary resolver with runtime network configuration.
Native Python/SSL/SQLite/Expat/FFI/compression/GDBM/curses/readline imports and
pip 26.2.2 passed. Flit-Core, Packaging, Wheel, Setuptools and Meson were built
from frozen inputs offline; a real Meson/Ninja C project passed. Kmod built and
read the builder kernel's module list; target-kernel load/unload remains H09/H12.

Coreutils' patch required balanced context (ADR-0019), with zero-fuzz result
byte-identical to the book-default patch result. Root and complete tester suites
with RUN_EXPENSIVE_TESTS=yes passed, followed by native copy/ACL/hash checks.
Diffutils full tests and native equal/different comparisons passed. Findutils'
initial Greek regex failure was corrected by selecting its supplied fixed
Gnulib implementation (ADR-0020); the full suite and native sigma regression
passed. This does not globally repair Glibc bug 20381.

| Accepted runner | Recipe/postcheck | Full log SHA-256 |
| --- | --- | --- |
| h07-python-test-recovery | 0 / 0 | 007793e1da383398e96de6bc0515cc9dd25458d161b082e1ee06539714d91827 |
| h07-coreutils-recovery | 0 / 0 | e4e481c19e9f6bd75ae59703740f48a50bbf79ff04aea195a011e3e6f4b35452 |

Native archive SHA-256: Python
ffb2baa6df3defc9122b3c7e35316afe2156fffab44f2f7ded2fdbbb51f3ad64;
Coreutils 0d7fe0ed7a6d8bca6a3a1f859ba42b128ecfc1da672ff597248db1c982849410;
Diffutils 093d20e6c74fd86aee3844d063f311032429720bc708f919f0febbab696e967b;
Findutils 256fb4d2488d1e00fada09b2c5453a16c8214bf82469b4dcb972851401353eb8.

The initial Groff suite stopped with only neqn-smoke-test failing because its
wrapper could not find newly built eqn in PATH. No installed files changed.
The focused probe succeeds with the build directory in PATH. Full-suite retry
preserves the first logs; acceptance still requires its actual result and
native formatter postcheck.

Input transfer now shares the dispatcher's exclusive build lock, validates a
complete per-file hashed staging bundle, and blocks dispatch after interrupted
installation. Tests cover busy locks, incomplete transfers, hash corruption,
source escape and symlinks. Actual guest probes verified both refusal paths;
39 local regression tests pass. No active recipe is overwritten during sync.


## Utilities through Patch: 73 accepted native packages

Groff full retry: 316 total, 298 PASS, 14 SKIP, four XFAIL, zero FAIL/ERROR.
Native formatter passed. GRUB built both i386-pc and x86_64-efi modules and
successfully generated both core images; grub-file recognized the EFI image.
No boot sector was written and actual BIOS/UEFI boot remains H09/H12. Gzip,
IPRoute2, Kbd, Libpipeline, Make and Patch passed their applicable native checks.
Kbd's original strict patch preflight stopped before configuration; ADR-0022
refreshes only two stale context lines and proves all 1327 postimage files
identical to book-default application. Full Kbd suite/parser passed afterward.

| Accepted runner | Recipe/postcheck | Full log SHA-256 |
| --- | --- | --- |
| h07-groff-recovery | 0 / 0 | feb7e15828ad20ac45f8db4d3ed9378d992bfca5fe53d3cc30af39e2e0bfe612 |
| h07-grub | 0 / 0 | 9ae027b98844627994653f07f569620b980ba942072f612f87577b704c2e204a |
| h07-gzip | 0 / 0 | 8232451bb0189357c04441418dd194e072d09d0060fd8dfed555984a1c1f17a4 |
| h07-iproute2 | 0 / 0 | 14eb58b103d5cab53640c3cb86709f40c18881a5649242db4db3c9b1663e5940 |

The 65-package cache .local/native-package-snapshots/20261106T073446126113Z
passed exporter and copied archive/record hashes. Inventory SHA-256:
603310729c7840d416e4a3fafe79a0b5cf3d7ad0ab3e7f7aefa55b9b6e350849;
cache SHA-256 68f89f0ea41be7bc6fe3cdeb936ca37f5007a0941bc7d128f3acdb28c3a4c39e.
The additional runner/nested log copy .local/logs/h07-native-through-groff.tar.gz
has SHA-256 0bb39dc9311088149d799b45967b03fb26fa118cac4fbe48c6fe9d967170c4fd.
These recovery ingredients are not a bootable checkpoint or ISO.

Tar's unchanged full suite is 223 PASS/20 SKIP/one known display mismatch,
raw make exit 2, zero installed changes (ADR-0023). The compiled binary preserved
exact security.capability bytes in an independent guarded probe. Acceptance
still requires strict complete-suite classification and installed ACL/capability
roundtrips. No test is deleted or relabeled passing.

Systemd/D-Bus/Man-DB/Procps/util-linux/E2fsprogs and supplemental dependency
recipes are prepared, not yet accepted. ADR-0021 freezes public CA data; Curl's
initial profile explicitly disables cookies without Libpsl. Vim's unchanged full
downloader tests are scheduled after native TLS/client prerequisites. Final
ownership, conffile, runtime-dependency and license-expression closure is pending.


## Final services and TLS client: 86 accepted native packages

Tar's strict full-suite classification accepted only the measured getcap display
difference. Installed ACL copy/read and exact security.capability byte roundtrips
passed; original raw make exit remains 2. Texinfo, MarkupSafe and Jinja2 native
checks passed. Systemd's complete UTF-8 suite is 1828 OK/33 SKIP/one book-known
chroot namespace FAIL (ADR-0025); raw ninja exit 1 is retained. Initial five-fail
POSIX report and the four-test focused locale correction are preserved. A
collector path error stopped the first retry before staging; the corrected
complete retry and classification passed before installation. Installed version,
init link, udev tool and escaping checks passed. No native boot is claimed.
H12 must rerun the exact namespace case under the native booted OS before G1.

D-Bus's full configured suite and an actual ListNames call through dbus-run-session
passed. Man-DB formatted a real native manual; Procps full tester suite and
process/memory queries passed. Util-linux's complete unprivileged suite and
native mount-info/UUID probes passed. Root device tests were not run. E2fsprogs'
393-success/one-known allocation mismatch retains raw make exit 2 (ADR-0027).
Installed default ext4 creation/check/mount/write/unmount/recheck/remount proved
persistent exact data inside a disposable regular-file filesystem; cleanup
removed only its own fixture. Installer use of unproven prezeroed optimization
is forbidden. Actual installed-disk/ISO boot remains untested.

The frozen public CA package verifies its source SHA, parses all 118 certificates
and loads them with Python's default SSL context. Nghttp2's suite/native API
passed. Curl considered 2138 tests and reported 1597/1597 OK; unavailable-feature
cases remain unclaimed, including cases needing an HTTP/2 server absent from the
lib-only Nghttp2 build. Installed Curl verified real HTTPS and rejected the
self-signed endpoint with exit 60. HTTP2 compiled capability is not a claim that
all end-to-end HTTP/2 server tests ran. Cookie support is explicitly disabled in
this initial build-client profile (ADR-0021).

| Accepted runner | Recipe/postcheck | Full log SHA-256 |
| --- | --- | --- |
| h07-tar-recovery | 0 / 0 | 8565dcd89ad54245c1aaeb7ae972fbbedb69f1fceabc7fdcafadbad361bfc546 |
| h07-texinfo | 0 / 0 | bf404275e45e74697124176e379104ad25b693e64da2a5c2d78765c984c983f5 |
| h07-systemd-recovery | 0 / 0 | a7e88dc525ee58d596e04ac4c3dc8c1027165773e88350d806313d7c42081cac |
| h07-dbus | 0 / 0 | 71259bdfdb8e94dbfaf3b3a3296761a40ffd108f05f832724094c1c621421b9e |
| h07-man-db | 0 / 0 | 1e07961aaaff3967bb9014071ca9049a4d2992830b0b1aa70b56944f9a9a2dfd |
| h07-procps-ng | 0 / 0 | 8b416c64d349154f4d9eb4147d72972c7bf5b5d1535e84ca7533d0e6f43fa106 |
| h07-util-linux | 0 / 0 | e84d7fe00ef3f938ee4ab0ab2b93d46e87b5d64891e599854956b571b036b9e1 |
| h07-e2fsprogs-recovery | 0 / 0 | c4b3e4acb8f085fef646fcb9227ec8c114b2951eae2c47e7128b51cbd84c60f8 |
| h07-ca-certificates | 0 / 0 | 354fd70b3bc09b2af7d945d182cc0125df7a2473b25de1c00a60eb64aff298a8 |
| h07-nghttp2 | 0 / 0 | 75bc4270e8e0aaf6ae9f0195cd68b6bb832213459924da620c6c3983e58d8f3f |
| h07-curl | 0 / 0 | 189f06fd8cdb8a826e9b4876b6ebb4bd6d9e1f8cdee39d711c1cf98593061ebe |

86-package cache: .local/native-package-snapshots/20261106T081438374341Z.
Inventory SHA-256 87d1bdd5311848905db42ffac7d4f099208a83835264939e62c6847cbdae67e2;
cache SHA-256 285a26fb43142e8d48b62304b31cf5d960ae25f71066b9252016b9aa13daa96f.
Raw runner/nested evidence .local/logs/h07-native-services-86.tar.gz SHA-256
26e16f61e40d2e2e9fe4a49ae50e31f49dd65b71d20db563bb7281988e2b1d05.
Both are verified copies, not bootable checkpoints. A cold pair is being saved.

The old orchestration shell was stopped at the completed Curl boundary; no
build/test was interrupted. Frozen signing inputs/recipes were then synced under
the exclusive build lock. The fresh supplemental driver skips accepted packages
and runs Libuv/Libarchive/CMake, package-manager prerequisites and authenticated
GnuPG support next. It refuses Vim before frozen GLVS downloader inputs exist;
no mutable third-party plugin may execute before source verification. All Vim
tests remain required. Fifty local regression tests pass. Final native dpkg/APT,
ownership/conffile/dependency/license closure and all release gates are pending.


The h07-native-services cold paired checkpoint now passed both image checks and
source/copy SHA comparisons, exit 0. Manifest is
.local/vm/checkpoints/h07-native-services.json. Builder hash
04f0d30eaf79e029948feae68255b20c3cab9a79dd4d67756af5128d6de44519;
target hash 536109a5db3f6f2c44620c33f954fc2ce96570636c9a6b33bbc1b708e57785fd.
It contains the 86-package accepted boundary and prepared supplemental recipes.
It has not been restored; the earlier H06 pair remains the demonstrated restore.
VM restart/remount/sync is the next operation, not an ISO/native OS boot claim.


## Native build support through Libmd: 90 accepted packages

After checkpoint restart/remount/sync, Libuv's initial complete 507-case suite
failed only both copyfile variants because archived fixtures retained root GID
while tester's copies used GID 101. The whole build/test tree was corrected to
tester:tester; source/tests were unchanged. Complete retry and native loop/API
passed. Seven platform/environment skips are retained (Windows-only cases,
recursive watching, root-only identity case and absent controlling TTY).
Libarchive full unprivileged suite and Zstd archive/extract comparison passed.
CMake full suite reports 674/674 passing, followed by installed CMake/Ninja C
configure/build/ctest. No GPU/compiler feature is claimed from test labels that
internally check unsupported configurations. Libmd full suite and native MD5
abc vector passed. Native dependency/license closure still remains open.

| Accepted runner | Recipe/postcheck | Full log SHA-256 |
| --- | --- | --- |
| h07-libuv-recovery | 0 / 0 | fb444a9db5ab4f56fdbd2f7ac76ca61b90bb7dfc0d8bd96cb1857eefefaa5afd |
| h07-libarchive | 0 / 0 | 2ebef9503817bb523e1b1d6cab15f46ae65e28a926f4350524fa264cd200b660 |
| h07-cmake | 0 / 0 | 05480e309ed0e468cbdb0b6cc0312fa172ad9d4803f7fab5c95982dffcb36d61 |
| h07-libmd | 0 / 0 | 96f17ffdee919117e730cd4755be9033b4e85cc39df70a6899c19a9189fbe733 |

XXHash's full tool target stopped for absent external GNU Time, zero installed
changes. ADR-0029 freezes authenticated book Time 1.10 and requires its full
check/native exit-format tests, original-source identity check and complete
XXHash retry. XXHash remains unaccepted while that driver runs.

ADR-0028 freezes all four actual Vim GLVS plugin-version inputs. The prepared
test-only download guard uses actual native HTTPS, validates live metadata's
frozen source ID/name, and verifies exact executable bytes before exposure.
No upstream Vim test/source/assertion is modified. Host regression checks also
accept the captured actual metadata/plugin bytes and reject new versions,
corruption and metadata modelines. Native guarded preflight/full suite remain
pending; all test-only payloads are excluded from the runtime image.

Berkeley DB source-only patch probe applied all 19 frozen Debian patches with
zero fuzz in independently verified host-side extractions; no source code was
executed/installed there. .local/probes/db53-patch-series/verification.json and
per-patch logs retain the result. Native builds/tests remain pending.


## Native signing and full Vim acceptance: 100 packages

Time 1.10 full check: 9 PASS/1 SKIP/zero FAIL; native exit-format probe passed.
XXHash unchanged full suite passed after adding that missing tool. GoogleTest:
63/63 passed. Libgpg-error, Libgcrypt, Libassuan, Libksba and nPth full configured
suites and native installed API probes passed.

GnuPG initially failed unconditional CMS setup with Gpgsm disabled. ADR-0030
enables the local component with existing frozen libraries; source bytes were
verified and complete unchanged suite passed. Native Ed25519 generation/signing,
gpgv verification and tampered-message rejection passed in a private temporary
key home, removed afterwards. No online keyserver/CRL acceptance is claimed.
Recipe/postcheck 0/0, log SHA-256
52d3f85aa9fcdea0f19dcc58a99df8095f8e42070c299e3a8b017f5b322cdcfd.

ADR-0031 records Vim input/PTY and inherited SHELL environment failures, plus
focused real-test confirmation. Full unfiltered PTY retry with SHELL=/bin/bash:
8014 executed, 200 skipped, zero failed; every planned NEW_TESTS_RES exists.
Syntax tests: 293 OK/zero failed/skipped. All four unchanged downloader tests
used real native TLS and verified frozen plugins as nonroot. Installed native
Vim passed. Recipe/postcheck 0/0, log SHA-256
89c8f47ac4f19aec2b73bf99b181dc1c9f1105cde710ac383eeb76aa31bceedf;
archive 87408d33c9f15a96782b14b84161b72bbcee054254f68231357271c4d509469c.

Verified 100-package cache: .local/native-package-snapshots/20261106T101602370604Z;
inventory SHA-256 051743282474842a3b4181b8764f1b00e862a11ae14750972be4c3a5c02e7f83,
archive bfde27f0c8117087906e8ee855283b4bf517d43cb99389a6f624aafb525b9598.
Raw runner/nested reports: .local/logs/h07-native-support-100.tar.gz SHA-256
0921173c1c50901a06611d43157b92084f0e1df1ce2c37b379fa1e2ea9d726e8.
This cache is not a new cold checkpoint or ISO. Native package managers and final
ownership/dependency/conffile/license closure remain required; H07/G1 incomplete.


## Native Dpkg acceptance and closure audit: 101 packages

Dpkg 1.22.22 full configured check and native package build/install/query,
conffile-preserving upgrade, ownership conflict rejection, removal/purge passed.
The four reported Perl test groups contain 3991, 712, 12815 and 277 tests;
raw reports retained. Main target database hash was unchanged by disposable
postcheck operations. Log SHA-256
cc609c7462e4b56102228abee78df0aa905cf4622bd1b142771f8769590b65c1.

Berkeley DB's initial test configuration needed DBM/compat185 for unconditional
Tcl test bindings. Next link exposed maintained symbol generator's reliance on
static .o files. Both failures changed zero installed paths; trees/logs retained.
Corrected fresh build passed C tests and is running complete standard Tcl suite.
Production disables compatibility interfaces and excludes .a/.la staging.
ADR-0032 records causes/corrections; no DB acceptance claimed while tests run.

Read-only native audit inspected 2551 ELFs in 101 packages, finding 135 missing
metadata provider declarations and one private Systemd execution context. Actual
native loader resolves both Systemd private libraries; details in ADR-0036.
Ownership audit found 2026 unowned files/links, zero duplicate owners. Prepared
931-path exact quarantine covers obsolete cross-triplet/Python/Xz remnants;
Linux API headers, layout and generated state remain separate closure work.
No cleanup or metadata upgrade is claimed executed yet. ADR-0033/0034 freezes
native APT test/build additions; ADR-0035 prepares native packaging transition.
61 local tests pass. Published checks for 762dd6b are green; H07/G1/G2 pending.


### Prepared metadata/layout and legal-notice retention

63 local tests now pass. Native metadata upgrader prepares new +toddy1 archives,
conffiles, exact measured provider additions, consistent .la removal and shared
Info-index regeneration. Filesystem-layout/LFS build-support and Linux API header
recipes are prepared with book-source hashes and native probes. Quarantine and
upgrades have not run; BDB complete suite still owns the dispatcher lock.
Source legal-notice inventory examined 149 frozen inputs and identified 680
named/COPYING-numbered/LICENSES-directory files; inventory SHA-256
ab117f0dbeee1c2a902451f2c8f3ab2e57b75fd6eadbea0cf40a18c0a7cb511a,
.local/legal/source-notices/inventory-ab117f0dbeee1c2a902451f2c8f3ab2e57b75fd6eadbea0cf40a18c0a7cb511a.json. New packager retains exact notice
bytes and source/path/hash index; this is evidence for, not completion of,
embedded per-file and bundled-component license review. No release gate changed.


### Read-only native text-consumer probes

ADR-0037 records 18 actual probes: all eight English/Portuguese cases pass;
three default Greek cases fail (Gawk UTF-8/single-byte and Bash single-byte).
Explicit existing Gawk GNU matcher passes both Greek encodings. Report retains
all_cases_pass=false and exact failures; no global engine/source change or full
locale correctness is claimed. The report SHA-256 is
3e7546e1ecb70d9616b35b7d54aeb9e905b2016874146c19113f434f4a5efdb4.
Native boot repetition and remaining consumer review remain required before G1.


Verified 101-package recovery cache:
.local/native-package-snapshots/20261106T104331341467Z, inventory SHA-256
00b1e1f3709eef2c19ad0b55c5b39b14cb1d6a93514ab9ce2344686306890380,
archive fcc82a8eb9abc23fe59c9000151fbce2686a79f1c1ace365729f6483eebf7f29.
This includes accepted Dpkg but remains a cache, not a bootable checkpoint.
Native CMakeCache confirms system libraries enabled except the explicitly
bundled JsonCpp/cppdap/librhash (KWSys/KWIML also embedded); their actual notice
terms were reviewed and recorded in config/component-licenses.json. JsonCpp's
explicit MIT option is selected. The inventory exporter now exposes reviewed
licenses/bundles, source kind, book provenance and packaging backend rather than
marking even reviewed entries generically pending. Unreviewed packages still
remain pending; no full license closure or native backend acceptance is claimed.


Read-only native payload audit checked 58815 recorded regular/link entries:
zero missing files, zero duplicate owners, no modified registered conffiles.
The sole hash difference is Glibc's initial /usr/share/info/dir, already classified
as shared generated state in ADR-0008. Prepared metadata upgrade removes that
historical ownership and rebuilds the complete Info index; final postcheck must
have zero unexplained payload findings. Audit SHA-256 d0cd3d60bf6f4f67d89a177a79b47221a95dcf8448d833cd9496dfe1f7ac4f9a,
.local/logs/h07-native-payload-101.json. No upgrade execution claimed yet.


### Build ownership correction prepared

Archived/installed native metadata shows four unintended tester-owned CMake
Licenses entries (three files plus directory), versus intended DBus root:18 and
wall root:5 identities. ADR-0039 preserves the exact 16 accepted privileged
helpers and normalizes only unprivileged build-owned payload in staging.
Unexpected helper/mode/identity or build-owned setuid/setgid stops before install.
67 local checks pass, including escalation-refusal and exact helper-preservation
tests. CMake correction will occur in the versioned upgrade; none is claimed
applied while the unchanged BDB standard suite remains active.


### Source grant/bundle and executable-interpreter review

All 101 currently installed component names now have identified upstream grant/
license-collection entries; mixed/per-file terms remain original, not relicensed.
Actual Python-bundled pip vendor pins/notices and CMake selected bundles are
recorded (ADR-0038). Expanded source scan includes ARTISTIC, LICENSING, nested
wheel notices and selected original BSD algorithm headers. Older 670/680-entry
inventories were reproduced from their committed scanner versions with identical
hashes and preserved under content-addressed filenames; current scan remains
incomplete as a release audit until native notice/image/source distribution checks.

Read-only interpreter audit measured 380 provider edges and 275 missing metadata/
interpreter findings. ADR-0040 resolves actual unversioned Python/C-shell needs
without dropping executable paths; staged native fixes and final zero-finding
checks are prepared. No correction/native Tcsh acceptance claimed yet. Seventy
local checks pass after updating the isolated traversal fixture for the new
explicit license-policy input; actual unsafe-path rejection remains tested.


Expanded legal-notice scan before Tcsh addition: 149 frozen inputs, 878 candidate
texts/selected source comment blocks; inventory SHA-256
c4df32691dc57548b0fc898ae978908f810b8fa1a77fab4cce3412013591c11c,
.local/legal/source-notices/inventory-c4df32691dc57548b0fc898ae978908f810b8fa1a77fab4cce3412013591c11c.json.
Full LICENSING/README.licensing and selected BSD algorithm headers preserve
conditions that a general LGPL/MIT label alone cannot represent. Final release
source availability and actual installed notice verification remain required.


Read-only unowned-file classification before corrections: 1968 unexplained
paths, 54 explicit generated-state paths and four bootstrap configurations
reserved for H08. All unexplained paths are the exact planned 931-file
quarantine, native Linux API headers, config.site and owned filesystem aliases;
no extra unexplained namespace was found. Raw classification SHA-256 321e8c7b1f92f018f53cc8954b752de05fdb16b6de79f2f1781f13893f77b13f,
.local/logs/h07-unowned-classification-before.json. Prepared final check requires
zero unexplained paths after actual package upgrades; generated/H08 state remains
visible and is not falsely counted as package-owned. Filesystem layout also owns
book mtab and var/run/var/lock aliases; no mounted API filesystem is packaged.


## Triehash recovery and Which acceptance

Triehash repeated all seven original upstream tests and HTML coverage generation
(96.1% total). Corrected filename-based native generated C lookup/rejection
passed; same-step runner recipe/postcheck 0/0, zero installed changes. Original
failed postcheck evidence remains in runner history. Success marker SHA-256
12a9f81fc4eb91d6a459f2a9239ea4528a8c4e7a75cbd32a1a758ee0ff2a3766;
log SHA-256 d1340753ff8b440f75766be2451a79121030494e0e8c6122d4c70317a5c1b921.

Which 2.25 was compiled/installed with native Dpkg and its actual Bash lookup
and version passed. Frozen BLFS 13.1 general/which.html states no upstream
test suite; make check is not advertised as upstream coverage. Archive SHA-256
977f057cff28e0357c904de84ee1baccda8bba5827a9a892fd1a0c78f880b7f6.
Runner recipe/postcheck 0/0; log SHA-256
87ae3c2336a77b4143ed77dd8eba0a8d4a1b4fbed9db6a9800b35c69099db014.
119 accepted packages; H07 remains incomplete. Summary outside Git:
.local/logs/h07-native-support-recovery-summary.jsonl.


## Remaining native support accepted

Libseccomp 2.6.1: standard suite reports 7928 passed, 86 skipped, zero failed/
errored; skips retain absent optional Valgrind and default explicitly opt-in
live cases. Native compiled postcheck actually denies getppid with EPERM while
allowing getpid on the builder kernel. No Toddy kernel coverage is claimed.
Archive SHA-256 d1fc165127990dd8284204dcfc88c24ad292c5b1613c962e738608d92cf974c7;
runner recipe/postcheck 0/0, log SHA-256
edf5af4c2ab8e08d9fc05ad6c25e1ef49c48a34c55575d5657eea3e865c84373.

Tcsh 6.24.16 unchanged suite: 196 successful, 53 skipped. Native csh alias,
array/loop and subprocess-exit propagation passed. Archive SHA-256
1f810b41ab98e3f4c642ad25cba3a04d3a343387e9f31f22ef265e1a9a3710df;
runner recipe/postcheck 0/0, log SHA-256
c7a96221bc10e10562696e95877d6c0144c3bc1c2739451a257e822ab7be0622.
Frozen BLFS 13.1 general/libseccomp.html and postlfs/tcsh.html were reread
before this sequence. Support driver exit 0. Total 121 accepted packages;
BDB/APT, final ownership/dependency closure and H07 completion still pending.


Updated source-notice inventory: 151 frozen inputs, 880 named/header/embedded
notice candidates; SHA-256
5f0d3737b1ec07840cbf190418fc74cb74b4135176fce42e92c9724f995a4865.
Content-addressed inventory under .local/legal/source-notices; older versions
remain preserved. The test-only project patch is a non-tar frozen input; this
inventory does not grant new rights or replace final legal/source review.


## Independent ownership and full ACL retest

ACL full suite now has 14 PASS and two NFS expected failures, including
cp.trs PASS with final Coreutils; runner 0/0, zero installed changes, log SHA-256
be6e6d0ac1dea3b6b4c928a0f7d8b9e6f244089b32787ccd143c4fb26b312c59.
Linux API 7.1.8 headers are natively owned; compiled version/openat2/seccomp
probe passed. Runner 0/0, log SHA-256
550096f25c27d2ca3c5e0f82e167a471e6320cfcce5d5e3f1bb1c3b8040b2f6b.
Filesystem layout 13.1 native package owns merged aliases, shell/loader and
mtab/run links; actual shell and Bash loader resolution passed. Runner 0/0,
log SHA-256 a1c1235183b216273df3131e246d29249a027e791b98b15dac3de51cb64ea0f6.

123 accepted packages; lfs-build-support installed but failed postcheck and
is excluded from this count. ADR-0044 records the frozen Glibc patch-49
interaction; corrected package/retest acceptance pending. Raw summary:
.local/logs/h07-ownership-before-spawn-correction.jsonl. Completed support raw
logs/markers retained outside Git in h07-native-support-121-raw.tar.gz, SHA-256
2f85f2d29f0a099cb65f660f9377acf6c08d7a5b914151541ef3b66c3a2c7a3d.


## Native build-support correction accepted

ADR-0044 correction is now measured: 13.1-2 archive SHA-256
1e8bbc7d4bb0ad0590682a27980e172d65f9d811caf30291b3521aaaac215dd7;
runner recipe/postcheck 0/0, log SHA-256
ae05d8fa5f0856b8a02af6fae7db695075b6f73cd93d8467a780cf8794993846.
Actual installed-site Autoconf checks no/no/yes/yes, both real spawned-child
working-directory actions passed. Original failed package/stage/archive remains.
Independent ownership driver exit 0; 124 accepted packages, no BDB/APT acceptance.
Raw summary .local/logs/h07-native-spawn-correction-acceptance.json.


124-package h07-native-support cold pair saved with exit 0 and verified source
image consistency/copied hashes. Manifest and hashes are in RECOVERY.md. This
new pair is not restored or advertised as an ISO; BDB/APT remain unfinished.
Builder restarted for the complete corrected DB standard retry.


## Active-story visibility

Official foundation progress remains 38% until all H07 acceptance passes; its
weight is 24 points, so acceptance would raise the phase total to 62%. The
new active-work panel reports actual verified/running/remaining work separately
without awarding fractional credit or treating private preparation as completion.
At this update 124 packages are accepted, the cold pair is verified and the
complete corrected DB suite remains unfinished. No ETA is inferred from package
counts. Published state is a snapshot, not a live process monitor.


Direct native Dpkg count: 124 installed/configured packages, all 124 with their
matching own-source/recipe provenance record; zero partial/unconfigured entries
and zero missing provenance. Berkeley DB remains running/unaccepted and APT
unaccepted/absent. The current H07 recipe chain adds those two new packages,
for 126 planned base packages. Counts include real library/module/data/config
packages and do not measure remaining test duration or whole-release progress.
Raw count .local/logs/h07-live-package-count.json; future kernel/desktop/agent
stories and any later package-profile splits are outside this H07 count.


Release hygiene research (not H07 completion credit): a scoped Python audit
identified 15 exact public upstream PEM test fixtures; staged QA partition
verified 5395 regular test files and 3943 retained runtime entries unchanged.
No installed packages changed; actual native owner transfer/image exclusion
remains H11 work in ADR-0049. Full source tests remain preserved.

Raw scoped fixture audit SHA-256:
`1fad84d1bfad08fb55b2e33c32d6e6cf4544ab6bc08ff908d2453d88f187b540`.
Raw native archive partition probe SHA-256:
`bcf00808fc7142dd82895a64fd900750a89ac3d69c67fd68e666d30df850d130`.
Both reports remain outside Git at the paths recorded in ADR-0049.


Pre-dispatch native interpreter audit exposed a second Python metadata
generation requirement (direct bash/coreutils edges). Corrected the helper to
retain its exact canonical python -> python3 link across generations while
refusing unexpected payload. Private actual native Python 3.14.10/SSL execution
through the twice-processed link passed, exit 0; installed files unchanged.
Raw .local/logs/h07-native-python-alias-retry.json SHA-256
`d756d4f25426f625b41f31de0afcf04ede0e5fc087ad67d9d3ea3f2edc630d30`.
97 local checks pass; real package upgrades/final audit remain pending.


2026-11-06 19:37 UTC: live DB driver/runner and continuation supervisor remain
active. The standard suite reached transaction tests after file operations,
locking, logging, memory pool and mutex. Txn010's frozen source explicitly
waits 120 seconds before asserting the two-minute checkpoint condition;
this observed quiet interval is part of the test, not evidence of termination.
No final suite success or package acceptance is inferred. Raw partial
observation .local/logs/h07-db-transaction-observation.json SHA-256
`fd4660d3c68a884daebd91adc604f529b5d6f3b04ef3150751e294b6814a5fb7`.
The active-work snapshot advances; foundation credit remains 38%.


2026-11-06 20:05 UTC: actual driver/runner remain active after 2h56m; the
complete standard suite advanced from transaction tests into Dead006 deadlock
detection. One ten-worker group completed and the suite continued its checks.
No FAIL or final success sentinel appears in the observed partial log. The
success-gated continuation supervisor remains live; no duplicate dispatcher or
input sync was started. Raw .local/logs/h07-db-deadlock-observation.json SHA-256
`3595a785d3733f4380687f3c014daf2c9bfc46813429b112951257ed39e8be34`.
This is progress evidence, not Berkeley DB or H07 acceptance.


2026-11-06 20:34 UTC: DB driver and runner remain live after 3h25m. The
complete standard suite has advanced to Dead011 maxwrites/priority cases.
No FAIL or final success sentinel appears in the observed partial log.
Raw .local/logs/h07-db-dead011-observation.json SHA-256
`cd2297519d217c1614efeca5104ea5255fbb3a4882a9b1d85498970d2ed1c397`.
The continuation supervisor remains armed; 124 accepted packages and 38%
foundation credit are unchanged. Prepared later boot tooling earns no credit.


2026-11-06 20:52 UTC: driver/runner remain live after 3h43m; full standard
regression has advanced from deadlock cases to secondary-index cases Si001
through Si008 across method combinations. No FAIL or final success sentinel
appears in the observed partial log. Raw observation SHA-256
`bc18d28890a3e607103088de27d46d4b98b574944820e9f3e72b27573d8dfbd1`,
.local/logs/h07-db-secondary-observation.json. This remains unfinished work;
124/126 accepted packages, 38% foundation credit and all gates are unchanged.


2026-11-06 21:04 UTC: full standard regression continues Recd001 transaction
recovery variants after secondary-index cases. Driver/runner are live after
3h55m; observed partial log contains neither FAIL nor the final success sentinel.
Raw .local/logs/h07-db-recovery-observation.json SHA-256
`c65daa633cf109eabb885f0058a594a5ecd08e51b43a1e245e7bd92545ad0049`.
No new package or milestone acceptance is inferred; 124/126 and 38% remain.


2026-11-06 21:24 UTC: driver/runner remain live after 4h15m. Full standard
regression has advanced to Recd011's transaction-protected increment loop and
checkpoints. No FAIL or final success sentinel appears in the observed partial
log. Raw .local/logs/h07-db-recd011-observation.json SHA-256
`2e720187035ae8c31e6ee9a749c14a8e15fbacdc936dace7c0263380e22b3d0c`.
The existing continuation supervisor remains active. Accepted packages and
foundation milestone credit are unchanged; a partial recovery case is not
complete Berkeley DB acceptance.


2026-11-06 21:33 UTC: investigated the owner's suspected hidden blocker/loop.
The same Recd011 callback variant advanced checkpoint 59 to 104 between two
observations. Source proves a finite 201-iteration loop with 424.512 seconds of
intentional sleeps per variant; the prior range variant took 7m10s. Driver is
not retrying, and current guest resources are ample. See
[the investigation](H07-bdb-wait-investigation.md) for measured evidence and
limits. Continue this execution; no final suite acceptance has been inferred.

2026-11-06 21:36 UTC: the specifically investigated Recd011 callback variant
actually completed in 7m10s; its process exited and the original suite advanced
to Recd012 file-management recovery. See the wait investigation's completion
record. The suspected infinite loop was disproved for that execution; full DB
acceptance remains pending and the existing supervisor stays in place.


2026-11-06 21:39 UTC: quantified remaining work at the owner's request.
[Remaining volume](H07-remaining-volume.md) distinguishes 124/126 packages from
actual test/closure effort: the current partition group still precedes a
planned 1215-entry access-method matrix, among other standard-suite sections.
Final H07 also includes APT, Python alias, 931-path bootstrap quarantine,
126-package metadata review, seven audits and a paired cold checkpoint.
Counts are measured/planned scopes, not time or test-pass percentages.


2026-11-06 21:46 UTC: corrected DB driver/runner still live. Partition recovery
advanced through Recd024 and into its general Test014 cases; complete suite
result remains pending. Observation .local/logs/h07-bdb-archive-preparation-observation.json
SHA-256 3811608ed8a140180c6ca5ee9866388e5ec2a59c168b5bae60df3bf0929bee18.
During this wait, a private native minimal-initramfs archive roundtrip passed
(ADR-0054), including same-filesystem duplicate-build equality, exact extraction
and corruption/truncation rejection. No installed or active BDB input changed;
this future image preparation does not count toward H07 or live-boot acceptance.


2026-11-06 21:54 UTC: partition Test044 is running its first cycle with five
native workers, each observed near one full CPU and increasing CPU time.
Source defines three cycles, each with 300–600 seconds of randomized load
before simulated crash/recovery; the current first cycle logged 525 seconds.
The numbered general sequence ends at Test142 with 135 listed entries, not at
Test135; seven numbers are absent upstream and 91 entries follow Test044 in
one pass. See H07-remaining-volume.md for exact names/source/process evidence.
This corrects the conversational conflation of entry count and highest number.
No suite input, test coverage or acceptance boundary was changed.


2026-11-06 continuation during Test044's timed load: implemented a read-only
private-key-marker image audit and exercised it against the real own Python
3.14.10-1 archive in private staging (ADR-0049). All 15 known upstream test-key
files remain intact in QA; the separated runtime has zero matching markers.
The scan accounts for 9,330 regular files and 293,207,634 bytes without dropping
bytes. Installed files, active DB sources and package ownership remain unchanged.
This is future release-audit preparation, not native QA ownership transfer or
complete image credential acceptance. H07 still awaits the full DB result.


2026-11-06 22:01 UTC: Test044's first partition cycle reached its programmed
crash at 22:00:16, exactly 525 seconds after start, performed recovery/file
verification, and entered cycle 2 at 22:00:51 with a 446-second load interval.
Original driver/runner remain live; the complete standard suite and package
acceptance are still pending. Raw observation
.local/logs/h07-test044-cycle1-observation.json SHA-256
440825c0d730ca0ea43616d38ccedcde79a3241aa979ab5ee7a937dbf784ab1b.
The root-image private-key audit preparation is published with 110 local checks
and all GitHub workflows passing at 4bab52b; it does not satisfy H11 acceptance.


2026-11-06 continuation during Test044 cycle 2: a native Dpkg private-root
experiment proved the planned Python QA ownership handoff (ADR-0049). Wrong
order was rejected; core-then-QA unpack transferred all 5,395 real source-built
files with exact bytes, modes, ownership and mtimes. Both private packages
remain explicitly unpacked, not configured. Installed Dpkg state is unchanged.
This prepares release image work and does not alter H07's 124/126 package count
or accept the future installed QA split.


2026-11-06 22:10 UTC: current range-partition Btree Test044 invocation advanced
through its second programmed crash at 22:08:17 and recovery/file verification
into cycle 3 at 22:08:53 (370-second load). Other configurations still follow;
this is not completion of Test044 across the suite. Original driver/runner
remain live. Raw .local/logs/h07-test044-cycle2-observation.json SHA-256
680a839c89af6e48bc081d38f88780cc0a858959f2e0c4e645dea18d09e23a05.


2026-11-06 22:16 UTC: the first range-partition Btree Test044 invocation
completed all three crash/recovery cycles. Its retained log segment contains
10 database verification successes, 10 dump/load successes, 10 salvage
successes and no FAIL marker. At 22:15:39 the suite entered the next callback-
partition variant, whose first cycle logs 366 seconds. Raw full case/transition
.local/logs/h07-test044-range-partition.json SHA-256
7a43188cc0c1cd800ffa0d5e11dc9c1f6b57a260529f8f0500c81aa67f7e5389.
This accepts neither the complete Test044 matrix nor Berkeley DB.

Prepared the H11-only unchanged Python QA archive handoff and verified its
read-only preflight on all 5,395 real installed QA files (ADR-0049). Default
package conflict refusal is retained; the special plan cannot install. Native
production archive creation/transfer remains gated and unexecuted. Active
BDB inputs and installed package state remain unchanged.


2026-11-06 22:45 UTC: callback-partition Btree Test044 completed its three
programmed crash/recovery cycles (last crash 22:41:12), ten database verification
successes and ten salvage successes, with no FAIL marker in the retained case.
This callback case has zero dump/load success messages; no such check is claimed.
The original suite has advanced to Test081, and driver/runner remain live.
Raw complete case/observation .local/logs/h07-test044-callback-partition.json
SHA-256 2cdd5a6fd35578cdebf4c4ff6cccc40273a27ee4df7ea07b513a701a98aff95e.
Case segment SHA-256 9b2dcfaccace8cfada61ac0fb470d053dee483729db62043d8bcbce172cfbf11.
These two observed Test044 invocations do not accept its remaining matrix or
the complete DB suite. H07 remains 124/126 packages with full closure pending.


2026-11-06 22:55 UTC: both partition Btree Test142 variants have appeared and
the same original suite has moved to Recd001 hash operation/transaction recovery
checks. Driver 1364 and runner 1365 remain live; the change of test-family name
is not a new build or full-suite acceptance. Raw observation
.local/logs/h07-partition-numbered-progress.json SHA-256
 a175fc1f034c1bc9f101282d2133108210a9abb12ee9c56278ccd157892081ea.
The prepared fresh-image account component passes native Shadow checks in a
private root (ADR-0055); installed accounts and H07 package counts are unchanged.


2026-11-06 23:04 UTC — Original DB recovery progression observed from Recd001
(hash) to Recd002 split recovery at 23:00 and Recd003 duplicate recovery at
23:01 UTC. Runner 1365 and driver 1364 remain live. This remains within the
full standard suite, whose final result is pending. Raw observation
.local/logs/h07-recd003-progress.json SHA-256
5fda33864751609ec1794fd9120bcd38c5f6cfe137932e858c673b5bb3532ca8.


2026-11-06 23:17 UTC — The original partition recovery suite advanced through Recd011
timestamp recovery into Recd015 hash prepared-transaction cases. The current
large cases prepare 10,000 transactions, recover their handles/GIDs and check
commit/abort outcomes. Driver 1364 and runner 1365 remain live. Raw observation
.local/logs/h07-recd015-progress.json SHA-256
f1150b17b0e17ebd8dc8968c0efbc811080b9754f3c6ae8ff6de44835f8eed5e.
The complete Berkeley DB result remains pending. A separate read-only native
payload audit found only the already planned shared Info-index ownership issue;
see ADR-0057. No H07 test or final closure requirement was relaxed.

2026-11-06 23:33 UTC — Partition block reached Hash callback-partition Test044.
The first 512-second load ended with its intentional crash at 23:31:48,
recovery/verification ran, and cycle 2 began at 23:32:24 for 517 seconds.
Driver 1364 and runner 1365 remain live; the partial log has zero lines starting
FAIL. Complete-suite output validation and subsequent blocks/method matrix are
still pending. Raw observation .local/logs/h07-live-console-progress.json SHA-256:
09eb2ea6c12fe869ef0df2a5f716cec7f58a8e4e4ace1fac06d6eae5d9f903a5.
Independent private native live-console component checks passed (ADR-0058),
without changing H07 sources, installed accounts or package state. The accepted
package boundary remains 124/126; the story is not accepted.

2026-11-06 23:41 UTC — Hash callback-partition Test044 finished its second
517-second workload with the controlled crash at 23:41:01, completed the next
recovery/verification, and began cycle 3 at 23:41:36 for 450 seconds. Original
driver 1364 and runner 1365 remain live; zero partial FAIL lines observed.
Full-suite acceptance is pending. Raw observation
.local/logs/h07-package-database-progress.json SHA-256:
27b63c9f77e1210f5ce045ea6ca50d13316b2073d6b09876325fd33bdbdd8a6c.
Separate native metadata-copy checks passed without installed changes (ADR-0059).
They do not bypass the pending H07 package/payload/dependency closure.

2026-11-06 23:50 UTC — Hash callback-partition Test044's segment is complete:
three workload/crash/recovery cycles, ten file verifications and ten salvage
verifications. The suite advanced to Test081 in the same partition block;
driver 1364 and runner 1365 remain live, with zero partial FAIL lines observed.
This does not accept the complete standard suite or the package. Segment SHA-256:
d7814ce5abbd6f97be0d32f74e4b7af846880a16ef46320fa205f7a9654b152e.
Raw observation .local/logs/h07-test044-hash-callback-complete.json SHA-256:
b2a95c2898911c5ec5dbcce0e7bd3f5d0579b4bd62348076592582566f226137.
Independent native offline-service checks corrected prepared H08 defects
(ADR-0060), with no installed package/configuration or running-input changes.

2026-11-06 23:55 UTC — The unchanged full standard run advanced beyond the
partition group into compression (block 19). Test014 was observed within this
new group. Driver 1364 and runner 1365 remain live; zero partial FAIL lines.
Group traversal is not final acceptance: later groups/method matrix and the
complete output validator still must finish. Raw observation
.local/logs/h07-compression-progress.json SHA-256:
ee0e32411ab87b95a8befd63590420b89d486396347e54a779176cb269da2ff3.


2026-11-07 00:16 UTC read-only observation: compression Test044 completed two
crash/recovery cycles and started cycle 3 at 00:15:46 for 301 seconds. Original
driver/runner PIDs remain live; the partial 4585452-byte log contains zero FAIL
lines. Complete standard-suite validation and package acceptance remain pending.
Raw observation .local/logs/h07-compression-cycle3.json SHA-256:
7b052c821f75706c3524ed0da6ba085321dd15b43ffd22dadc2868d79d11e67c.


2026-11-07 00:22 UTC: compression Test044 finished its three 554/442/301-second
cycles, three recovery checks, ten file verifications and ten salvage checks.
Execution advanced to compressed Btree Test095; original driver/runner remain
live, with zero FAIL lines in the partial standard-suite log. Full-suite and
package acceptance are still pending. Raw observation
.local/logs/h07-compression-test044-complete.json SHA-256:
e5051a5b150efcec79e90a0fd7086c3ad6a76b8bf8ae5ee63750c5cdd49bee6f.
Test044 segment SHA-256:
5cc7bd288af58456e7a20c3b7b8641c82fdf7e7ed6e9d6a94076682b9628af62.


2026-11-07 00:27 UTC: the full standard run advanced beyond compression into
automated repmgr (block 20), exercising master/client transactions with mixed
on-disk/in-memory configurations. Original driver/runner remain live and the
partial log has zero FAIL lines. Raw observation
.local/logs/h07-automated-repmgr-progress.json SHA-256:
38b814be3c73221619525870eae0daea561573a9380a04a4d1cfcaedcdd2d803.
This group transition is progress, not complete-suite/package acceptance.


2026-11-07 00:37 UTC — Original driver 1364/runner 1365 remain live (7h28m);
automated repmgr election cases progress through in-memory/on-disk combinations
and master failure/re-election. Partial ALL.OUT has 4,969,028 bytes, zero FAIL
lines and no driver exit file. Raw observation
.local/logs/h07-repmgr-election-progress.json SHA-256:
0a47aebdf6c8f0300e01895c961d33cd0806b18ba1e18973007b4fd97a2f3d31.
This remains block 20/27, not complete-suite or package acceptance.


2026-11-07 00:50 UTC — The complete suite has two actual FAIL entries, first
observed at 00:42:16: repmgr007 reads an asynchronous error log too early, and
repmgr100 cannot find db_repsite. Original driver/runner remain live in block 23
(replication, observed Rep016); no suite or package acceptance is claimed.
The timing failure was reproduced and corrected privately with three complete
native repetitions passing; the missing helper's source is absent from the
frozen and upstream 5.3.28 trees. A C++-enabled isolated build confirmed that
absence. All twenty other_repmgr cases are now running in a separate bounded
private fixture. See ADR-0067 and its raw evidence hashes. The current full run
is collecting additional failures; its failed groups are not counted passed.


2026-11-07 00:58 UTC — The independently implemented native db_repsite adapter
passed unchanged repmgr100/101/102, exit 0, including real replication and
process-death/failchk recovery. All eleven original multi_repmgr cases now run
in a private network namespace/build directory; the first-three fixture is
preserved. The separate twenty-case other_repmgr run is in Repmgr026, and the
original standard suite is in Rep020 with the same two FAIL lines. See ADR-0068
for source/binary/log hashes. No full-group, suite or package acceptance yet.


2026-11-07 01:01 UTC — All eleven unchanged multi_repmgr cases passed with the
native adapter (exit 0, no FAIL lines). Five negative native invocations passed;
all 483 private Tcl input hashes match the independently reconstructed frozen
reference. Exact recipe compilation reproduced the same tested executable.
The repmgr007 patch is frozen and recovery preflight passed idempotence plus six
negative input checks. See ADR-0067/0068 for complete hashes. The original suite
continues collecting block 23 results with its two known failures; the separate
other_repmgr group remains active. H07/package acceptance is still pending.


2026-11-07 01:08 UTC — Both diagnosed replication-manager groups now pass
completely in the private native fixture: other_repmgr 20/20 and multi_repmgr
11/11, explicit exit 0 and no FAIL lines. Dispatch lists exactly match the
frozen testparams.tcl definitions. Both group results and hashes are recorded
in ADR-0067/0068. The original standard suite continues in Rep039 with the same
two known failures; Berkeley DB is not installed/accepted and APT remains gated.
Prepared provenance corrections pass all 148 local checks; published commit
9862c7d contains the helper/patch source-list coverage and production exclusion.


2026-11-07 01:26 UTC — A complete corrected Berkeley DB standard run is active
in a private canonical source view (ADR-0069), guest driver 1107192. It reuses
460 verified native build files and 483 verified Tcl inputs; all 10,208 copied
inputs have a protected manifest. Native CuTest passed and the complete run_std
reached Env012 with zero FAIL lines. Original driver 1364 continues in Rep079
with its two diagnosed failures. Separate PID/IPC/network/mount namespaces and
private tmp/var/tmp/tmpfs shared memory were measured. An initial ext4 shared-
memory view was deliberately stopped and corrected, with its failure evidence
preserved. No package installation or acceptance is authorized by this test-only
driver. Complete-result/production handoff remains required.


2026-11-07 01:40 UTC — Original Berkeley DB standard run is in Recd001,
block 25/27, with its same two known failures. The corrected complete run is
in Fop006.80, block 4/27, zero FAIL lines. Both drivers are live with no exit
files. An independent read-only completed-result verifier now rejects actual
unfinished/interrupted/outside-path inputs, and all 152 local checks pass.
ADR-0069 records hashes and limits: no positive full result, production install
or package acceptance yet. H07 remains 124/126 accepted packages.


2026-11-07 — Independent APT preparation found a runtime seccomp configuration
omission before installation. ADR-0070 records the correction and native proof
that the worker observer accepts only the expected credentials plus an additional
kernel filter. Eight real process scenarios and a native TLS fixture passed;
154 local checks pass. Actual APT build/acquisition and Berkeley DB acceptance
remain pending. No package-count or weighted milestone credit is added.


2026-11-07 01:52 UTC — Both Berkeley DB drivers remain live with no terminal exits.
Original: Recd003.e: remove dups 1 at a time prepare-commit; same two failures.
Corrected: Fop006.196: truncate (a) 0 commit;  rename (foo b) no such file.  Files remaining: b a.; zero failures.
Raw .local/logs/h07-db-standard-progress-<sha256>.json SHA-256:
f31ecc5d75d5575b9ca73827db06d74d1b109fc92e2adc4e9ab3cfae6c3066a5.


2026-11-07 — While both complete Berkeley DB runs continue, independent
release preparation verified native optional Python QA exclusion in a private
configured root (ADR-0071): 5,396 QA entries removed, 3,943 runtime files/links
preserved, 22 packages retained and native runtime/database checks passed.
A controlled residual-data case correctly failed after successful Dpkg exit.
This is component preparation only; H07 still has 124 accepted packages and
H10/H11/G1 remain unaccepted.


2026-11-07 02:07 UTC — Original driver 1364 remains live in Recd011.b (200 iterations),
block 25/27, with the same two failures. Corrected driver 1107192 remains live
in Fop008.33, block 4/27, zero FAIL lines. Raw observation SHA-256:
c32c917dc2d6ae0b0f870a48a2973f9d346823c6338ee491f0279f1cfc4146b2
(.local/logs/h07-db-standard-progress-<sha256>.json). No suite/package acceptance.

2026-11-07 02:15 UTC — Original driver 1364 is live in Recd012, iteration 43,
block 25/27, with the same two failures. Corrected driver 1107192 is live in
Fop008.103, block 4/27, with zero FAIL entries. Both process identities/start ticks
were checked and terminal exit files remain absent. Raw observation SHA-256:
8e996a1782ca24f135ada840959c8c2b54dd5f16dde03795c73c53b8353d93cb
(.local/logs/h07-db-standard-progress-<sha256>.json). H07 remains 124/126; independent
image marker-review preparation passed its actual native probe (ADR-0071),
without changing the installed base or granting milestone credit.


2026-11-07 02:27 UTC — Both Berkeley drivers remain live with unchanged process
identities and absent terminal exits. Original: Recd004.c in the next rbtree
recovery configuration (block 25/27), the same two failures. Corrected:
Fop008.219 (block 4/27), zero FAIL entries. Raw observation SHA-256:
8bd1860ef2ea99e10c4d9cdcde16057ad7f85cd467207419c682d11eaf66b3bf
(.local/logs/h07-db-standard-progress-<sha256>.json). Independent root-assembly
preparation and actual native payload-audit checks are recorded in ADR-0072;
H07 remains 124/126 accepted packages, with no new milestone credit.


2026-11-07 02:43 UTC — Original Berkeley driver 1364 is live in Recd001.h,
now using recno after the earlier btree/rbtree recovery configurations (block
25/27), with the same two failures. Corrected driver 1107192 is live in
Fop010.98 (block 4/27), zero FAIL entries. Both retain their original process
identities and lack terminal exits. Raw observation SHA-256:
d8ed88b0566e2211c79feca478d2528c7f8f3f4de48d53ad1007a0e4a1bb2a36
(.local/logs/h07-db-standard-progress-<sha256>.json). Independent image-state
attribution checks are recorded in ADR-0073; no active inputs or installed
package state changed, and H07 remains 124/126 accepted packages.


2026-11-07 02:52 UTC — Both actual Berkeley driver identities remain live, with
no terminal exits. Original: block 25/27, Recd011 recno recovery iteration 104,
the same two known failures. Corrected: block 4/27, Fop010.181, zero FAIL entries.
Raw observation SHA-256:
d5f513ae80b87bccb973ab4e7bfd1d54984066e301b1c46d1005726a81998751
(.local/logs/h07-db-standard-progress-<sha256>.json). Independent private native
image executable-resolution checks passed (ADR-0074): seventeen packages,
147 dynamic executable entries, 41 scripts, eight refusal cases. The installed
builder remains unchanged; H07 is still 124/126 accepted packages. No full
foundation image or later milestone acceptance is claimed.

2026-11-07 07:59 UTC — Corrected by ADR-0079: both driver identities were live,
but only the original was in block 27/27. The corrected run was in partition
(block 18/27); the earlier final-matrix claim was wrong. Original: Test091
queue configuration, the same two known failures. Corrected: Test044 hash with
partition callback, third crash/recovery cycle, zero FAIL entries. Neither has
terminal exits. Raw observation SHA-256:
729e4c8728c2d28d456b84929bc54646562f34afb0e674b221326727ee3016ca
(.local/logs/h07-db-standard-progress-<sha256>.json). The observer now reports
Test headers as well as Recd/Fop instead of retaining an obsolete recovery
heading. H07 remains 124/126 accepted packages. Independent private native
Squashfs/overlay correction and initramfs evidence are in ADR-0075.

2026-11-07 08:09 UTC — Corrected by ADR-0079: original block 27/27; corrected
run still in partition, block 18/27. Both identities were live.
Original: Test044 queueext cycle 1 with the same two known failures. Corrected:
Test142.h hash/partition callback, zero FAIL entries, after completing the earlier
Test044 crash/recovery cycles. Neither driver has terminal exits. Raw observation
SHA-256: 5401327de7abb15a4fee1d5d3189820fbff85b246e13ebdec287be2c2b1a86eb
(.local/logs/h07-db-standard-progress-<sha256>.json). H07 remains 124/126 accepted
packages. Independent native compression/readback preparation passed (ADR-0076);
complete foundation assembly and native-kernel boot remain pending.

### Native ISO preparation during the two DB suites — 2026-11-07 08:20 UTC

Both actual Berkeley driver identities remain live: original 1364 in Test044
queueext cycle 2 with the same two known failures; corrected 1107192 in Test044
btree cycle 1 with no FAIL entries. No terminal exit exists. Observation SHA-256
3ef0f21ba8a0e3988227ec82a8c9de460d081e3ca1d381083cc26f4b557c15e0.
Native private ISO preparation passed after measured header and symlink fixes
(ADR-0077): thirteen stages, eight metadata entries and corruption rejection.
This independent experiment does not increase H07 package count or accept H11.

### FAT and actual loader boots during DB wait — 2026-11-07 08:30 UTC

Correction (ADR-0079): original block 27/27, corrected compression block 19/27.
Both driver identities remain live. Original 1364
finished this configuration's Test044 recovery cycles and reached Test078
queueext with the same two failures. Corrected 1107192 is verifying Test044
btree cycle 2, zero FAIL entries. No terminal exit exists. Observation SHA-256
237daaff4ce9b361951cec936ce3eef6921d442178089ee2d987fdcd2ab191cb.

Independent private preparation passed native Mtools FAT readback and four real
BIOS/UEFI CD-ROM/USB GRUB loader boots (ADR-0078). No kernel/root was included;
this does not accept the full boot matrix, H07 packages or any later milestone.

### Reporting correction — 2026-11-07 08:36 UTC

ADR-0079 corrects the previous misclassification of the corrected complete run.
Actual outer dispatcher headers place it in compression, 19/27, not the final
matrix. It reached Test076 with zero FAIL entries. Original remains live in
27/27, hash method 8/9, Test044 cycle 1, with its two known failures. Neither has
a terminal exit. The versioned observer retains each full outer-header snapshot,
checks source/configuration hashes and refuses malformed sequences. Raw SHA-256
0ffd396f79afaea39598e11cee701e5b31af7fa6fcf28d5f3fee61742c49787b.
Package counts and milestone credit were not changed by the reporting error.

### Independent identity audit and verified database wait — 2026-11-07 08:48 UTC

Original driver 1364 remains live in group 27/27, hash method 8/9, Test044 cycle 2
with the same two failures. Corrected driver 1107192 is live in group 20/27,
automated repmgr, zero FAIL entries. Neither has terminal exit files. The
corrected run has advanced beyond compression; returned groups are not separate
acceptance claims. Complete raw observation SHA-256:
ba771b0d7940f738a412fc89290155c35390ce5e53cb31a32119ea24fb42249b.

Independent private image preparation passed the fresh-identity audit and
eighteen rejection cases (ADR-0080). Active H07 inputs and installed packages
were unchanged. Berkeley production acceptance, APT and final closure remain
required; H07 stays 124/126 and foundation credit stays 38%.

### Compression/initramfs integration during DB wait — 2026-11-07 08:56 UTC

Both actual driver identities remain live. Original 1364: final matrix 27/27,
hash method 8/9, Test044 cycle 3, the same two known failures. Corrected 1107192:
automated repmgr 20/27, initialization tests, zero FAIL entries. Neither has
terminal exits. Raw observation SHA-256:
6a13e3281f6acd2461ea7e9e0b480efcea7c6207dbb9f3ce56287f161f02a537.

Independent preparation connected a real private compressed filesystem to its
native initramfs with strict evidence/profile binding (ADR-0081). Sixteen
negative bindings and premature production gates passed; full foundation image
and boot remain pending. No installed package or active H07 input changed.

### Replication detail correction and verified wait — 2026-11-07 09:03 UTC

Original PID 1364 is live in 27/27, hash method 8/9, Test097.c; it completed
the previous Test044 crash/recovery cycles and retains the same two failures.
Corrected PID 1107192 is live in 21/27, Repmgr025.h, zero FAIL entries. Neither
has terminal exits. The observer now replaces stale compression configuration
labels during replication; outer-group classification is unchanged (ADR-0079).
Raw observation SHA-256:
db25c36e4e06c63e292f20a84a47c56f21b13e0607fea48dca8c6adc8f9e19a8.
H07 stays 124/126; complete corrected suite and production postchecks precede APT.

### Original terminal result and output diagnostics — 2026-11-07 09:20 UTC

Original driver 1364 ended at 09:10:53 UTC, recipe/driver exit 1, no postcheck,
zero installed changes and empty change manifest. Its complete standard output
contains 25 unexpected lines: the two known repmgr failures, thirteen copies of
an informational Test142.b line and ten log-record coverage warnings. The
prepared original-result handoff correctly refused these additional diagnostics;
no nomination or production installation occurred.

The versioned probe_bdb_output_diagnostics.py extracts the frozen check_output
procedure without sourcing or executing the test dispatcher. Actual native Tcl
rejects the informational line's extra space between tab and Test142, accepts
the identical line without that space, and still rejects deliberately injected
FAIL and missing-coverage controls. Four checks pass. Original and corrected
checker, Test142, logtrack implementation and logtrack list have identical
hashes. Neither source tree nor original output changed. The corrected output
already contains four copies of the same informational line, so zero FAIL alone
will not satisfy the current strict final summary. No success is claimed.

Raw diagnostic report SHA-256:
5a962f29ff257eacf51b97ed0e4d6c2cd436c4d015e8592107775f09786d4a33
(.local/logs/h07-db-output-diagnostics-<sha256>.json).
Original standard.log SHA-256:
2d0441963aad69dda37ee0f26fd4814ea35541bec2e5008390eb6a8779c38283.

Missing recovery records are __bam_irep, __crdel_inmem_create,
__crdel_inmem_remove, __crdel_inmem_rename, __db_merge, __db_pg_trunc,
__db_pgno, __db_realloc, __ham_changeslot and __ham_contract. Frozen
logtrack.tcl:112-117 emits these when its collected database has no matching
record. Frozen test.tcl:1856-1921 initializes and summarizes that database only
around run_recds; testutils.tcl:1446 and 1714 collect inside recovery helpers.
Other access-method tests also exercise compaction/recovery (for example,
test140), but the current evidence does not establish coverage of these ten
records. Additional source analysis and actual native coverage/recovery
experiments are required; broad warning suppression is not an authorized fix.

At 09:20 UTC corrected PID 1107192 is live, group 23/27 replication, Rep002,
zero FAIL entries and no terminal exits. Raw progress observation SHA-256:
f94a65c5895842071e52915245bf2556f00bec285bbb44905399b9dbb4a89573.
H07 remains 124/126; source/coverage corrections, complete terminal review,
production postchecks, APT and final ownership/audit closure remain pending.

### Native recovery-coverage diagnosis completed — 2026-11-07 09:29 UTC

The separate ADR-0083 experiment passed with actual test/driver exits 0/0.
All ten warning-named log types were observed through native db_printlog after
unmodified hash-recovery, named-memory, 80,000-entry deep-tree and 10,000-entry
hash-compaction tests. Disk data compared equal across actual recovery; committed
named-memory data survived recovery/reopen using the documented retained
environment mode. Commit/abort behavior and source/input stability also passed.

Report SHA-256: b2730bcd16ec81fb3d228c20afdeef5dd32d4f0fd9b7091416f1a273e5afd5af.
The fixture is /mnt/lfs/sources/recovery/db-standard-coverage-0_05jaht.
This resolves the question of whether those types can actually be exercised;
it does not accept the still-running complete standard suite. No acceptance
gate, source input, terminal exit or failed original output was rewritten.

### Independent complete-output review — 2026-11-07 09:40 UTC

Native Tcl reproduced all 25 diagnostics from the original complete report.
The new classifier retained both actual failures and refused diagnostic-only
readiness; it also refused the incomplete corrected report. Exact original
report hashes now permit history preservation, while actual premature prepare
still refuses the live corrected run without creating a candidate/archive.
Raw report SHA-256:
e1775d2ec868f2693fdf30d2237dccdd33235ffa8521a90e0de5c869c9fcd616.

Independent coverage verification rehashed all 10,208 source entries, confirmed
the exact native witness and its pairing with the standard input manifest, and
passed sixteen rejection cases. Raw report SHA-256:
6839dcca04bc5db9e13b9a0097ec1724d7f9e3ba4d7d34f55ffe1cc3de3eb0e3.
Complete corrected review, protected custody and production qualification remain
pending; no package acceptance or exit code changed. See ADR-0084.

Corrected PID 1107192 remains live in group 23/27, Rep036.c, with zero FAIL and
no terminal exits. Observation SHA-256:
4cd1b0f16093513750190d584e39b782e718c7c9fa16ffd9e4e60c6c9e29995d.
H07 remains 124/126 accepted packages, foundation 38%, APT gated.
