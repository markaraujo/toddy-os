# ADR-0077: Verify native ISO metadata and correct measured upstream defects

- Date: 2026-11-07
- Status: Native private build and metadata/corruption checks passed; production installation gated

H07's complete database suites still run. Build the frozen Libburn 1.5.8,
Libisofs 1.5.8.pl02 and Libisoburn 1.5.8.pl02 in a protected private prefix
inside the designated target. Do not install packages, synchronize active build
inputs or grant H11 acceptance. The separate shared-library stack follows frozen
BLFS 13.1 multimedia/libburn.html, libisofs.html and libisoburn.html, including
the explicit pkg-config option. No upstream test suite exists for these packages.

The private driver uses two compilation jobs, cleared environment, verified
frozen archives, safe extraction, individual durable logs/exit codes and
30-minute stage deadlines with private process groups. The native compiler,
libc, ACL, Readline and zlib providers come from the accepted source-built base.
It verifies the actual shared-library resolution, runtime versions, ISO metadata
roundtrip and deliberate payload-corruption refusal. Package database identity
and immutable probe inputs are checked afterward. Private-prefix libraries and
experiments are not distributable release artifacts.

The first attempt correctly stopped at Libisoburn configure. Its early header
checks precede PKG_CHECK_MODULES, so private-prefix experiments need explicit
CPPFLAGS/LDFLAGS in addition to PKG_CONFIG_PATH. That is an experiment-only
path setting; normal production libraries remain under /usr.

It also exposed an obsolete attr/xattr.h test in frozen Libisoburn configure.ac
lines 244–274. The native target has Glibc's sys/xattr.h. Frozen Libisofs already
prefers this header and uses its real listxattr implementation. Libisoburn's own
configure.ac lines 205–210 explain that its ACL/xattr macros mirror Libisofs;
they are not direct source dependencies of Libisoburn/Xorriso. No corresponding
attr/xattr.h include occurs in those source directories.

Correct the frozen Libisoburn configure and configure.ac header probe to
sys/xattr.h. Keep real compiler/linker detection and the required generated
feature definitions; do not force an Autoconf cache answer. Preserve the frozen
versions and source hashes. Alternatives rejected: installing an obsolete
compatibility header into the OS, pretending the removed header exists, omitting
the feature check, or silently upgrading the selected packages. The consequence
is a small recorded source adaptation that future rebuilds must apply before
configuration; actual metadata roundtrip remains mandatory.

Patch both shipped input and generated configure while retaining their source
timestamps. The first corrected configure passed but touching configure.ac
triggered a request for upstream's unavailable Automake 1.14. Regenerating the
entire Autotools output or adding that obsolete host tool is unnecessary for
this matching literal header change. Preserve that failed generation and verify
the timestamp-preserving correction with a fresh private build.

Primary-source configure.ac SHA-256 values from the frozen archives:

- Libburn: c597c6163595752c693dd7b45df73c78c947b9581df8120a26cf8052ffc8f411.
- Libisofs: f5dc3f7fea35b7bc727ba9e6fa265e151afbad362a63b4766ecc22ccb100d495.
- Libisoburn: 56be3f59c60c483b0c956b713dd363d21fd24845868580e80d23d245be2ebef9.

Failed generation: /mnt/lfs/sources/recovery/libburnia-native-ukt3ad_w, terminal
exit 1 at Libisoburn configure. Complete local collection SHA-256
7b9b6abc3af3a0c4093db2b20881846ad7146bdbddd7018cd841352e3cf0fde8 retains
the successful earlier stages and failed diagnostic. No installed state changed.

The Autotools regeneration failure is retained in generation
/mnt/lfs/sources/recovery/libburnia-native-82kv9yvc; collection SHA-256
ed73a4b0be1344ef4b95256ebc5eb1c90b4227e08a9dc3403908541206b7130e.

Hybrid BIOS/UEFI image generation, native-kernel boot, complete assembled-root
inspection and the G1 acceptance matrix remain separate required work.

The first complete native stack built and resolved all three private shared
providers, but exact extraction comparison failed: the restored relative
symlink had extraction-time mtime instead of the original mtime. The original
unfiltered mismatch remains in collection
93feb4dfab6554ddb80c5755daa82b033e58791929a7bf5a0e63cd2a66df9f72,
generation /mnt/lfs/sources/recovery/libburnia-native-j5je2gmq. All other compared
metadata matched. Frozen xorriso/read_run.c SHA-256 is
a936fe4c72b781f7d3f58ca325523dc3042ffbf2f88c5039eeb8d9b3a859a7b9.
Its restore_properties label explicitly bypasses symbolic links. The generic
timestamp function uses utime, which follows links and must not be reused here.

Apply a small versioned patch to restore symlink numeric ownership with lchown
and timestamps with utimensat(AT_SYMLINK_NOFOLLOW), preserving the existing
minimal-transfer/no-properties flags and propagating errors as FAILURE. This
uses the native Linux/Glibc API rather than a compatibility shim. Keep the
original complete metadata comparison; do not normalize restored timestamps
from the expected fixture or omit symbolic links. Extend the actual test with
non-root-owned links, a dangling link and a link to a separately hashed/stat'ed
outside sentinel. Its ownership, mode, contents, mtime and xattrs must remain
unchanged. The patch applies to the frozen source with zero fuzz and is retained
with installed documentation for corresponding-source reconstruction.

Alternatives: accepting the timestamp loss as an upstream limitation would not
meet the prepared exact roundtrip check; manually correcting extracted files
would hide the defect in the tool. The local patch adds maintenance obligations
and needs native regression on future updates. It does not establish arbitrary
untrusted-ISO extraction safety or waive the disposable-target restriction.

Corrected full private build passed: generation
/mnt/lfs/sources/recovery/libburnia-native-utlu89er, driver 3407380 terminal 0,
all thirteen stages exit 0, unchanged installed package status and probe inputs.
Complete raw collection SHA-256
b005fa096c802c3a2752813f2228799a9105602e45a32885ba90e978414d25f1.
All three actual runtime libraries report 1.5.8; Xorriso reports 1.5.8.pl02.
Compiled Xorriso SHA-256:
b37e3a15b23a7d44ad961dae927bfd03a0af49a9a9fbc533c2b8295be72d6fa1.

Eight fixture entries passed exact content/mode/numeric ownership/mtime/xattr
comparison, ACL preservation and hardlink identity; dangling and outside links
passed without modifying the external sentinel. The 458,752-byte regular-file
ISO passed embedded checksums. A copy with one payload bit flipped reported
MISMATCH and exited 32. Its successful fixture was removed after evidence
capture. This ISO is test data, not a bootable release. No upstream test suite,
native-kernel boot, package acceptance or full-root acceptance is inferred.

The exact production shell header-adaptation slice also ran with native tools
on a fresh private copy: bytes match the successful build, original mode/mtime
remain intact and configure remains executable. Raw SHA-256
2d089cc1a65102c098aee393edea933d1aafc0efa9ae3adec4a8163bfc571ba9.
Repository validation passes all 154 local checks; these do not replace boot.
