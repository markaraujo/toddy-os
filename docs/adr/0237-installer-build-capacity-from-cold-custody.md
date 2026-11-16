# ADR-0237: Prepare installer build capacity from cold checkpoint custody

Status: source preparation only; coordinator execution and measured capacity pending
Date: 2026-11-16
Scope: reversible development-host checkpoint representation; no guest/release change

## Context

The coordinator's actual native Qt 6.11.2 inventory reports Wayland/scanner
disabled and no WaylandClient/platform plugin. A conditional same-version QtBase
rebuild plus composed image/install/ISO work needs about 30 GiB more host space.
The 100 GiB host reserve plus 512 MiB graphical margin remains unchanged.

A read-only audit found no direct backing consumer of
`checkpoints/h07-native-services-target.qcow2` and no backing in that image.
This is the superseded historical 86-package H07 recovery checkpoint. Earlier
RECOVERY text still calls it the latest pair, but later accepted h07-final-base
and h09-boot-ready boundaries supersede it. The coordinator explicitly confirmed
that superseded historical recovery checkpoints qualify for reversible byte-exact
representation custody. They are not expendable failures: every original byte,
receipt and reconstruction hash must remain retained. Preserve h07-final-base,
h09-boot-ready and current H13/B02 directly usable recovery/backings as-is.

Fixed candidate identity: inode 11832773, size 61,737,336,832 bytes,
mtime_ns 1793953144185127409, UID/GID 1000, one link, mode 0644, no xattrs.
Physical allocation is 59,699,474,432 bytes. Read-only Docker `/vm:ro` QEMU
check returned 0 with zero errors and image-end-offset 61,737,336,832. The full
[audit/graph](../evidence/B12-installer-capacity-preflight.json) retains this
identity and the protected current/primary images. No candidate was moved or
punched. The current complete digest must be recomputed during actual custody
and must match historical SHA-256
`536109a5db3f6f2c44620c33f954fc2ce96570636c9a6b33bbc1b708e57785fd`.

## Decision

Add only an explicit `installer-capacity` profile/context to the qualified
ADR0219/0223/0227 tool. Preserve old profile tuples, contexts, receipts, archives
and accepted evidence. The new profile retains the stricter 100 GiB + 512 MiB
floor and records original access time/empty xattrs for restoration. Its full
current digest must match the historical H07 receipt before source rename.
The existing 32 MiB gzip/fsync/hash/manifest-before-punch protocol is unchanged.
Source preparation runs no custody initialization, rename, punching, deletion
or restore, and changes no existing foundation/B02 disk identity.

Before execution, revalidate no active consumer, actual namespace graph, fixed
metadata, read-only QEMU check, native-boot/custody locks, exclusive source lock,
free space and original complete SHA-256. New consumers or changed bytes stop
the operation. Record actual controller boot/PID/start identity and producer
hash. Resume an interrupted operation only with its exact original producer
after reconstructing and verifying the original complete digest. Completed old
receipts are immutable and never replayed with a changed script.

The original services target path becomes unavailable only during actual
reversible custody; `source.custody` is not bootable after range retirement.
Keep all verified gzip chunks and the sparse original inode. Completion requires
full reconstructed original length/hash, not a free-space estimate. Measure
reclaimed bytes before allocating Qt/build/ISO scratch; 30 GiB is a goal, not a
claimed result. The [restore guide](../cold-installer-checkpoint-restore.md)
requires an absent output, exact ordered verification, preserved metadata and
read-only QEMU/paired-checkpoint checks before reuse. Amend historical recovery
representation notes only after actual custody completion, never by deleting
accepted evidence or relabeling old validation.

## Validation and limits

Focused real temporary-file tests cover interruption before/after punch, archive
corruption/changed source refusal, new selection/prior-profile preservation,
and restoration into a new absent file with exact data/mode/mtime and all
archives retained. These test host custody, not OS acceptance. Preparation
recovered zero bytes. No guest, physical disk, target package, model, display
security policy or story acceptance changes.
