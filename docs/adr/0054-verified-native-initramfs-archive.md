# ADR-0054: Package and independently verify the minimal live-init archive

- Date: 2026-11-06
- Status: Private native archive roundtrip passed; image integration and boot pending

## Decision and sources

Use the accepted Libarchive 3.8.11 bsdcpio newc writer and Gzip 1.14 to package
the ADR-0052 native runtime, ADR-0053 live /init and its public metadata.
scripts/build/h10/initramfs_archive.py creates a fresh confined staging tree,
checks the installed source-owned archive tools, stages the verified runtime,
and adds only the two reviewed scripts and generated identity/digest files.
Production invocation retains the H09-completed/H10-in-progress gate and the
actual kernel/bootloader success-marker requirements. Its metadata arguments
must come from the eventual real root-image assembly; arbitrary fixture values
are not evidence of a valid compressed root.

References inspected: frozen BLFS 13.1 postlfs/initramfs.html; Libarchive
3.8.11 cpio/bsdcpio.1 and libarchive/archive_write_set_format_cpio_newc.c;
Linux 7.1.8 Documentation/driver-api/early-userspace/buffer-format.rst.
The book packages the shell runtime as newc plus gzip. Linux defines the
070701 header, four-byte alignment, root metadata, device numbers, symlink
payload and hardlink handling. We keep those formats, using the native tool
choice already accepted in ADR-0047 rather than adding another cpio package.

Sort NUL-delimited input names, assign an explicit 32-bit-compatible timestamp,
and use bsdcpio --owner 0:0 followed by gzip -n -9. An independent parser checks
every entry against the staged inventory: exact entry set, content SHA-256,
type/mode, root ownership, timestamp, device numbers and link data. It rejects
duplicates, unsafe paths, truncation, modified data and unexpected trailing
content. The minimal runtime has no hardlinked nondirectory entries; do not
apply that restriction to the full root filesystem. Decompression must recover
the exact checked newc bytes. Preserve the work directory and logs on failure;
an existing or redirected destination is refused before native queries/writes.

Alternatives were unverified archive creation, copying the full root, or a
second archiver. The selected component reuses verified native payload and
provides explicit archive postconditions with a smaller early-root inventory.
It does not claim publisher authenticity or Secure Boot.

## Actual private target experiment

scripts/host/probe_initramfs_archive.py transfers only the current public helper
sources through guest Python stdin, without synchronizing active build inputs.
Two fresh private stages on the target filesystem each produced 44 entries,
including 20 verified native executable/library files, the actual prepared
/init, integrity helper, public fixture metadata, root aliases and two character
devices. Both uncompressed and compressed archives were byte-identical.

The compressed size is 14,270,966 bytes. Gzip SHA-256:
`60f0fdfa0660e674123cf83d430bb1c081e65b189cf62bfc66e1ef91164162a3`.
Newc SHA-256:
`aaeca32cd216151a17d7f942c66f800608f79bff39abd587b9f2662d368da3fa`.
These are private fixture hashes, not release artifacts.

Actual native bsdcpio extraction preserved the exact inventory, bytes, modes,
root ownership, symlink targets and console/null device numbers. The extracted
native shell executed /init's non-PID-1 refusal (exit 1 before mounts), loaded
the integrity helper, and read/hashed the embedded metadata. Deliberate /init
byte corruption and a truncated archive were rejected. Attempted reuse of the
existing work directory was rejected and its original archive remained intact.
Three local regression tests additionally cover malformed content/metadata,
duplicate/traversing names, trailing data and destination preservation.

Raw evidence, including the complete manifest and per-file native provenance:
.local/logs/h10-native-initramfs-archive-probe.json, SHA-256
`c15e8ba599a126709a7dd1234cf1789f7b1325d8efc0c8ae2cf4ac0b1cd4d210`.
The same report is retained under a SHA-256-suffixed immutable filename.
The archive helper SHA-256 is
`8a2a3cdf8995e652cbee934fd5091da06f873b6a9c6affc7786e01d9a96c3732`.
Successful guest fixtures were removed; no installed files changed.

## Limits and remaining acceptance

Repeatability is measured only for these same-filesystem, same-native-tool
inputs. The writer synthesizes inode numbers but retains source device major/
minor fields, so cross-filesystem or independently rebuilt byte reproducibility
is not established. Keep the actual epoch and complete manifest with artifacts.

The fixture contains no Squashfs root, kernel image or ISO. No kernel unpacked
this archive and /init never ran as boot PID 1. Actual image metadata generation,
Squashfs mounting, media discovery, indexed overlay, ACL restoration, Systemd
transition, rescue interaction and BIOS/UEFI/USB tests remain mandatory. H10
remains unstarted; this preparation cannot accept H07, H09 or G1.
