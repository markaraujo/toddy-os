# ADR-0046: Prepare a gated generic QEMU kernel build

- Date: 2026-11-06
- Status: Prepared only; no kernel configuration/build/install/boot executed

H07's corrected complete DB standard suite is running. H08 remains unstarted.
Prepare the next foundation kernel slice without changing those gates. The
recipe refuses before source movement or target writes unless synchronized
status says H08 completed/H09 in_progress and the actual H08 native base-config
runner succeeded 0/0. The real premature gate probe refuses exit 1. H09 remains
not_started; prepared text/source inspection earns no milestone credit.

Sources: frozen LFS 13.1-systemd chapter10/kernel.html section 10.3; Linux 7.1.8
README, Documentation/process/changes.rst, arch/x86/Makefile, Kconfig files and
scripts/Makefile.modinst from the already-frozen/verified kernel archive. Use
book-recommended x86_64_defconfig plus a versioned fragment rather than copying
the workstation kernel configuration. Disable X86_NATIVE_CPU explicitly:
arch/x86/Makefile selects -march=native when enabled and -march=x86-64 with
-mtune=generic otherwise. This records intended code generation, not empirical
minimum-CPU or physical-hardware support; H09/H12 boots must establish tested
CPU/device qualification. Do not substitute ELF notes for actual boot tests.

The fragment requests the book's systemd/console/security features, built-in
VirtIO storage/network, ext4/GPT/EFI, ISO/USB/loop/squashfs/overlay support, and
virtual display/input. It reserves a loadable dummy network module for actual
Kmod loading/unloading later. Generic HDA is optional virtual audio support;
physical GPU/Wi-Fi/firmware support is untested. No external firmware or builtin
initramfs bytes are requested. Modules and real driver behavior still require
native boot verification. WERROR, IKHEADERS and Rust follow the selected book's
initial-build rationale; no physical-host security setting changes.

Actual source-symbol preflight caught obsolete SND_HDA_CODEC_GENERIC; Linux
7.1.8 uses SND_HDA_GENERIC. Corrected 137 requested symbols all exist, source-only
probe SHA-256 f49e551a79e5bd804368c374a12fccffc6f6b36856191d36083c6780022a5c04.
Fragment SHA-256 9cce660ca4f4c88eb7ef386a58b07fdddcf7f993afef2d0a9506e7061baac7d2.
This does not prove Kconfig dependencies resolve: the actual build must run
olddefconfig, reject unknown symbols or dropped/changed required values, and
record full resolved configuration/hash. A known disabled invisible symbol can
be omitted; requested y/m values must survive. Four boundary tests cover missing
root driver, unknown symbol, native CPU selection and hidden disabled option.
90 local checks pass; no mock is substituted for a required kernel/boot result.

Preserve the prior API-header source tree by renaming it into source recovery,
never remove installed UAPI ownership. Refuse an existing configured/compiled
kernel tree for diagnosis/recovery instead of blindly running mrproper over
completed work. Build/image/modules use bounded -j8 inside the same disposable
target; modules_install has an explicit stage prefix. Remove only exact known
module links to the excluded /sources build tree. Retain full notices/docs,
resolved config, System.map, image and hashes in a native linux-kernel package.
Kernel build identity uses toddy/builder and the frozen-source review date;
byte-for-byte reproducibility is not claimed. The guarded runner now snapshots
/boot too, so future kernel/boot mutations are included in its change evidence.

Prepared postchecks inspect actual image format, installed ownership, config
and dummy module vermagic while explicitly recording boot_validated false.
GRUB installation, actual BIOS/UEFI early boot, native Kmod/Glibc/Systemd retries
and H09 acceptance remain mandatory future work. No build or boot is claimed
by this preparation. Relevant files are scripts/build/h09 and the fragment.


Direct-root GRUB configuration preparation follows section 10.4 of the same
frozen LFS book. Search for the measured ext4 filesystem UUID, then pass the
measured GPT PARTUUID to the kernel. A filesystem UUID alone requires an
initramfs; this direct-root builder entry has none. Do not assume hd0 or vdb
naming remains stable after the target disk is attached to a test guest.
Serial and virtual console output support early-boot evidence. The pure
renderer validates both UUIDs before output and performs no disk writes.

An actual native GRUB 2.14 grub-script-check accepted rendered configuration
using the designated target's measured UUIDs; invalid/injected UUID input was
rejected before output. Only a private temporary config was created/removed.
Raw .local/logs/h09-native-grub-config-probe.json SHA-256
cd3d22a441d102f7cafa89a9f8010064577501ec3579e813e3ea2c3aff677914.
Syntax success is not module availability, successful GRUB installation or
kernel boot. Package/stage ownership, guarded BIOS/EFI installation and actual
early-boot tests remain pending behind H08/H09 prerequisites.
