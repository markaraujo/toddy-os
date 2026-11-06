# ADR-0047: Reuse native newc support and freeze live-image tools

- Date: 2026-11-06
- Status: Sources frozen and private native newc experiment passed; image builds pending

H07 remains incomplete, with its full corrected DB standard suite active. No
H10/H11 target build or image assembly is eligible yet. Prepare tools without
mutating active inputs or claiming an ISO. Frozen BLFS 13.1 general/cpio.html,
postlfs/initramfs.html and multimedia/libburn.html, libisofs.html and
libisoburn.html are primary references, along with actual native Libarchive
3.8.11 cpio/bsdcpio.1 and Linux 7.1.8 initramfs format documentation/parser.

The accepted source-built Libarchive already supplies /usr/bin/bsdcpio. Its
archive SHA-256 is cff483c439eba92b129f569da9374f5bedc3e72f7f977477da2a343f9ac8c1ee.
Use its explicit -o --null --format=newc --owner 0:0 interface for the minimal
initramfs instead of adding GNU cpio. Do not alias incompatible CLI flags or
replace the main root filesystem's numeric ownership with all-root data.
Root Squashfs metadata/ACL/xattr preservation still needs separate real tests.

Focused actual-target experiment passed: seven private fixture entries,
independent 070701/13-field header parsing, root ownership, executable/file
modes, hardlink identity, symlink content, Unicode/newline names, native
extraction and gzip -n roundtrip. No installed changes. Log JSON SHA-256
59332afbdabc5822654f29817d9a9c9f6545ebd6a18f624adfb5a485e49ea576,
.local/logs/h10-native-newc-probe.json; captured exit 0. Temporary fixtures are
removed. Archive hashes describe that experiment, not cross-build reproducibility
or an actual boot. Kernel boot remains mandatory after native image assembly.

GNU cpio 2.15 was an additional candidate, never part of the frozen target.
Its known extraction/listing issues would require maintained fixes and native
security regressions: first-party distribution tracking links upstream fixes
for [CVE-2026-66484](https://security-tracker.debian.org/tracker/CVE-2026-66484),
[CVE-2026-66485](https://security-tracker.debian.org/tracker/CVE-2026-66485) and
[CVE-2026-66486](https://security-tracker.debian.org/tracker/CVE-2026-66486).
Reusing already-tested native newc support avoids that extra component. This is
not a blanket security certification of Libarchive or its XML entry points;
ADR-0041's final-image bounds/consumer obligations remain open.

Freeze additional source inputs before their future recipes:

| Component | Version | Verification |
| --- | --- | --- |
| libburn | 1.5.8 | Official HTTPS archive matches frozen BLFS MD5; observed SHA-256 pinned |
| libisofs | 1.5.8.pl02 | Same; archive expands to libisofs-1.5.8 |
| libisoburn | 1.5.8.pl02 | Same; archive expands to libisoburn-1.5.8 |
| squashfs-tools | 4.7.5 | Official release asset SHA-256 digest matches downloaded bytes |

Exact URLs/hashes/sizes are in supplemental-sources.lock.json; 155 total frozen
inputs now. No independent maintainer-signature claim for these additions.
All four archives pass the same safe extraction filter without extraction.
Raw candidate/digest/root/member evidence is .local/upstream-verification/
live-tools. Re-fetch validation uses fetch_security_overlay.py --supplemental.
Keep source archives outside Git and transfer only at a quiescent locked sync.

Squashfs-tools is not in the selected BLFS book. Select the upstream stable
[4.7.5 release](https://github.com/plougher/squashfs-tools/releases/tag/4.7.5),
whose sparse-file corruption fix matters for root images; do not use earlier
4.7 releases or an unreviewed development branch. The GitHub release asset digest
is 547b7b7f4d2e44bf91b6fc554664850c69563701deab9fd9cd7e21f694c88ea6.
It is an additional component, not an upgrade of an existing frozen package.

Use the book's separate libburn/libisofs/libisoburn sources rather than a bundled
standalone xorriso stack. No upstream test suites are advertised for those book
packages, so actual file-only ISO creation/extraction/integrity and BIOS/UEFI
boots must provide acceptance. Never invoke optical/physical-media burning in
development. Future recipes retain original GPL-2.0-or-later grants and per-file
notices; final corresponding-source/license availability remains required.

H10 still needs full live overlay/root discovery/recovery verification. H11
still needs real hybrid ISO construction, manifests, credentials/source/license
audit and checksums. No mock image or private fixture satisfies either gate.

Actual regenerated notice inventory covers 155 inputs/890 candidates, SHA-256
a132d03bdf48d03b7c2b909c51b969da1153b8c1bcf44bd23c90504af1fe5507.
Older content-addressed inventories remain preserved. This is not complete
license review; no new tool is installed by the source freeze.


Prepared Squashfs 4.7.5 recipe follows the verified archive Makefile and
explicitly enables gzip/xz/zstd plus xattrs, with xz default. These compressors
match the required kernel fragment. Disable LZO/LZ4/deprecated LZMA rather than
implicitly enabling every CONFIG preset. Installation uses explicit staged
binary/manpage directories. Upstream prebuilt manuals are retained with a
profile noting their broader optional-compressor descriptions; the installed
tool's help describes the selected build. No source test suite is invented.

The prepared actual native roundtrip uses each selected compressor, compares
root/file metadata and content, numeric ownership, special mode bits, relative
symlinks, shared hardlink inode, sparse allocation and extended attributes.
Extended ACLs must be absent before the separate numeric physical restore and
match afterward (ADR-0048). Its byte/hash fixture includes long UTF-8 and
newline names; no external data or credentials are involved. Failure preserves
the private fixture path for diagnosis; success removes it. This userspace
extraction check does not establish Squashfs kernel mounting, live overlay,
early ACL restoration before services or successful live boot.

H10 requires accepted H09/status and actual kernel/bootloader markers. The
exact gate run through guest Python stdin refused premature execution, exit 1;
raw .local/logs/h10-squashfs-premature-gate-refusal.json SHA-256
4a06550dd602fb73206f335c4845cc13196259184d32f3e03a82aa0420f8d50e.
Shell syntax, Python parsing and 97 local checks pass. The Squashfs native
build/roundtrip itself remains unexecuted until the prerequisites pass.
