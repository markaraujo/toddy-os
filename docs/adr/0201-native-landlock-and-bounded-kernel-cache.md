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
