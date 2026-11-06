# ADR-0046: Prepare a gated generic QEMU kernel build

- Date: 2026-11-06
- Status: Private native configuration/preparation verified; kernel image/install/boot pending

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


Prepared boot-config recipe additionally requires actual h09-kernel success.
It packages /etc/toddy/grub.cfg as a preserved conffile and owns the relative
/boot/grub/grub.cfg symlink; this honors the existing strict /etc conffile
policy rather than leaving boot configuration untracked. The recipe itself
has not been dispatched. Its postcheck requires both native GRUB platform
module sets (part_gpt/ext2/search_fs_uuid/serial/linux/normal); all twelve
currently exist, but that alone is not a boot result.

A separate actual native probe formatted only a private 16 MiB regular-file
ext4 image, populated a configuration and the exact relative symlink with
native debugfs, then read /boot/grub/grub.cfg through native grub-fstest.
The observed bytes matched and native grub-script-check passed (exit 0).
No block device was written or mounted; temporary image/data were removed.
Raw .local/logs/h09-native-grub-config-link.json SHA-256
bc3303a6c379c3c2b0be539d96d06d28e5daf36c8467ea297bcc098992243e31.
This validates the filesystem link channel, not execution of a GRUB core or
a kernel. BIOS/EFI installation and early boot remain unexecuted and required.


Prepared bootloader recipe now follows LFS 13.1 section 10.4 for i386-pc and
x86_64-efi installation. It requires actual kernel/configuration success and
the H09 gate, repeats the existing virtual disk serial/size/root guards, and
checks measured GPT BIOS/ESP types, parent disk, FAT label and mount ownership.
Unexpected existing platform/EFI payload or recovery evidence causes refusal.
It preserves the first MiB, BIOS partition and partition table before writes,
checks that the table and owned configuration/kernel bytes stay unchanged,
and uses --removable --no-nvram for EFI. Generated files plus the MBR receive
an explicit hash inventory; a read-only ESP remount postcheck compares them.
File-format/hash success explicitly does not establish actual BIOS/UEFI boot.

Native GRUB 2.14 help and read-only target inventory confirmed the requested
options and partition identities. The recipe remains undispatched: current
build inputs deliberately lack H09 while BDB owns the lock. An initial script
probe refused at that missing gate file before reaching disk operations; raw
.local/logs/h09-bootloader-unsynchronized-input-refusal.json is preserved.
Running the exact gate bytes separately through native guest Python stdin
then produced the intended H08/H09 status refusal, exit 1. Raw gate report
.local/logs/h09-bootloader-gate-refusal.json SHA-256
c018c4c41ec964098f2d583799cd3269a87d7b3344902764dffe4c7a68edb37e.
Shell syntax, Python parsing and 97 local checks pass. No bootloader installed,
no boot sector written, no kernel/boot acceptance credited by these probes.


Prepared toddy-boot-config now carries the frozen book lock and an explicit
build-target profile alongside LFS notices. Its measured UUIDs must not be
reused as live-media or installed-system defaults; image assembly and the
installer must generate their own configuration. Component inventory maps
version 0.1 to the same LFS-instruction/original-Toddy pending-D10 classification
as base configuration. No new license grant or completed legal review is
inferred from retaining the upstream notice. Package build remains pending.

ADR-0051 adds explicit DMI/DMI_SYSFS for the ephemeral test guest's documented
Systemd SMBIOS channel. The current fragment has 139 source-verified symbols;
its hash and native generator preflight are in that ADR. The earlier 137-symbol
hash remains historical evidence. At that earlier source-only checkpoint, configuration resolution had not run.
The new options do not waive any existing boot gate.


## Native configuration preparation and release-string correction

A private source tree under /mnt/lfs/sources/probes was extracted only after
verifying the frozen Linux archive SHA-256
`ff01dcb449279d5b4cfccdb01fee639cf5ff1803f1749a77844dd33915422c49`.
The native GCC 16.2.0 environment ran mrproper, x86_64_defconfig, the exact
fragment merge and olddefconfig with two jobs. All 139 requested settings
survived. Resolved configuration SHA-256:
`3ad1bf1ce1e1a844ac35a5c0c9769536bff6e30d9ae75dd20ee2341a9f544e0e`.
No active source tree, installed package or H09 build gate was changed.

The next query exposed a prepared-recipe defect: make -s kernelrelease returned
7.1.8 even though .config requested CONFIG_LOCALVERSION="-toddy". Its generated
include/config/auto.conf still held the earlier defconfig values. Frozen
Makefile's no-sync-config-targets explicitly includes kernelrelease, and
scripts/setlocalversion reads auto.conf rather than .config. Its own diagnostic
instructs running make prepare before querying an unprepared release.

Run make prepare after configuration verification and setting the reproducible
build identity, before the recipe's exact release check. The native private
retry passed with 7.1.8-toddy and the same resolved configuration hash. It built
configuration/preparation utilities and generated headers, including Objtool;
no vmlinux, bzImage, installed modules or boot result is claimed. It does not
bypass H08/H09 prerequisites or grant H09 acceptance. The real recipe must
repeat preparation, then build/stage/install and validate actual boot artifacts.

Evidence .local/logs/h09-native-kconfig-probe.json retains the initial command
log/exit, original requested/resolved configuration, corrected preparation
log/exit, synchronized auto.conf and kernel.release. SHA-256:
`f597a18e1696b8775b556b30c4c68a35ea2152d7c28bc933426e88e08a3f5106`.
Both private drivers exited 0; the initial experiment recorded the unexpected
release, and the corrected experiment asserted the exact intended release.
The source tree and logs remain in the printed private probe directory for
recovery; only temporary configuration/build-preparation files were produced.
