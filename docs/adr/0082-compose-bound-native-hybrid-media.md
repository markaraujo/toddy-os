# ADR-0082: Compose hybrid media from bound native generations

- Date: 2026-11-07
- Status: Native composer and component inputs verified; production release pending
- Extends: ADR-0078 and ADR-0081

## Decision

Share the actual native GRUB/Mtools/Xorriso composition between the four-mode
loader experiment and the prepared H11 ISO command. This removes duplicated
assembly commands and connects the verified compressed root/initramfs generation
to the selected own-built kernel. No H11 production gate has been opened.

hybrid_media.py creates BIOS El Torito and x86_64 EFI loaders, a FAT EFI image,
and the hybrid BIOS/EFI/GPT catalog using the frozen native tools. It verifies
EFI bytes through FAT readback and every immutable input file through actual
ISO extraction and SHA-256 comparison. Generated BIOS boot-info bytes are
handled separately because Xorriso patches them. Private physical target paths,
protected regular inputs, a canonical search marker and fresh outputs are
required. The static live/recovery menu is parsed by actual native GRUB.

assemble_iso.py requires H10 completed/H11 in progress, the exclusive build
lock, no active dispatcher/sync, accepted kernel/bootloader/media-tool markers
and exact configured own-package versions. It checks archives, records, regular
payload bytes/metadata and aliases. The release initramfs must retain its
verified compression binding; actual gzip/newc readback checks its inventory,
media identity, root digest, epoch and current reviewed early-boot scripts.
Every owned kernel regular file must match the compressed root's manifest,
including modules. Inputs are rechecked after composition. Logs, actual exits,
artifact SHA-256/size and checksum file are retained before completion is set.

Each generation remains separate. Failure never overwrites an older artifact.
ISO creation/readback is explicitly separate from release acceptance: complete
component/source/license inventory, final credential review and native Linux
BIOS/UEFI/USB boot/recovery remain pending. The command is prepared, not claimed
to have successfully assembled the complete foundation.

Alternatives considered: duplicating the successful loader recipe leaves an
untested production variant; trusting filenames alone permits mismatched roots,
kernels and initramfs; handing an independently typed hash to the composer loses
the accepted generation's provenance. Sharing the real composition and checking
its input bindings preserves the existing acceptance boundaries.

## Actual native evidence

The final loader probe used native GRUB 2.14, Mtools 4.0.50 and the private
Libburnia 1.5.8/1.5.8.pl02 tools described in ADR-0077/0078. All four disposable
QEMU boots passed: BIOS/CD, UEFI/CD, BIOS/USB and UEFI/USB. Each executed GRUB
and read its unique ISO marker. No Linux kernel was included or executed.

- Fixture: .local/vm/grub-media-tests/probe-2imk5bgh
- Native evidence SHA-256: 87555e356443a025a76570f593f9ae7dd4167417f62c298def85332d0dd7b656
- Boot result SHA-256: 3de46abfc1feb2b167d268deadedd3e4d18b7cbad88f1c2008f30ce5adc9d563
- Probe ISO: 3,528,704 bytes; SHA-256 3f6d94f14a1fa52d69e74a48508209a6e25f28771e020ecd9ac21ffbec3283ca
- Composer SHA-256: 77cd2ec6350dddd2c9aa78ed054efadef18f5c9c7799b8a17741d4ab09906959
- Prepared assembler SHA-256: 8b75f1bf53100dd51bccddc115d0d807dbe9a1649c5d94c6a47c793b917d7d22

Seven composer negatives rejected marker syntax, missing identity, writable
input, redirected input, special FIFO, existing early configuration and reuse
of a completed generation. Rejections preceded writer stages and preserved the
outside sentinel. Installed Dpkg state and GRUB payload remained unchanged.

The actual thirteen-entry native Squashfs/45-entry initramfs experiment also
passed the new ISO-input verifier. Its assembly journal is explicitly a metadata
fixture; the compression and archive/readback are real native operations.
Six new negatives rejected missing binding, wrong identity, wrong epoch, wrong
entry count, corrupted archive and changed reviewed init script. Together with
fourteen compression and sixteen binding cases, 36 negatives pass.
Raw report SHA-256:
5869d2a6b8358f5f92884e7a1236f858b81904ce30f49a125de7964ce9424df2
(.local/logs/h10-root-compression-<sha256>.log).

Production preflight correctly rejects the premature ISO gate. The package
validator positively checks all 1,315 regular files and recorded aliases of
actual own-built GRUB, and rejects a different version. Other native kernel/H11
package prerequisites remain pending. Fourteen preflight negatives pass; full
source readiness still refuses the unfinished shared Info index. Raw report:
60c2317352898db0846fe3125ad8f7d1eeb49034a34e245798d7c62c2ba67939
(.local/logs/h10-root-assembly-preflight-<sha256>.log).

Reproduce with the three host probes documented in BUILD.md. Sources remain
the frozen GRUB 2.14 grub-mkrescue composition and Mtools/Xorriso manuals cited
in ADR-0078, plus the archive/root formats cited in ADR-0081. No new dependency,
package upgrade, accepted full ISO, native Linux boot or physical test is claimed.
