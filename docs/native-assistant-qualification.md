# One-boot native assistant qualification

Source harness only: no VM, provider/model, microphone, audio or native acceptance
was executed to prepare it. The coordinator is the sole guest writer. Commit the
reviewed inputs first. Existing B02 desktop/browser/kernel evidence remains
unchanged; no foundation rebuild, hardware matrix or story acceptance is implied.

The new fixed hook/control pair consumes **installed native packages**, including
the [original-source package wrappers](native-source-package-delivery.md). It
never builds fixture packages, installs source files over runtime paths or runs a
private mock service as a GUI substitute. The candidate must contain actual
Whisper/eSpeak/model/catalog packages from the
[voice pipeline](../runtime/voice/NATIVE-PIPELINE.md), when those phases are chosen.
All current first-party package versions must be `0.2.0-1+toddy1`; the older B04
fixture `0.1` packages cannot satisfy this probe. Missing native packages, source
records, archive bytes, model/license bytes or required receipts fail before GDM.

The sole boot backing is the **cold current candidate**
`.local/vm/phase2-candidate/lfs-target.qcow2`, mounted through the complete canonical
read-only `/vm` backing chain. A NEW `/work/target.qcow2` overlay receives all
runtime test changes. The original accepted B02 disk is never the writable test
root. Require `phase2_candidate_vm.py stop`, which authenticates the actual
candidate through `owned()`/`bases()` before shutdown and retains a cold identity
receipt. Do not use an old B02 controller, raw Docker stop or an active candidate.

This qualifier explicitly uses **12 GiB guest RAM, four CPUs** (13 GiB container
limit), `-cpu host`, no network and no host audio backend. It is not an 8 GiB
product resource acceptance. Frozen Qwen3-1.7B-Q8_0/Pi 1.5.0 and all existing CPU,
context/tool/deadline and authorization checks stay in force. No model switch,
automatic download, cloud fallback, real provider key or license consent occurs.

## Prepare the actual inputs once

The model path below is the existing 1,834,426,016-byte frozen local Qwen input.
The coordinator transfers the already cached 11,544-byte raw Apache license to
exactly `/sources/qwen-LICENSE`; its frozen SHA-256 remains mandatory. No model or
license download or automatic consent is part of collection.

After native package install/check postconditions pass and the global compiler
lock is free, deliver the two reviewed scripts and attributed human WAV fixtures
to `/opt/toddy-build` through the coordinator's existing verified metadata route.
In that guarded builder, explicitly collect a fresh generation, for example:

```sh
python3 /opt/toddy-build/scripts/host/phase2-native-assistant-hook.py \
  --collect assistant1 \
  --phases ui-prepare,ui-en,keyring,agent,agent-ui,ui-pt,ui-return-en,memory,grant,automation,automation-alert,automation-interrupt,revoke,integrations-bootstrap,integrations,voice-files,voice-device \
  --local-model-path /sources/phase2/inputs/local-model-proof/model.gguf \
  --local-license-path /sources/qwen-LICENSE
```

Those model/license paths are **explicit example inputs**, not an acquisition
promise. Supply the actual already acquired, regular root-owned/readable paths
with the exact frozen hashes; do not fabricate a file or weaken the guard to make
the example work. The Qwen model is 1834426016 bytes, SHA
`061b54daade076b5d3362dac252678d17da8c68f07560be70818cace6590cb1a`.
The original Apache license SHA is
`5de36594c10839788a8c589443a8ef9d8b8d17c65a1b5807206ae037fc36c6bd`.
No host/model download is performed by collection or boot. The voice model remains
the separate 147951465-byte full multilingual base artifact.

Collection only reads native dpkg versions and `/var/log/toddy/packages` records,
verifies exact new archives from `/var/cache/toddy/packages`, and copies those
archives into a new `/mnt/lfs/sources/phase2/assistant-native-inputs/GENERATION/`.
It uses the existing target guard/global lease and preserves 16 GiB + 512 MiB plus
the exact additional copy size. Baseline archives are reused only when their
version/archive/record SHA exactly matches accepted B02 metadata. Raw native
record text is retained alongside parsed data so transport key ordering cannot
silently change its checksum. A `DONE.json` plus output manifest hash proves
collection completion; a leftover preparation without both is uncertain, never
an instruction to replay. Existing generations/destinations are refused.

