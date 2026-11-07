# ADR-0085: Compile the frozen kernel in a private native fixture

- Date: 2026-11-07
- Status: Native compilation and BIOS/UEFI diagnostic boots verified; production acceptance pending
- Extends: ADR-0046

## Decision

While the corrected complete Berkeley DB suite runs, extend the existing private
kernel configuration experiment to actual compilation and module staging. Use
the native final compiler, frozen Linux 7.1.8 source and unchanged reviewed
139-option fragment in a fresh protected directory under sources/recovery.
This is independent feasibility work: do not dispatch the H09 package recipe,
install into the target's boot/module directories, modify boot sectors or reboot
the builder. H07 remains the active story; H08/H09 prerequisites and acceptance
are unchanged. A private binary is not an accepted kernel package or boot result.

The frozen LFS 13.1-systemd section 10.3 prescribes clean source preparation,
configuration, make and modules_install. It also explains that retained builds
should preserve object files for incremental rebuilds. Follow those steps with
an explicit private INSTALL_MOD_PATH. Preserve the prior API-header tree and
ADR-0046 configuration experiment. Do not import the builder's kernel config.

Alternatives: waiting leaves independent compiler compatibility unexplored;
dispatching the final recipe would violate its prerequisite gate; building on
the workstation would test a different compiler/library environment. A private
native build exercises the intended inputs without changing installed packages.
It costs additional disk space and must not be mistaken for final packaging.

## Resources and recovery

At launch the 12 GiB builder had 11,167 MiB available, zero swap use and 123 GiB
free on its designated target. Limit make to two jobs, preserving capacity for
database tests and unrelated host workloads. The target identity guard and
10 GiB free-space floor run before work. The source archive is checked against
the frozen SHA-256 before extraction:
ff01dcb449279d5b4cfccdb01fee639cf5ff1803f1749a77844dd33915422c49.

scripts/host/probe_native_kernel.py transfers only private probe inputs, not a
global build-input synchronization. The native driver records per-stage intent,
PID, log hash, timeout and actual exit. Each attempt retains separate logs and
failure evidence. Successful stages have exclusive completion records; resume
verifies their command/log identity and preserves compiled objects. Source,
fragment/checker/driver and installed package database hashes are rechecked.
The fixed build identity matches the prepared production recipe. Byte-identical
reproducibility is not claimed.

The launcher refuses another live fixture and refuses resuming a locked driver
or an unfinished stage whose detached child still exists. A missing supervisor
alone is not permission to restart. A partial extraction remains for diagnosis;
do not delete it automatically. A changed compiler/package environment requires
review rather than silently reusing objects. Final artifact checks require real
x86 Linux/EFI image recognition, exact release/configuration, a staged dummy
module with matching vermagic, artifact hashes and unchanged package status.
They cannot prove successful boot or module insertion.

## Actual evidence

The private driver started at 09:48 UTC. Source verification/extraction and
configuration/preparation exited zero. Native GCC reports 16.2.0; the exact
release is 7.1.8-toddy. At that first observation the make stage was live and
compiling native objects; it did not yet establish a complete image or boot.
The later terminal build and diagnostic boot results are recorded below.

- Launch report SHA-256:
  65c1320d6a7598389e536d9dc2b1f1e3509efae8f9b1643dcd0c4ab61a17db4f.
- Actual configuration/preparation log SHA-256:
  8018b5bfccb7235f867dc095d61d15564b55031c4bb7743b4ecb3f85775850f1.
- Live collection report SHA-256:
  03df8e3d2f282a69c970c0c213ddfe4a7119a1ae40eb07b860289ff22bfe6818.
- Both native concurrent-start and active-resume attempts refused; report SHA-256:
  59d3eee1d2d961184cade34f72de39d118788e56f732bafb9aa60b3c471c6425.

Raw reports remain in ignored .local/logs/h09-private-kernel-* files. The exact
fixture, PID and next command are in the local checkpoint and recovery notes.
Collect and inspect terminal exits, artifacts and postconditions before any
later claim of successful compilation. Production packaging and complete native
boot tests remain mandatory behind H08/H09.


## Prepared diagnostic boot, distinct from foundation boot

The next independent experiment uses the completed private kernel and a tiny
native static-libc diagnostic PID 1 in a separate diskless QEMU guest. Frozen
Linux 7.1.8 init/main.c implements rdinit and /init; its initrd documentation
explains compressed cpio initialization, and include/uapi/linux/reboot.h defines
guest power-off. The prepared probe uses these interfaces without changing the
kernel configuration or final H09/H10 boot recipes.

Before creating guest artifacts, require the kernel producer to be terminal
with actual exit zero, all five completed-stage exits/log hashes, unchanged
inputs/native package status and current artifact hashes. Build diagnostic C
with the native GCC/static libc, package it and the actual dummy.ko using native
bsdcpio/gzip, and verify transferred kernel/initramfs hashes. BIOS and pinned
OVMF runs use a generic qemu64 CPU, no disk/network and separate firmware
variables. The existing boot-test lock/container ownership helpers protect
other guests; only the newly created labelled containers may be stopped.

The real diagnostic assertions will check kernel/firmware identity, volatile
file write/read, user/mount/IPC/network namespace creation and actual native
module insertion/removal. A per-invocation token, exact success marker, no
failure/panic and actual QEMU exit zero are all required. Power-off occurs
inside this disposable guest. This is not Systemd/login, GRUB/ISO boot, the live
root/overlay, native compiler-runtime regressions, installation or G1 acceptance.
Those complete-system checks remain mandatory.

Native preparation evidence so far: the diagnostic C compiled with -static,
-Wall -Wextra -Werror and no ELF interpreter. Execution as an ordinary builder
process correctly returned 125 before mounts or reboot. Raw preflight SHA-256:
ed2b6b692cf8b0cd0eab6a5e77b4d5735d1770a6b23baae0edd554e3a9f1b234.
The exact helper refused the still-live kernel producer before preparing guest
payloads or starting QEMU; refusal log SHA-256:
57d069f21e0aff58b41c950819a454a2f8a7e160a3582bf6514d8b33bce72050.
That early refusal did not establish successful boot. After compilation
completed, the actual diagnostic boots passed as recorded below.

## Terminal build and actual BIOS/UEFI result

By 10:02 UTC, the kernel driver, all five native stages, boot driver and its
supervisor had actual exit zero. Twenty native modules were staged privately;
the image is 15,553,536 bytes. Both diskless BIOS/UEFI guests ran the compiled
7.1.8-toddy kernel and passed every diagnostic assertion, including actual
module insertion/removal and namespace creation. Serial logs and QEMU states
were independently inspected after the supervisor finished. The complete
artifact/log hashes and limits are in
[H09 private-kernel evidence](../evidence/H09-private-kernel.md).

The prepared final package recipe was not dispatched. Full Systemd/root/ISO
boot, Kmod userland checks and release acceptance remain pending. Keep H09
not_started until H08 passes, and retain the completed private build for
inspection/recovery instead of restarting it.
