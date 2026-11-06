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
