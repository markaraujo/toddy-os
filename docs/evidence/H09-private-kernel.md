# Private native kernel compilation and diagnostic boot

Date: 2026-11-07. This is independent preparation under ADR-0085, not acceptance
of H09, H12 or G1. H07 remains active; final kernel packaging still requires H08.

## Build actually executed

The isolated native driver completed all five stages with exit zero: frozen
source extraction, configuration/preparation, compilation, private module
installation and artifact checks. Its own actual terminal exit was zero. The
build used GCC 16.2.0, Binutils 2.47.20260726, two make jobs, x86_64_defconfig and
the unchanged 139-option project fragment. Kernel release: 7.1.8-toddy.

The source archive SHA-256 is
ff01dcb449279d5b4cfccdb01fee639cf5ff1803f1749a77844dd33915422c49.
The image is 15,553,536 bytes, SHA-256
3ccb8a6c3f3e125542e3d6892e242af1d37e873833de27ee32e3951871a723a1.
Twenty modules were staged privately, including dummy.ko, SHA-256
eadf6e162cd0fa3cb8ec6c1a4ffa16fce22a16015e6374fbc5cd92f64caa44ab.
Native GRUB recognizes both Linux x86 and x86_64 EFI image formats. Requested
configuration and release checks passed, as did dummy's vermagic check. The
installed native package database remained unchanged.

| Evidence | SHA-256 |
| --- | --- |
| Native result.json | 17a1387dc7d5936ece1982663e20628d50bf662d5b234db46141f38c6f806ae1 |
| Complete collected native report | 6fc83f5698592163c49cc47e6ca5cf673be5a3a91ce708cf1a5e6ea741027309 |
| Compilation log | 8f390aea91e73c46e476b96645f21629d2773da60170c0a45f71c7e59b9a693a |
| Private module installation log | 1b7c9317aa8cb3d1f0211e40bccbdc79eeb404944744fd1e083a3725deb0f4a0 |
| Artifact checks log | f513092ef9b94cad9f150bcad1979e3a21e540f2f8f4eebef7c81cb41284fc14 |

## Actual diagnostic VM boots

After terminal build verification, a separate native helper compiled a static
diagnostic PID 1 and archived it with the actual module using native bsdcpio and
gzip. Kernel and initramfs were copied to private host artifact storage and
rehashed. The initramfs SHA-256 is
ac9b8445d3e63454dbecc6b0fc12623613bbba29b492343daf5c75dd2a1e3596.

Both disposable QEMU/KVM guests passed: BIOS and pinned OVMF UEFI, generic
qemu64 CPU, two vCPUs, 1 GiB RAM, no disk and no network. Each used the compiled
kernel through QEMU's direct -kernel/-initrd channel. Actual serial output
confirmed Linux 7.1.8-toddy, the native compiler/linker and expected firmware.
Each run reached the unique success token, powered down and returned QEMU exit
zero without OOM or panic. Only the test-owned containers were removed; serial
logs, exact invocation, firmware-variable files and exit records remain.

Actual guest assertions passed in both modes:

- Mount proc, sysfs, devtmpfs and a volatile tmpfs.
- Write, synchronize and read back the exact volatile payload.
- Fork a child and create user, mount, IPC and network namespaces.
- Insert the native dummy module with finit_module, observe it in sysfs,
  remove it with delete_module and verify its absence.

These are real guest syscalls, not simulated reports. The diagnostic refuses
execution outside PID 1/root; its native preflight returned 125 as intended.
The boot preparer also refused the initially live kernel producer. These
negative checks are documented separately in ADR-0085.

| Evidence | SHA-256 |
| --- | --- |
| BIOS serial log | 526f81c7d11c2590cca581903dfba11d049fda7176d77b3fef434819893c30fb |
| UEFI serial log | 8adaa62a58d47fca7ef0276245e9bd63f5a29763bbdc3a6117c138d443bd3b6f |
| Boot result.json | 8c5fc6b719a8c466f9b1adb474c5c3568e0686e0618451270a33a6e99abc151e |
| Host boot driver log | 185f0b150d4652592f20d0e25f755c7b2f4ad077654cc84358c5cf2c21832f66 |

## Scope and remaining acceptance

This does not boot the complete foundation or a release ISO. PID 1 is a focused
diagnostic, not Systemd; no login, signed package repository, GRUB-mediated
kernel boot, live root/overlay, persistence or installer is accepted here.
Full Glibc/Systemd/Kmod regressions in the final booted root remain required.
Native module syscalls do not substitute for the Kmod program's final checks.
No physical hardware or signed Secure Boot result is claimed.

Reproduction commands and the exact retained fixtures are in docs/RECOVERY.md.
The normal production kernel/bootloader recipe and full boot matrix remain
gated on their declared story prerequisites. Preserve these completed builds;
do not restart them to recover an interrupted observation.
