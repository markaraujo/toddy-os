# ADR-0219: Bounded, byte-exact custody of an unused cold backup

Status: accepted
Date: 2026-11-11
Scope: B02 development storage only

## Context

The host retains a 100 GiB free-space reserve. A native graphical boot additionally
requires 512 MiB, and the current boot-scoped Samba/Settings compiler cache must
survive stopping the builder. Seven stationary disposable native-test overlays
have been compressed with exact decompression verification, recovering
86,839,296 bytes. This alone does not cover both requirements.

The explicitly selected `h07-native-math-builder.qcow2` cold backup has no backing
consumers in the actual QEMU image graph. Its logical size is 5,940,445,184 bytes.
Nearly all zero ranges are already sparse; punching those ranges would provide
no useful capacity. Ordinary whole-file gzip needs more temporary disk space
than is available above the reserve. Active images, foundation masters, package
archives and compiler/source data must remain available.

## Decision

Use `scripts/host/phase2_chunk_cold_checkpoint.py` for this exact unused backup.
Hold the existing native-boot and cold-custody controller locks. Verify ownership,
link count, fixed inode/size/mtime, QEMU structure and the absence of backing
consumers. Perform the read-only QEMU structural check before acquiring the
exclusive source-file lock: QEMU itself needs its image byte locks. Acquire the
exclusive source lock and revalidate identity before computing the original
SHA256 and changing its representation.

Rename the original into a private custody directory. For each at-most-32-MiB
range, create a gzip archive, fsync it and its directory, verify decompressed
length and SHA256, and durably record the archive identity before retiring that
source range. Retiring means punching only this already preserved range; the
same source inode remains retained as a sparse custody file. Do not place this
incomplete representation at its original usable image path.

A resumed operation must reconstruct the whole original digest from recorded
archives and untouched source ranges before proceeding. It accepts a pending
retirement only when the actual range still matches the verified archive or is
already entirely zero. Changed source bytes and corrupted archives stop the
operation while retaining all data. Completion requires reconstructing the
original whole-file SHA256 and length again. Preserve every archive and receipt.

This does not change target packages, the accepted foundation, runtime security,
reserve thresholds or the owner's B02 stopping boundary.

## Verification and recovery

Real temporary-file tests cover interruption after durable archive verification,
interruption after punching but before the receipt, complete reconstruction,
corrupted archive refusal and changed unarchived-source refusal. These test the
custody tool, not operating-system acceptance.

To restore the backup when sufficient space is available, decompress the chunks
in recorded offset order into an absent original image path, verify the recorded
whole-file SHA256 and length, restore recorded metadata, then run the same
read-only QEMU structure check with its backing namespace available. Retain the
chunks until restoration is verified. `source.custody` contains holes after
completion and must never be used as a QEMU image.

The separate boot-scoped scratch archive records regular-file hashes, ownership,
mode, nanosecond timestamps, hardlink identities, symlink targets and exact mount
aliases. It retains source, compiler and staged data; old closed fixture sockets
have no restorable payload and are explicitly omitted. Restoring this cache must
restore recorded timestamps and verify the inventory before exposing its aliases.
No fixture, compiler or package transaction is replayed by restoration.

## Next native graphical slice

The next diagnostic uses the installed GDM service on an actual virtual DRM and
input seat, with Virtio VGA, USB keyboard/tablet and QMP scanout. This changes the
concrete seat/input path that blocked the prior headless Shell/Editor probes;
it does not reset those failure budgets or repeat their automation. The isolated
root probe observes the unmodified greeter/session properties and stops GDM.
QMP captures actual guest display frames and sends one pointer movement. It
sets no password or automatic login and does not bypass PAM or owner policy.
A registered greeter and successful service lifecycle alone do not prove visual
correctness or authenticated desktop/basic-app acceptance.
