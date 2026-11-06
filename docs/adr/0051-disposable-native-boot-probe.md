# ADR-0051: Ephemeral native boot checks in a disposable QEMU guest

- Date: 2026-11-06
- Status: Native generator preflight passed; firmware transport and boot pending

H09 needs actual BIOS/UEFI early boot evidence after kernel/bootloader acceptance.
The build target keeps root locked and has no reusable test password. Prepare
an ephemeral boot probe delivered by the test VM firmware, rather than changing
installed account state or adding test services to the release filesystem.
H07 remains active; no native-kernel boot has been performed by this preparation.

Frozen Systemd 261.2 man/systemd.xml documents the preferred SMBIOS Type 11
io.systemd.credential.binary:NAME=BASE64 channel. Its core/import-creds.c and
shared/smbios11.c read /sys/firmware/dmi/entries/11-N/raw. The debug generator
supports systemd.extra-unit.* and systemd.unit-dropin.*; its documented
LoadCredential interface supplies the public probe script to a one-shot unit.
These payloads are public test code/configuration, not passwords or account/API
secrets. No credential payload is installed in /etc or the release image.

The prepared unit runs a guarded Python probe and requests poweroff on success
or failure. QEMU exit status alone cannot accept a test: the host must retain a
fresh serial log, require the success report, reject any failure report and
check the reported firmware mode/kernel. The probe requires root, exact native
kernel 7.1.8-toddy, Systemd PID 1, QEMU/KVM and an ext4 TODDY_LFS root on a virtual
disk with serial TODDY-BOOT-TEST before any write/module operation. It compiles
and executes C, checks dynamic linkage for temporary paths, and loads/unloads
the native dummy module while checking interface creation/removal. It refuses
an unexpectedly preloaded dummy module. Failure output includes command details;
private compiler fixtures are removed. No login, ISO or installer success is
inferred from this probe, nor does it replace the qualified native Glibc/Systemd
suite retries and full H12 scenarios.

The future host launcher must use a private copy/overlay of a hash-verified cold
target checkpoint, never the live builder target or physical storage. Mount its
backing checkpoint read-only, use separate writable UEFI variables copied from
the pristine template, keep serial/QEMU/exit evidence and terminate only that
designated guest on timeout. It must enforce H08/H09 and actual kernel/bootloader
prerequisites. The firmware importer, launcher, BIOS and UEFI execution remain
unverified; current work only prepares the payload and validates its generator.

Alternatives considered: a fixed password conflicts with release hygiene;
a temporary password or test-unit mutation in the source root creates cleanup
obligations that firmware-only input avoids. A read-only kernel/initrd direct
boot does not verify GRUB disk boot. Firmware instrumentation preserves the
normal on-disk boot path. It cannot prove an uninstrumented interactive login;
that remains an independent boot/login gate. The VM owner already controls its
firmware and disk, and no host/global authentication policy is changed.

Linux 7.1.8 drivers/firmware/Kconfig makes DMI_SYSFS default n. Add explicit
DMI=y and DMI_SYSFS=y to the existing generic fragment, so Systemd can read the
SMBIOS entries early without /dev/mem. All 139 requested symbols exist in the
hash-verified frozen source. Fragment SHA-256
322184bcada99ea9c072413474843efb3aa7aa7c4808f62f3d70986618f72cc4;
source-symbol preflight SHA-256
bfc48d137b9cb51123f6a8792ce9972d191ab442f0b5f9267370ed5377a3be62
at .local/logs/h09-kernel-smbios-symbol-preflight.json. This does not establish
resolved Kconfig/build/boot success; existing strict resolution checks remain.

Actual native Systemd debug-generator execution in private temporary directories
produced byte-identical unit/drop-in files, and native systemd-analyze verify
returned 0. Running the probe in the builder chroot correctly refused the wrong
kernel with exit 1 before mutation. Raw input hashes/results are preserved in
.local/logs/h09-native-boot-generator-probe.log, SHA-256
2e554925348315dc4b0e4689e0c169a1dd6f675ae78303305000d993e4169342.
Only temporary fixtures were created/removed; active BDB inputs were unchanged.

Existing host-tool container inventory: QEMU 8.2.2 package
1:8.2.2+ds-0ubuntu1.18, SeaBIOS 1.16.3-2 and OVMF 2024.02-2ubuntu0.10.
Non-Secure-Boot OVMF_CODE_4M.fd SHA-256
ad23261d43116abc3747d59a7837fbf578c9586a8993f4eeba064cd07eccb083;
pristine OVMF_VARS_4M.fd SHA-256
5d2ac383371b408398accee7ec27c8c09ea5b74a0de0ceea6513388b15be5d1e.
No dependency installation was necessary. Inventory JSON SHA-256
96ec8f585bd247102e3132bb12be28261e8c29bdc57c2eb7d22312ee63f76759
at .local/logs/h09-boot-firmware-inventory.json. These are infrastructure inputs,
not Toddy release components or evidence of Secure Boot/physical hardware support.