Read back `/var/log/toddy/phase2/assistant-native-inputs-assistant1.json` through
the owned candidate's read-only SSH command into a private host file. Shut the
candidate down cleanly with its existing controller, then bind and run:

```sh
python3 scripts/host/phase2-native-assistant-control.py bind \
  --inputs /absolute/private/assistant-native-inputs-assistant1.json --generation assistant1
python3 scripts/host/phase2-native-assistant-control.py run \
  --manifest /absolute/repository/.local/phase2/native-assistant-inputs-assistant1.json \
  --generation assistant1
```

`bind` only binds collected data to the final cold candidate identity. `run`
requires a clean checkout, actual cold stop receipt, unchanged accepted backing,
no other writer/test and 100 GiB + 512 MiB host reserve. Contexts never resume or
redispatch uncertain effects. The read-only packet uses a new short serial
`TODDY-ASST-DATA` and a small firmware-pinned loader; larger source/data is bounded
and SHA-verified before execution. JSON cannot name a downloaded executable/hook.

## Authenticate and advance the same session

The controller keeps a fresh synthetic login password only in RAM/private serial
transport; it is never printed, stored in the manifest or included in QMP event
receipts. The hook creates `td-asst-owner` UID 12406 and starts actual installed
GDM, Polkit and the root executor. No autologin, PAM override or grant database
write exists. Inspect the actual GDM screen before typing a password:

```sh
python3 scripts/host/phase2-native-assistant-control.py send --context CONTEXT --request-id frame-login --action capture
python3 scripts/host/phase2-native-assistant-control.py send --context CONTEXT --request-id login-name --action username
python3 scripts/host/phase2-native-assistant-control.py send --context CONTEXT --request-id login-tab --action key --codes tab
python3 scripts/host/phase2-native-assistant-control.py send --context CONTEXT --request-id login-secret --action password
python3 scripts/host/phase2-native-assistant-control.py send --context CONTEXT --request-id login-enter --action key --codes ret
```

Adapt only the explicit keyboard navigation to the observed native GDM fields;
never blindly type the private password into another application. Wait for
`OWNER-READY` in private `control-state.json`: root verifies the actual active,
local, unlocked Wayland owner/seat0. Send one phase at a time with a unique request
ID, inspect its actual `RESULT`, then advance. Duplicate IDs refuse replay.
The controller rejects another phase or `done` while a phase is pending, rejects
previously requested phases even under a new request ID, and enforces the selected
manifest order. A failed native result blocks further phases; inspect the retained
report rather than retrying that disposable session.

```sh
python3 scripts/host/phase2-native-assistant-control.py send --context CONTEXT --request-id prep-ui --action phase --phase ui-prepare
python3 scripts/host/phase2-native-assistant-control.py send --context CONTEXT --request-id activate-ui --action shortcut
python3 scripts/host/phase2-native-assistant-control.py send --context CONTEXT --request-id check-en --action phase --phase ui-en
```

Continue the selected ordered phases below. An `action:phase` acknowledgement only
means requested; it is never proof. `grant`/`revoke` launch the fixed owner surface
through actual per-user systemd/Polkit; inspect the **real native Polkit password
prompt** and explicitly use `action:password`/Return. There is no cached permission,
profile grant or generic verification callback. The native Keyring must already
have its real PAM-unlocked default collection; absence/locked state at initial
save fails honestly instead of creating an unprotected replacement.

The host rechecks current **committed** status prerequisites before each phase.
In particular B08 requires accepted B07 and B09 requires accepted B06/B03. Review
actual phase receipts/frames and record eligible milestone evidence before those
requests; this harness never edits status or accepts a story. It can hold the same
boot while the coordinator performs that review. B10 retains its actual independent
B02/B04/B05 dependencies. Native root also enforces selected phase order and
one-shot completion. Failed phases terminate with retained failure metadata.

