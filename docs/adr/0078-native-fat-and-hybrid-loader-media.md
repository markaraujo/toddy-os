# ADR-0078: Native FAT construction and explicit x86_64 hybrid loader media

- Date: 2026-11-07
- Status: Private native FAT and four loader boots passed; foundation gates remain pending

While the two complete Berkeley DB suites run, validate the already-frozen
Mtools/GRUB/Libburnia components in private targets. H07's installed package
boundary remains 124; no H09-H12 milestone is accepted by these experiments.
The selected Linux 7.1.8 kernel, complete live root, initramfs handoff, Systemd,
login and native-runtime tests remain mandatory before G1.

## Native Mtools

Follow GNU Mtools 4.0.50's frozen INSTALL and Makefile.in: configure, make and
private-prefix installation, without X or floppyd. The signed archive and
source selection remain ADR-0050. Its check target prints `No self tests
included`; that exit is not test coverage. The private driver uses two jobs,
verified inputs, protected storage, individual durable logs/exits and bounded
process groups. Neither the installed Dpkg status nor probe inputs changed.

The shared native behavior check now serves both private preparation and the
future installed-package postcheck. Production still requires actual package
identity/ownership before that shared check. Generate a genuine native GRUB EFI
executable, use the exact frozen grub-mkrescue mformat geometry (`-f 2880 -L 16`)
and recursive mcopy path, read back identical EFI bytes and a long UTF-8 filename,
and require prompt malformed-image rejection. Preserve failed fixtures; delete
only successful disposable FAT fixtures.

All five private stages passed in
/mnt/lfs/sources/recovery/mtools-native-huftg6xd. Complete local collection SHA-256
e0f8da80e34c31d27fcdb3430115ae79769a37b8cf4165b6df9f8eed64488b07.
The multicall executable backing mtools/mformat/mcopy/mdir has SHA-256
7da97662bb3c44a6fee575e65afefc4243769a48921dd244336ca44eb867f34a.
This is not h11-mtools package acceptance or an independent CVE regression.

## Measured font dependency and assembly decision

The actual native grub-mkrescue invocation failed before producing media:
`/usr/share/grub/unicode.pf2` does not exist in the accepted base GRUB package.
Explicit empty font/theme lists bypass its module-directory font installation,
but the EFI branch still unconditionally renders an Apple `.disk_label` using
that font. The second attempt reproduced the same failure. Do not fabricate a
font, import a distribution binary, change the frozen package versions or claim
that the empty lists fix grub-mkrescue itself.

For the foundation's x86_64 BIOS/UEFI text/serial profile, compose the existing
source-built tools explicitly using the frozen grub-mkrescue implementation:

1. Generate i386-pc-eltorito and x86_64-efi images with native grub-mkimage.
   Embed early search for a media-specific file and set the GRUB prefix.
2. Embed all commands required by the profile; retain explicit module inputs.
   Actual first boot caught a missing `echo` module even though QEMU exited
   zero. Add that real module and repeat the firmware matrix. Exit zero alone
   is never loader acceptance.
3. Put the EFI program at EFI/BOOT/BOOTX64.EFI in the native Mtools FAT image.
4. Use native Xorriso mkisofs emulation with GRUB's boot_hybrid.img,
   --grub2-boot-info, BIOS El Torito/no-emulation/load-size 4/boot-info-table,
   the EFI boot image and EFI GPT partition, and protective MBR label.
5. Inspect both boot catalogs/system area, extract the exact configuration/data
   and compare bytes. Independently execute the resulting image in firmware.

Xorriso is always wrapped with -no_rc first. Verify the complete installed GRUB
payload against its accepted record before/after assembly, all private tool
inputs/binary/library digests, image transfer SHA-256 and installed DB stability.
No physical drive, global bootloader installation or active-input sync is used.

Primary sources: frozen GRUB 2.14 util/grub-mkrescue.c, especially the BIOS core,
unconditional Apple label and EFI FAT branches; SHA-256
8a7aec61e0407f74ee9e122e4e45a855ad1804596907c0a15858192b16881c2e.
Its util/grub-install-common.c implements empty font/theme lists, SHA-256
3c2ecdbd2336fecde1eafdc6a0e60c48034e2523b43b29bf9c9f755944970cf4.
Native --help confirmed the actual options. ADR-0077's verified private shared
Xorriso stack supplies the image writer; no bundled/host replacement is used.

Alternatives: add a source font and font conversion dependencies now, or patch
grub-mkrescue to conditionally omit Apple branding. Both are unnecessary for the
current text/serial foundation. Explicit composition preserves BIOS/UEFI/USB
scope without modifying the accepted GRUB package. Apple/HFS boot and graphical
GRUB fonts are not advertised. Future graphical boot branding requires its own
font build/licensing decision; this does not narrow the planned desktop.

The prepared H09 grub-install commands now pass empty font/theme lists because
their native console/serial configuration requires neither. They use the shared
installation helper, not grub-mkrescue's Apple-label branch. Actual H09 disk
installation remains gated and unexecuted; its future acceptance is unchanged.

## Actual loader-only boot evidence

Corrected generation: /mnt/lfs/sources/recovery/grub-media-b1s4yk1i.
Native assembly/readback collection SHA-256:
5422df82373cc9b3d7f914f70e1d76e672a0144e2e2458336e50d331b5d6a677.
Local host fixture: .local/vm/grub-media-tests/probe-5su1id9m.
Complete boot command/state/serial collection SHA-256:
ee6658edbfa4e4a51da652358892ff170d8a82cd24aaf157de02306bd0d90ce4.

The 3,528,704-byte **loader-only test ISO** has SHA-256
b5efdb2f08c4f19c717240a7ceae276fc511413db803604423ec3fa11816d3b0.
It contains no kernel or operating-system root and is not a release artifact.

| Firmware | Attachment | Actual result |
| --- | --- | --- |
| SeaBIOS | Virtual CD-ROM | pc platform, unique media data read, clean halt/exit 0 |
| OVMF UEFI | Virtual CD-ROM | efi platform, unique media data read, clean halt/exit 0 |
| SeaBIOS | Read-only virtual USB disk | pc platform, unique media data read, clean halt/exit 0 |
| OVMF UEFI | Read-only virtual USB disk | efi platform, unique media data read, clean halt/exit 0 |

Each test uses a separate disposable QEMU/KVM process, one qemu64 vCPU, 512 MiB
guest RAM, no network or hard disk, a read-only ISO and fresh private UEFI vars.
The container drops capabilities, uses no-new-privileges/read-only root, and
receives only KVM plus the specific image/work paths. The existing pinned OVMF
hashes were checked. All four serial logs require exactly one firmware-specific
execution marker plus the unique data read from the ISO and no GRUB error.
The image hash remained unchanged. Containers were removed after recording
their final state; the builder and both database tests continued untouched.

Retain the failed font generations and the missing-command serial log under
the earlier printed fixture paths. This evidence establishes real firmware
execution of the accepted GRUB code and the hybrid layout, **not Linux boot,
the H12 foundation matrix, hardware support, Secure Boot, installation or G1**.
