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