| Phase | Actual postcondition |
| --- | --- |
| `ui-prepare`, `ui-en` | Register the reviewed per-user shortcut, actual QMP activation/focus, installed GApplication PID-scoped AT-SPI EN widgets; canonical broker systemd MainPID matches D-Bus owner. |
| `keyring` | Native Secret Service dummy roundtrip, profile isolation, actual collection Lock and fail-closed lookup, no plaintext fallback; another UID cannot connect to the owner's private bus. No secret bytes in receipts. |
| `branding` | Requires native defaults upgrade `0.2.0-1+toddy2` and B11 prerequisites. Fresh GNOME owner has no background override; effective/admin-default light/dark URI/zoom and actual artwork hashes must match. Actual GTK icon-theme 32/48/64 lookups at theme scales1/2 are displayed in a native inspection window, with QMP frames before/during and actual surface scale recorded. Visual review remains required. |
| `agent` | Actual installed Pi Core/Pi AI 1.5.0 + Node 24.19.0/frozen Qwen turn, observed tool file effect and text, duplicate request without effect replay; Stop during actual generation and native worker/model child cleanup. |
| `agent-ui` | Real GTK entry/Send→canonical service→Pi/Qwen effect, actual assistant text rendered; real GTK Stop, native user-service restart/reconnect and unchanged completed effect. |
| `ui-pt` | Explicit native quit/relaunch in PT, PID-scoped native PT labels/focus. `ui-return-en` explicitly closes/relaunches the real app in EN before later EN widget automation; no widget fixture is substituted. |
| `memory` | Canonical owner create/update/generation CAS/delete, sealed FD export/restore, stale profile/backup tombstone safety and per-profile isolation; real Qwen first retrieves a nonsecret preference canary and cannot retrieve it after deletion/stale restore. |
| `grant` | Profile selection alone cannot enable a standing workflow; fresh actual authenticated owner standing grant and root-UID0 live inspection. |
| `automation`, `automation-alert` | Actual timer slots, two stable disk checks with quiet behavior; controlled native NetworkManager stop/restore produces one real visible GNOME alert, second unchanged actionable check is quiet. No model call. |
| `automation-interrupt` | pidfd-bound fault injection stops one actual fixed systemctl health child, kills its canonical broker main, then requires actual uncertain recovery and 35 s without replay; explicit typed read-only review retires uncertainty without rerunning. Failure to catch the real child is a failure, not seeded SQLite state. |
| `revoke` | Fresh native owner revocation; the independent root query becomes false and a new workflow enable is denied. |
| `integrations-bootstrap` | Distinct trusted disposable native qualifier: real production release-reference lookup plus a clearly labelled actual bwrap confinement fixture (file/bus/FD/env/network/caps/read-only mounts/Stop/deadline), and real fresh Firefox/scoped AT-SPI read/revoke. Only then root emits exact production receipts. |
| `integrations` | Canonical profile opt-in and source pins; actual broker MCP lookup, isolated Firefox local-page read, on-demand skill, revoke blocks new dispatch. No installed-status claim from release reference data. |
| `voice-files` | Actual qualified native package/process/legal receipts and fixed root catalog; no source true-flags accepted. |
| `voice-device` | Actual guest PipeWire virtual input/output, licensed human EN/PT feed after PTT starts, captured PCM/non-silence/hash/real Whisper reference; native controller Stop/playback plus real GTK/QMP held-key review/Stop/speech/output capture and typed fallback; no automatic transcript task dispatch. |

`integrations-bootstrap` is permitted only as fixed trusted root qualification,
without a production flag/environment/path override. It uses the actual installed
`Plugin`/`BrowserSession`, a live authenticated owner predicate and exact pinned
capability/manifest/page/reader. Root receipts are absent until all native checks
exit 0, and existing receipts are never overwritten. The bootstrap proof and exact
receipt bodies are retained in the native result for coordinator custody and
later owned package/image delivery; this disposable overlay is not a released
installation. If receipts already exist and match measured inputs, omit bootstrap
and collect their exact files for canonical consumption instead.

