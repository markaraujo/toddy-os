# ADR-0081: Bind initramfs generation to verified root compression

- Date: 2026-11-07
- Status: Native component/readback and premature-gate checks passed; full image pending
- Extends: ADR-0053, ADR-0054, ADR-0072 and ADR-0076

## Decision

Integration inspection found two pending problems in the prepared initramfs CLI.
It always required H10 in progress, preventing regeneration for H11's changed
release root after optional QA removal. It also accepted an independently typed
root digest and timestamp, with no enforced connection to verified compression.
No production image had reached this point; this was a preparation defect, not
an observed Linux boot failure.

Give the CLI explicit compression-report and fresh-output arguments, with a
separate --release switch selecting the existing H11 gate. The default keeps
the H09-completed/H10-in-progress gate. Hold the exclusive build lock and refuse
active dispatch/synchronization markers. Require physical protected staging
paths and disjoint assembly, compression and initramfs generations. Do not
reuse or overwrite H10 output to produce the release archive.

After actual native compression/readback, its production CLI records hashes of
the accepted assembly journal and final image manifest, plus the assembly profile.
Recheck those inputs before binding the report. Component-only compression has
no such binding and cannot feed the production initramfs command. An interrupted
handoff with compression complete but missing binding remains ineligible.

The new initramfs_input verifier requires successful compression, matching
H10/H11 profile, unchanged successful assembly journal and current assembler
identity, the unique final manifest action and identical compressed-source
manifest. Require all three native stages in order with zero integer exits and
unchanged logs. Check the actual rootfs.squashfs path, size and SHA-256. Inputs
must be root-owned, non-writable by other users, canonical, regular and on the
target filesystem. Derive the embedded digest and archive epoch from this
verified generation, not separate operator-supplied values.

Generate the existing native newc/gzip archive, then recheck every bound input
before atomically adding compression_binding to its manifest. A partial archive
manifest without that binding is not a production handoff. Public media identity
is still supplied once by the media builder and must match the ISO identity
file; this is pairing/integrity metadata, not publisher authentication.

Alternatives: manually retyping hashes allows mismatched generations; loosening
the H10 gate globally permits premature construction; reusing a fixed output
path loses intermediate evidence. Explicit profile gates and preserved input
bindings maintain the existing state machine. No package version, critical test
or acceptance criterion changes. Full assembly, credential/license review and
native boot are still independent requirements.

## Native evidence

The extended compression probe uses the real private source-built Squashfs 4.7.5
and accepted native ACL/runtime/archive tools. Its thirteen-entry filesystem is
a real compressed/extracted/restored metadata fixture, not a foundation root.
Only the assembly journal is a deliberately constructed metadata fixture, clearly
labeled in the report; no fake journal is passed through a production gate.

Both assembly-profile bindings pass against the actual compressed artifact. The
bound root digest is embedded in a real native bsdcpio/Gzip initramfs; independent
gzip/newc readback verifies all 45 entries. Compressed archive size: 14,272,304
bytes; SHA-256 47fa5a7401ede227d046fdddc14a610f11fcafc640e900e9ea7b679b81f755ed.
The small Squashfs fixture is 61,440 bytes, SHA-256
1b9755f81854f66102e5298e647efe255665031a61b6a0840d6229659379e702.
Neither artifact is a release or contains a boot-tested foundation.

Sixteen binding negatives pass: missing binding, incomplete compression, wrong
profile, failed/missing native stage, invalid epoch, wrong artifact digest,
changed assembly journal/manifest/log, another source manifest, corrupted root,
input mutation during archive creation, writable/redirected root and release
input presented as H10. Existing fourteen compression/readback negatives and
two fresh identical compression generations also pass. Installed Dpkg status
is unchanged. Complete successful report SHA-256:
b2be90e5bcb0b38c27b7caf310cdad6553ecbf838b02033ad3de048c2f89b33d
(.local/logs/h10-root-compression-<sha256>.log).

Actual CLI preflight separately refuses both initramfs profiles under unfinished
H07 before creating output. Assembly/compression gates and six layout refusals
also pass, twelve negative cases total. Actual source readiness still refuses
the unfinished shared Info index; complete positive assembly remains unexecuted.
Preflight report SHA-256:
ae610b00eb6c0d5a47af78ee53495d5f529a51de0fcff6a27bafc2c257ce9881.

Verified component SHA-256 values:

- initramfs_input.py: bad6739086d7fb76112cb5fd702e6191c1dd7f7db30b31c860b4d2ef45f801bb
- initramfs_archive.py: a394d488275fbd60f067a47136bfde971594cc7086fbe7bedbe3eb9ab8730d1a
- compress_root.py: 550b2eda863e5a69539e1179d3a94603a8e64f533670588a8a7133d00ec411c2

Reproduce with `python3 scripts/host/probe_root_compression.py PRINTED_SQUASHFS_FIXTURE --initramfs`
and `python3 scripts/host/probe_root_assembly_preflight.py`. Successful private
fixtures are removed after content-addressed evidence is saved; failures remain.
No global inputs or active Berkeley test source were synchronized or changed.

## Sources and limits

The runtime/archive formats remain the frozen sources documented in ADR-0054:
BLFS 13.1 postlfs/initramfs.html, Libarchive 3.8.11 newc writer and Linux 7.1.8
early-userspace buffer format. The actual Squashfs format, extraction and ACL
contract remains ADR-0076. This change connects those already exercised native
components; it introduces no new upstream dependency or format deviation.

Checksums bind private trusted build records; they are not a signature against
a malicious administrator. The positive experiment proves the component chain
on a small real filesystem, not the complete production pipeline. The accepted
full assembly, installed Squashfs package, correct media identity, actual kernel
unpacking and complete BIOS/UEFI/USB live behavior remain mandatory.
