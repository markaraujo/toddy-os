# First real live-ISO and blank-disk qualification

This source-only controller closes the first-install bootstrap seam in
[ADR0248](adr/0248-first-live-install-qualification-and-ephemeral-credential.md).
No ISO, input snapshot, VM, target disk, password, native report or acceptance is
created by its source tests. The sole root coordinator owns actual execution.
Production Calamares still uses its fixed composition factory/readiness checks.
The first source qualification harness cannot award production readiness.

## Required real inputs

Require the actually built/hashed BIOS+UEFI live ISO, current committed controller
source, and independently reviewed actual native installer input directory:

```text
payload/  # existing PreparedPayload signed native archive/record bundle
policy.json
boot-profile.json
generated-entries.json
expected-image-manifest.json
```

The payload must pass its actual signatures/public pins, component/archive/
record hashes and exact selected namespace. Policy, generated resources and
expected clean image must come from actual native qualification; no placeholder
image manifest, fixture callback or copied dirty build root is accepted. The
source snapshot includes only the installer SOURCES closure and fixed source
qualification/collector helpers. Its runtime bytes must match the exact actual
installed:true toddy-installer/toddy-assistant native archives and source-manifest
pins. Later unrelated source helper changes cannot replace a packaged module.

The fixed host context is .local/phase2/native-installer-1, mode0700, owned by the
nonroot coordinator. Its NEW qualification-inputs child contains only the
explicit metadata-pinned auxiliary ISO/descriptor/build log/completion receipt.
No /etc, /root, host account, model, keyring, private .local tree or arbitrary
hook/JSON executable path is copied. The auxiliary medium is not release media.

