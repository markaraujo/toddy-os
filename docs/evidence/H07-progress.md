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
