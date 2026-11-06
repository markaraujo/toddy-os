# ADR-0051: Ephemeral native boot checks in a disposable QEMU guest

- Date: 2026-11-06
- Status: Native generator and paused QEMU preflights passed; actual boot pending

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

The prepared host launcher uses a private overlay of a hash-verified cold
target checkpoint, never the live builder target or physical storage. It mounts its backing checkpoint read-only, uses separate writable UEFI variables
copied from the pristine template, retains serial/QEMU/exit evidence and stops
only its designated guest on timeout. It enforces H08/H09 and actual kernel/
bootloader prerequisites. The actual Systemd firmware importer and native BIOS/
UEFI boots remain unverified; paused-machine tests do not execute guest code.

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

The prepared host executor is scripts/host/boot_test.py. It requires a clean
checkout, current accepted H09 artifact markers from the guarded builder, and
an H09 cold checkpoint created after those markers. It rejects redirected paths,
checks the target SHA-256/qcow2 consistency/180 GiB geometry, and creates a small
private qcow2 overlay with a read-only backing bind. No builder disk, SSH key,
source checkout or physical disk is exposed to the test container. A fixed
2-vCPU/2-GiB qemu64 profile, 3-GiB container limit, no networking and host memory/
disk reserves bound this early-boot test. Later network/USB/live tests remain
separate. UEFI template hashes must match the recorded inputs before use.

The executor retains result.json, prepare.log, qemu.log, serial.log, private
variable store, overlay and stopped container. It records immutable container
image ID, commit, payload/source hashes and the native report; successful
execution rehashes the cold backing. A controller flock and an independent
running-container check prevent overlapping runs, including a guest surviving
its original controller. Missing observations do not authorize restart.
Timeout/error handling stops only a container whose test label matches its
recorded run ID; uncertainty is explicitly recorded as cleanup_uncertain.
Native report parsing rejects failure markers, missing/contradictory reports,
wrong firmware/kernel/environment, temporary linkage and missing module checks.
No milestone is automatically accepted by this executor.

Actual infrastructure preflight used a newly created empty qcow2 file and
private overlays, not a Toddy checkpoint. Both BIOS and UEFI QEMU launches with
the exact versioned SMBIOS payloads reached QMP prelaunch/running=false and quit
cleanly, without executing guest instructions. Read-only backing consistency
and unchanged SHA-256 passed. Raw report
.local/logs/h09-qemu-paused-firmware-probe.json SHA-256
`d64e660424f11d04d8df564e078deb3f3f7dbc32e4e8804305c259508d339ca3`.
This proves argument/firmware setup, not Systemd firmware import or OS boot.

A separate paused QEMU test deliberately timed out its attached client. The
real overlap guard refused a second run; the stop helper refused a wrong run
identity and left that guest running, then stopped it with the matching identity.
All preflight containers/empty-image fixtures were removed after verified exit.
Raw .local/logs/h09-qemu-timeout-probe.json SHA-256
`7a7284d3dd099d44c1e27704874c47a828a3f3ac5b6b13e0cc0b2f68f2c23b36`.
Actual main-executor invocation refused the current H08/H09 state before any
checkpoint/container operation, exit 1; refusal SHA-256
`634270dd13d400e2199099dd09092f4176bee47da213f82510360e7b47fdbf4b`
at .local/logs/h09-boot-launcher-premature-refusal.log. Four repository safety
tests cover redirected/external checkpoint inputs and incomplete reports.
