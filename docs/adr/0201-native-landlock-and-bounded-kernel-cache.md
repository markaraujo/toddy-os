# ADR-0201 — Native Landlock requirement and bounded private kernel-cache preparation

Status: decision accepted; resource/primitive preflight qualified; kernel change pending.
Date: 2026-11-10 · Story: B02

## Concrete requirement

Frozen LocalSearch3.11.1, official archive SHA256
`7b39a6c28a8acf2b172f15b2fb5ee7c7a3764c447c2f4a14caa239b7ebe61942`,
source `src/common/tracker-landlock.c` queries the kernel ABI and must apply its
ruleset for metadata extraction. Its actual Meson contract supports explicit
`landlock=enabled` for an isolated distribution build, bypassing only a build-host
kernel probe, not the target runtime requirement. The frozen BLFS13.1 chapter
`gnome/localsearch.html` requires SECURITY_LANDLOCK and recommends retaining both
Landlock and seccomp. Native7.1.8-toddy currently has SECURITY/SECCOMP/FILTER=y but
`# CONFIG_SECURITY_LANDLOCK is not set`; CONFIG_LSM text alone does not enable it.
Do not disable the sandbox or replace the required runtime with a compile-only
file manager. No native extraction/desktop acceptance is claimed.

A same-version B02 kernel configuration revision is justified by this concrete
requirement. Preserve the accepted G1 ISO/history, frozen Linux7.1.8 source,
current owned kernel/archive and original2.7GiB kernel source/build cache. This is
an affected kernel feature change, not a foundation restart or baseline upgrade.
Actual configuration-delta, image/module, boot and unprivileged Landlock allow/
denial/recovery evidence is required before qualification. No kernel config,
image, installed package or boot entry has been changed at this checkpoint.

## Resource and isolation path

Target16GiB/host100GiB reserves remain. A full cache clone would exceed current
headroom. Qualify metadata-only private copy-on-write rather than modifying the
accepted cache. A disposable4MiB synthetic lower file demonstrated actual UID101,
private namespaces, no effective capabilities/no-new-privileges, denied source
and /usr writes, absent package DB and successful private upper write. Original
lower content/owner/mode unchanged. First own probe incorrectly expected0st_blocks
and marker value y; real xattr metadata occupies8blocks and an empty metacopy
marker. Finally unmounted the failed probe; actual unmounted state and unchanged
lower verified BEFORE new probe2. Probe2 requires marker presence, <=8blocks and
SEEK_DATA ENXIO to prove no file data extents before writing. It passed. Failure
and exact corrective command are retained; no real kernel/cache was involved.
The compiler harness adds only the exact synthetic input/work child-overlay bind,
with filesystem/ownership guards, retaining normal /usr/source read-only and
single-writer behavior. The real kernel-cache profile still needs preparation
and an exact guarded bind; this primitive result is not whole-kernel validation.

A dedicated768MiB virtual build file is fully preallocated under .local/vm/phase2,
not attached or formatted yet. Host free after allocation108053454848bytes exceeds
100GiB. Discard is explicitly ignored so later writes reuse reserved host blocks.
Default VM start remains unchanged when no scratch exists. Optional attachment
accepts only the fixed project filename/format/serial/size, original inode/device,
regular owned private single-link file and full allocation. Eight focused guard
tests cover default behavior, valid fixed path, partial prep, symlink, wrong inode/
size, external/pending declarations, hardlink/shared permissions. No physical
host disk, global security/power policy, paid storage or credentials are involved.
Guest formatting is NOT authorized by a receipt alone: later preparation must
verify exact virtual serial/size/blank state, record a fresh intended UUID before
any mkfs and reconcile uncertain results before retrying. Retain one guest writer.

[Actual primitive/resource proof](../evidence/B02-kernel-COW-preflight.json).
A kernel build should retain full checkpoint/final-image integrity and controlled
native transactions. Source/cache before-and-after identity, qualified isolated
unprivileged build, exact configuration delta and native proof remain mandatory.
The persistent diagnosis ledger is retained; do not restart its budget on resume.


