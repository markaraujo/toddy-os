# H07 — In-progress final package evidence

Date: 2026-11-05. H07 is NOT complete. Critical final compiler/libc/binutils
suites and the remaining chapter 8 packages are pending.

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