The virtual audio producer uses frozen PipeWire 1.6.8's
[pw-loopback property CLI](https://raw.githubusercontent.com/PipeWire/pipewire/1.6.8/src/tools/pw-loopback.c)
and [loopback source/sink endpoints](https://raw.githubusercontent.com/PipeWire/pipewire/1.6.8/src/modules/module-loopback.c).
It creates only transient named endpoints, validates their actual client PID and
object.serial, feeds the pinned WAV via real pw-cat, and leaves production wrapper
properties intact. Captured WAV hashes differ from the input hashes when graph
conversion/leading silence changes bytes; actual PCM and Whisper references must
still pass. All owned child PIDs/nodes are cleaned; no default/auto device,
physical microphone, physical speaker, host audio or silence/stub transcript is
relabeled as a human capture. GTK actions use the actual installed app and QMP
held/released events, never a replaced controller. Unsupported native AT-SPI,
missing virtual graph support or failed text/PCM verification fails the phase.

After all selected results pass, explicitly send `action:done`. A partial run
remains partial, with unrun phases listed. The probe is globally bounded to 30 min;
model/device calls have their existing narrower bounds. The controller preserves
serial report SHA, actual phase failures/line metadata, input/frame events, cold
identity and ownership receipts, stops only its own container and rechecks every
backing identity. No unchanged automatic retry, uncertainty replay, native GUI
claim from host fixtures, broad soak or G2/physical acceptance follows.

## Source contract regression checks

`python3 -m unittest discover -s tests -p test_native_assistant_harness.py -v`
checks the embedded client's literal Service1 names/signatures against the current
production XML, runs its extracted local connection/profile data through the real
ConfiguredEngine settings reader, and runs its revoke operation through the real
integration parser against disposable SQLite. The private socket fixture checks
that transport acknowledgement cannot queue a second phase or end an active one.
These are source contract checks, not native GTK, Qwen, keyring, browser or voice
acceptance. Current GTK copy keys, installed data paths and widget lifetimes were
reviewed directly; actual accessibility names and input/focus still require the
real GNOME boot.
## Optional B11 branding phase

Run the [native defaults upgrade](native-desktop-background-upgrade.md) first.
Add `branding` explicitly to the selected phases after `ui-en` and only after
actual B06 acceptance is committed. The controller applies the actual B11
prerequisites (B02 and B06); the harness does not accept either story. The input
collector includes the new native `toddy-desktop-defaults` archive/record plus
`toddy-branding`; the old plain-background package cannot satisfy this phase.

The phase creates only a disposable native GTK inspection window. It never sets
user background/scaling preferences or edits/resizes protected artwork. It checks
fresh-owner background values, hashes installed wallpaper/icon files against the
native package record, shows native icon-theme lookups for 32/48/64 pixels and
requests QMP captures. Theme lookup scale2 is explicitly **not** proof of a real
scale2 GNOME display. Its result records the actual surface scale. Coordinator
review of the real screenshots, light/dark/focus states, login/installer imagery,
actual alternate display scale and removal fallback is still required for B11.
An assertion or screenshot request alone is not visual success.

API semantics used here are documented by upstream:
[Gio.Settings.get_default_value](https://docs.gtk.org/gio/method.Settings.get_default_value.html)
(available since GLib2.40; includes administrator defaults) and
[Gtk.IconTheme.lookup_icon](https://docs.gtk.org/gtk4/method.IconTheme.lookup_icon.html)
(GTK4 size/window-scale lookup returning a native paintable). The current official
pages describe newer library releases; actual frozen GTK4.22.4/GLib2.88.1 behavior
must still pass in the native session.

## Optional installed root installer inspection

The optional `installer-gui` phase reuses this same authenticated native owner
session and transport. Include it after `ui-en` in a **new** collection generation
and bind/run that exact cold manifest through the existing commands above. Its
package selection additionally requires actual native archives and full installed
records for `toddy-installer` and `calamares-branding-toddy` 0.2.0-1+toddy1,
unchanged `toddy-branding` 0.2.0-1+toddy1, Calamares 3.4.3-1+toddy1, QtBase
6.11.2-1+toddy2, QtSvg 6.11.2-1+toddy1, KF6 CoreAddons 6.29.0-1+toddy1 and
yaml-cpp 0.9.0-1+toddy1. An installed version string alone is insufficient: the
normal packet and guest verification bind archive/record hashes and all owned
payload bytes. No source staging or package installation occurs during this phase.

Send the phase through the existing private controller, for example:

```text
phase2-native-assistant-control.py send --context ACTUAL_OWNED_CONTEXT \
  --request-id installer-gui-first --action phase --phase installer-gui
```

Use the actual executable Python command prefix from the existing guide. The
request remains pending until its native result returns; do not resend it, issue
another phase or finish while it runs. Screenshots use the same native INPUT/QMP
handshake; control-state records both the existing frame field and `native_frame`.
The ordinary explicit capture/key controls remain available to the coordinator.
Review the resulting real frames, not merely a QMP acknowledgement.

This is a narrow no-write **preacceptance probe**, authorized before full B12
acceptance. Its gate requires recorded Phase 2 approval and completed B01/B02/B03;
its native phase ordering still requires this session's successful `ui-en`.
B12's B06/B11 dependencies remain unchanged and uncompleted prerequisites do not
become installer or artwork acceptance. Other assistant/branding phases retain
their existing story gates. No install/partition/format operation is added to the
controller, and production launch/composition gates are unchanged.

The root hook imports the actual installed developer
`qualification_command(uid, display, locale)` shared with
`installer_qualification.py gui`, using the observed owner's sole Wayland socket.
The launcher independently checks authoritative active local unlocked logind
identity, socket metadata and kernel peer credentials. The returned command must
be exactly native `/usr/bin/calamares -c` with the fixed
`calamares-qualification` configuration; the root environment must exclude the
owner session-bus address. There is no upstream test/debug/nonroot bypass flag.
The hook launches English/Portuguese cases with requested owner light/dark
preferences, captures each actual root process and keyboard Tab state, and
restores the exact original owner color-scheme setting afterward. Each root GUI
child is closed and reaped within a bounded timeout. Intentional SIGTERM/SIGKILL
cleanup is limited to the owned show-only child, whose sequence has no exec job;
it is never used to interrupt an installer transaction.

The show-only configuration is bound to its exact source-produced SHA and has no
exec sequence. The hook additionally requires the entire production composition
path absent. The real native view automatically requests `targets` on activation;
its installed CLI first constructs and validates production composition. With
that path absent it fails closed **before** target enumeration, disk probing,
persistent journal construction or installation. This is the actual unavailable
state for visual inspection, not an emulated backend. Once production composition
exists this probe refuses to launch; do not remove a real seal or replace a
runtime binding to force it. Use a fresh disposable source qualification context.
No Review/Install button is activated, no real installer password is entered,
and no root GUI authentication field is automated by this phase.

The result deliberately retains `visual_review_required`, pending 100/200-percent
scale acceptance, `B12_acceptance: false` and
`launch_qualification_receipt_written: false`. Requested owner light/dark scheme
is not proof that an isolated root Qt process adopted it. The coordinator must
inspect real navy/artwork, EN/PT copy, readable native rendering, focus,
unavailable/error presentation and cancellation behavior in the captured frames;
additional real scale/focus/Cancel checks are still needed before filling the
strict production launch receipt's observations. This phase never fabricates that
receipt, signed inputs, blank-disk install, detached BIOS/UEFI owner boots,
recovery or release acceptance.

## Broker-independent native setup phase

Include `setup-offline` FIRST in a new selected phase list, before
`ui-prepare,ui-en,keyring,agent,...`. Collect/bind a new input generation through
the existing commands above; preserve older component-only packets and reports.
The phase uses the current installed `/usr/bin/toddy` and real GApplication/
AT-SPI widgets. It does not qualify source fixtures as native GUI results.

The root coordinator records the actual user unit's enabled/activity state,
refuses an existing mask or transitional/failed service, and temporarily stops/
runtime-masks only `toddy-agent.service` on that authenticated owner's user bus.
The user client skips ALL common broker capability/profile calls for this phase.
It verifies `NameHasOwner:false` and native MainPID0 throughout. The existing
fixed QMP input bridge supplies keyboard events to the actual focused GTK backend
preference dropdown; real Save preference actions must persist API/local/later
intent through native application exit/relaunch and protected PendingStore
readback. This tests preferences, not a paid provider call or model launch.

An existing deferred wish is preserved. When the disposable candidate has no
installer wish, the qualification explicitly seeds one through the actual shared
owner storage API and reports that fact; it does not claim installer-handoff
acceptance. Actual Software-page unavailable/retained-pending labels must render,
with no acquisition request and byte-identical native dpkg inventory. The final
Later action must persist invitation dismissal. Finally the exact prior user
mask/activity state is restored, including on a failed client phase. A restore
failure is a native qualification failure, never successful setup evidence.

The required later `keyring` phase separately proves real protected dummy-key
storage/isolation and locked failure without plaintext fallback. This phase
supplies no credential input and does not waive that check. Earlier selected
component reports without `setup-offline` remain component-only; neither
`all_selected_exits_zero` nor this source preparation alone accepts B06/G2.

The dropdown role is derived from frozen GTK4.22.4 `gtk/gtkdropdown.c`
(`GTK_ACCESSIBLE_ROLE_COMBO_BOX`); widget existence/focus/QMP handling still
requires the actual native run. Missing or ambiguous accessibility state fails
rather than selecting a fabricated tree or silently skipping the interaction.