## Verified scratch attachment and filesystem — 2026-11-10

The fixed preallocated virtual scratch was attached after verifying the only
builder idle and the GExiv2 native transaction terminal0/0. Controlled restart
produced boot3a77a52a-5994-4f9c-9a57-d8582921275c; the six existing scratch
filesystems, Systemd read-only source and Glycin companion binds were restored
with new receipts, never recreated. A host-side exact-command membership check
initially used the serial substring as a whole argument and failed before
restoration; actual QEMU args confirmed the full device argument, corrected once.

The guarded preparer accepts only the dedicated virtual serial/768MiB whole disk,
no children/mount/signature/UUID, and reads every byte to prove blankness. It
records an intended UUID before invoking mkfs, refuses any existing receipt, uses
no force-format flag, and mounts nosuid/nodev. Actual UUID
`c6c4176d-faed-4ee3-9ae0-94914a0af666` is mounted at kernel-landlock-1 with
758177792 initial free bytes. Four new identity guard tests passed. No physical
disk or accepted root was formatted. [Evidence](../evidence/B02-kernel-scratch-mounted.json).

Kernel source/cache/config/package/boot remain unchanged. This resource result
does not qualify the real kernel COW profile, Landlock feature or desktop. Next
prepare immutable baseline hashes and the exact isolated real-cache view; retain
the128MiB scratch reserve and actual boot/security proof requirement.


## Actual private compile and bounded capacity recovery

Real-cache COW preparation and UID101 denial checks passed. Only directory and
generated-output ownership metadata was promoted; all original111558 cache
entries/2599875499bytes remain byte/metadata identical after compilation,93715
pristine source entries unchanged in both views. Exact config delta enables
Landlock and its selected SECURITY_PATH. Preserve the no-Rust original kernel
profile with explicit `make RUSTC=false`: init/Kconfig detects Rust unconditionally
and Makefile overrides an environment-only setting. Both precompiler failures
are retained; no extra metadata was accepted or original compiler replayed.

The768MiB scratch guard interrupted final link, preserving partial outputs. A
single256MiB virtual-file extension/QMP resize/online ext4 grow retained the same
UUID and100GiB host reserve. Full preallocation was reconciled after geometry
update released a small physical extent. Fixed-path/inode/size/original receipt
checks refuse pending/mismatched growth; no physical disk or target root resize.

Incremental build4 completed compiler0 in15.003s with no configuration replay.
Its polling minimum152457216B missed a late allocation: actual final free was
88567808B, below the scratch reserve. This is explicitly not final reserve proof.
Canonical monitoring now records final free. After terminal/source/artifact
proof, only five named private linker intermediates were retired, preserving
all final artifact hashes and restoring388354048B free. Do not replay retirement.
[Compile evidence](../evidence/B02-kernel-landlock-compile.json) retains all exits,
partial failures, growth/cleanup manifests and source/artifact identities.

Native static-libc UID101 diagnostic preparation passed. BIOS/UEFI Landlock,
seccomp, namespace and module checks are prepared but NOT YET RUN. No kernel
package/boot file has been installed/updated; no installed-Systemd/desktop/ISO/
hardware/fresh full-source reproducibility acceptance is claimed.


## Verified native diagnostic boots

Actual Landlock candidate diagnostic BIOS+UEFI boots0/OOMfalse; both ABI9/UID101 rulesets2/allowed roundtrips4/denied reads4/writes4/creates4/fresh-process recoveries2/seccomp denials2/namespace/module insert-remove0. Complete token-bound serials; no target/builder/physical disk or network attached. All20 owned original module payloads byte-identical to candidate. Installed kernel/package/boot-entry/Systemd/desktop/ISO/physical acceptance still pending. [Native evidence](../evidence/B02-kernel-landlock-native.json). The diagnostic source and candidate hashes are bound to commit ef1f40a; no installed-system or stable-release gate is awarded by this focused proof.