Use an explicitly reviewed available xorriso tool. The QEMU tools image does not
currently include it, and a missing host tool is a concrete prerequisite, never
a fallback to an unverified binary. Host development dependency installation is
already authorized; retain actual installed tool provenance separately. Its
binary hash/version are recorded, personal xorriso rc is disabled, and dates,
file modes and ISO ownership are fixed. The timestamp controls follow the
[upstream xorriso manual](https://www.gnu.org/software/xorriso/man_1_xorriso.html).
The frozen target xorriso package version is unchanged.

```sh
python3 scripts/host/installer_input_snapshot.py \
  --native-inputs "$ACTUAL_PREPARED_NATIVE_INPUTS" \
  --source-commit "$ACTUAL_REVIEWED_FULL_COMMIT" \
  --record "$NATIVE_RECORDS/toddy-installer_0.2.0-1+toddy1_amd64.json" \
  --record "$NATIVE_RECORDS/toddy-assistant_0.2.0-1+toddy1_all.json" \
  --archives "$NATIVE_ARCHIVES" --xorriso /usr/bin/xorriso
```

Supply actual canonical archive/record paths; those versions are current source
recipe examples, not permission to fabricate records. The script invokes only
source ISO tooling, never QEMU/install/format. It admits100GiB+512MiB plus complete
output/readback headroom before creating a fresh generation. Old or interrupted
contexts are preserved and refused. The guest checks every exact auxiliary file,
namespace, installed runtime byte and source-manifest hash before root review.

## Nonsecret choices and actual live boot

Prepare a separate canonical nonsecret options JSON with exactly:

```json
{"operation_id":"ACTUAL_NEW_32_HEX_ID","boot_mode":"bios","username":"owner","uid":1000,"gid":1000,"locale":"en_US.UTF-8","timezone":"UTC","hostname":"toddy-owner","ai_choice":"later","extras":[]}
```

Use an actual new lowercase hexadecimal operation ID and supported firmware.
The existing validator rejects reserved names, unsupported layouts, invalid
choices/IDs and insufficient target space. API/local/extras are only deferred
PendingStore intentions, never downloads, activation, provider keys or grants.
No password belongs in options, plans, argv or logs.

With the candidate/other project VMs cold and the reviewed source committed:

```sh
python3 scripts/host/native_installer_live.py run \
  --iso "$ACTUAL_LIVE_ISO" --iso-sha256 "$ACTUAL_LIVE_ISO_SHA256" \
  --options "$ACTUAL_OPTIONS_JSON"
```

Keep this foreground process alive; the coordinator may launch it in an owned
persistent job. It holds the existing one-guest-writer lock, preserves accepted
foundation/B02 identities, admits actual payload storage plus100GiB+512MiB,
creates only installed.qcow2 (new self-contained64GiB,0600), and boots the actual
ISO via El Torito. It uses host CPU,8GiB guest RAM, no network and read-only live/
auxiliary media. Source/payload mounts stay within a private root unit namespace.
No foundation/builder root image or physical host disk is attached. The actual
fresh toddy-live UID1000 GNOME session/live authority must be observed before
ready; no blanket root autologin or display/security weakening occurs.

## Review, confirm and execute once

From another coordinator terminal, use unique request IDs. The status/control
files are private; a transport acknowledgement never proves an install effect.

```sh
python3 scripts/host/native_installer_live.py send capture --request-id live-frame-1
python3 scripts/host/native_installer_live.py send review --request-id review-1
```

Inspect the actual returned/saved review.json: exact observed disk path,
major:minor, virtual model/driver, serialTODDY-INSTALL-P2-1,64GiB, blank/unmounted/
writable state, both partitions, native payload SHA, owner/locale/intent choices
and plan_sha256. Source review does not write the target. Optionally request
`send gui --request-id gui-1` and inspect a real QMP capture: it runs the packaged
Calamares module through the existing qualification configuration, with execute
disabled. This is actual GUI observation, not production write acceptance.

Only after this explicit root review, run one of:

```sh
# Autonomous disposable fixture: secret generated only inside trusted host RAM.
python3 scripts/host/native_installer_live.py send execute --request-id execute-1 \
  --confirm "$ACTUAL_REVIEWED_PLAN_SHA256" --generated-password
# Or omit --generated-password for an actual human-selected password via getpass.
```

The exact confirmation is checked **before** private input. The guest invokes
unchanged real LinuxDisk/Installer/PreparedPayload/NativeFinalizer callbacks, with
a0600 sealed plan FD, password FIFO and cancellation FIFO. It re-probes the actual
target at the first write. The private protocol provides no command/hook/path/
policy override. A dispatched/unknown execute is never submitted twice. Actual
journal snapshots are captured consistently through the private channel and
stored as protected SQLite bytes for interruption diagnosis.

```sh
python3 scripts/host/native_installer_live.py send status --request-id status-1
# If needed, request cancellation; inspect later status/journal result.
python3 scripts/host/native_installer_live.py send cancel --request-id cancel-1
```

Normal cancel waits for a native safe boundary; its ACK is not undo, completion
or proof of no writes. Wait for actual execute-ended/canonical terminal result.
A canceled/failed operation is never automatically restarted. Emergency host/
transport/capacity stop can interrupt a long native phase; owned-stop.json marks
that outcome uncertain/reconciliation-required and no install is accepted. The
write throttle/capacity monitor preserves the host reserve; it cannot promise
rollback or graceful completion after a forced emergency stop. Preserve the
context and actual postconditions, never replay an uncertain disk operation.

## Actual nine reports, cold close and detached handoff

After the real helper reports completed, collect BEFORE finish:

```sh
python3 scripts/host/native_installer_live.py send collect --request-id collect-1
python3 scripts/host/native_installer_live.py send finish --request-id finish-1
```

The read-only collector checks the completed exact journal/plan, final target
probe, filesystems/GRUB/installed-initramfs receipts and all nine original
finalizer reports. It streams original bytes instead of requiring16GiB output
space in an8GiB live RAM overlay. The old native file collector still enforces
its unchanged16GiB reserve. Host custody independently retains100GiB+512MiB plus
actual report bytes, validates source/owner/plan/descriptor/kernel bindings and
preserves evidence/ and handoff.json. Missing/modified reports prevent handoff.

Finish is refused before actual terminal state, and a completed child requires
the collected reports. The VM powers off, closes all writes and detaches both
media. Only actual exit0, unchanged protected inputs, a successful self-contained
64GiB qemu-img check and source digest/identity/ctime produce cold.json. Both the
manual and generated-credential detached boot paths require this completed cold
receipt and retained reports; a pre-shutdown handoff alone is insufficient.

Run the existing installed_owner_boot.py first round with this handoff, then
round2 and separate round3 text recovery in the same private installed-owner
context, following [installed owner boot](native-installed-owner-boots.md).
The default real owner password path remains manual. No detached boot/login is
accepted until the existing actual guest observer records it.

## Generated fixture password without returning it

After successful live shutdown the same process releases the guest-writer lock
and keeps an optional generated fixture credential only in RAM for at most2h.
It publishes a restrictive same-UID socket, not the password. This allows the
existing detached owner boot controller to hold the writer lock normally.

At each actual GDM password or TTY password field: use the existing installed
controller's public username/navigation actions, capture a fresh actual frame,
inspect that it is the intended password field, and obtain that frame's SHA from
input-frame-N.json. The read-only extra guest observer must concurrently report
fresh matching round/boot/rootUUID, no active owner/completed desktop, an actual
Wayland GDM greeter plus password PAM worker, or a foreground noecho tty2 login.
Then explicitly request typing:

```sh
python3 scripts/host/native_installer_live.py type-generated-password \
  --installed-context "$ACTUAL_OWNED_INSTALLED_BOOT_CONTEXT" \
  --frame-sha256 "$FRESH_INSPECTED_PASSWORD_FRAME_SHA256"
```

The vault verifies source/overlay/container/mount/source-code identities, checks
the observer before every key and types into that exact QMP context. It never
returns/logs a credential and does not press Enter or claim authentication. Use
the existing public Enter action and retain actual PAM/GDM login observation.
An intended typing attempt holds that boot against automatic retry even if a
QMP acknowledgement is lost. A stale frame, wrong session, active owner, completed
desktop or disappeared observer refuses typing; it cannot echo into an owner
terminal. Normal GDM/PAM/login policy is unchanged. This mode is only a synthetic
qualification account, never a real owner's password choice or general Polkit
credential service.

After all actual boot/recovery observations, explicitly end the RAM service:

```sh
python3 scripts/host/native_installer_live.py close-generated-credential
```

Process death, expiry or closure records fixture credential unavailable. Preserve
actual evidence and checkpoint that condition; there is no silent password reset,
secret file, password-return endpoint or fabricated authentication success.
Current source work creates none of these native artifacts or G2 acceptance.
