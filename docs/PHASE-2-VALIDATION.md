# Phase 2 — Focused developer checks and owner validation

Accepted validation policy, 2026-11-07. See
[ADR-0105](adr/0105-toddy-assistant-and-owner-preview.md) and the
[implementation plan](PHASE-2-PLAN.md). Tests take time: prioritize one working
reference configuration and essential safety behavior, then let owner use expand
coverage. This policy changes Phase 2 acceptance, not historical G1 evidence.

## Execution rules

- Use one disposable reference guest and its checkpoints. All disk tests target
  blank virtual disks, never the development host. Preserve the accepted foundation.
- At each story run only its new/affected smoke rows; B13 performs one combined
  pass on the exact installed release candidate. A changed artifact invalidates
  affected results, not unrelated evidence automatically.
- Default tool/IPC fixture timeout is 30 seconds, desktop actions 120 seconds and
  basic local inference 5 minutes. Choose an explicit larger bound for install,
  downloads or source builds based on actual work; never terminate a package write
  unsafely simply to meet an arbitrary timeout. These are harness bounds, not
  measured performance promises. Preserve progress/logs and safe interruption.
- Capture elapsed time, input/artifact identity, command, exit status and observed
  postcondition. Retry only after diagnosing a failed case; one classified
  infrastructure retry is reasonable, an endless loop is not.
- Mock provider/driver fixtures are labeled as fixtures. A real local tool call
  is required for the supported local profile. A real remote integration is
  optional when owner-provided credentials/budget are available; otherwise mark
  that provider live-unverified and expose that status in the UI/release notes.
- No full hardware/provider/model matrix, long soak, exhaustive fuzzing or full
  unchanged upstream compiler/libc suite is required for the owner preview.
- Block release for an unexplained failure of a required row. Optional functions
  can be disabled and labeled unavailable with their acceptance explicitly
  narrowed; do not mark an originally required capability complete by omission.

## Required smoke matrix

| ID | Story | Basic check and observable result |
| --- | --- | --- |
| S01 | B01/B02 | Record machine/resources, boot-to-login and idle desktop/Toddy measurements; explain a budget miss |
| S02 | B02 | Login, keyboard/mouse, open browser/file manager/terminal/editor, resolve network and play a short audio sample |
| S03 | B02/B06 | Stop agent/model; desktop remains usable; launch Toddy without a model and reach deferred setup |
| S04 | B03 | Fixtures for advertised protocol families: text streaming, structured tool call, cancellation and invalid/error reply |
| S05 | B03 | One actual local profile completes a harmless file-tool task offline; no remote request on local-only failure |
| S06 | B04 | Authenticated allowed file/package/service action succeeds; wrong user, malformed arguments and revoked grant are denied |
| S07 | B04 | One malicious document/tool output asks to elevate or leak a dummy secret; policy prevents the unauthorized operation |
| S08 | B05 | Restart mid-task and reconcile one known side effect without duplication; uncertain result waits for review |
| S09 | B05/B06 | Stop during a long managed task prevents a queued action and terminates/reports the active child; revoke blocks new privileged work |
| S10 | B05 | Break one guest configuration, restore its recorded prior state and verify the service works |
| S11 | B06 | Shortcut activates focused entry; type request, view progress/history/error and Stop; keyboard navigation and EN/PT copy smoke |
| S12 | B06 | API/local/later choices persist per user; dummy key is absent from logs/export and cannot be read by another test user |
| S13 | B07 | Store/retrieve/correct/delete one preference with source; export/restore it and verify isolation and deletion from FTS |
| S14 | B08 | One schedule survives restart, runs once, avoids overlap and remains quiet when disk/service state has not changed |
| S15 | B09 | Short EN/PT push-to-talk samples transcribe, produce an intelligible response, show mic state and stop; same action policy |
| S16 | B10 | One real local MCP/plugin fixture invokes its tool; timeout, removal and revoked capability do not leak credentials or grant root |
| S17 | B11 | Inspect actual login/desktop/Toddy/installer at reference resolution; logo unchanged, navy palette, readable focus/light/dark styles |
| S18 | B12 | Review exact blank virtual disk plan, reject unsafe target/cancel before mutation, install, detach ISO, reboot twice and retain file/settings |
| S19 | B12 | Select/skip optional AI, apps and third-party packs; offline deferral and incompatible driver/kernel rejection are honest and recoverable |
| S20 | B12 | One representative optional app install/launch/remove path per advertised supported app; unsupported candidates clearly unavailable |
| S21 | B12 | Install/remove/upgrade a native package preserving config; invalid signature/conflict rejected; one controlled failed update restored and boots |
| S22 | B12/B13 | Third-party selection uses device fixtures and a reviewed package transaction; previous kernel/text rescue remains available; hardware status is explicit |
| S23 | B13 | Exact final image: boot/live networking, installed basic desktop plus text-agent task and applicable S05-S22 scenarios; hashes/license inventory match |

Audio/device fixtures cannot substitute for actual audio if sound is advertised
as verified. Headless speech tests may verify the engine while microphone/device
integration stays explicitly untested. Unavailable required guest audio blocks
that claim, not unrelated validated text preview work.

## Owner-use backlog, not automatic release acceptance

| Area | Owner validation after basic delivery |
| --- | --- |
| Physical devices | Exact GPU, Wi-Fi/Bluetooth, audio, storage, camera and peripheral combinations; actual driver/firmware behavior |
| Desktop | Suspend/resume, multiple screens, fractional scaling, long sessions and keyboard/layout preferences |
| Models/providers | More context lengths, model families, quality/latency, API billing and provider outages |
| Assistant | More realistic multi-step tasks, personality, memory relevance and longer-running automation |
| Voice | Accents, noise, devices, longer speech and subjective TTS quality |
| Reliability | Repeated updates, low space, long soak and external disaster-recovery rehearsal |
| Accessibility | Full screen-reader and assistive-device review beyond basic keyboard/focus/contrast checks |

Publish this backlog with practical recovery/reporting instructions. A physical
result needs hardware identifiers and actual observations; initial release can be
VM-only. Encryption, dual boot and Secure Boot are unsupported until their own
implementation and tests pass. A successful basic release is an experimental
owner preview, not a fully hardware-qualified daily-use or enterprise release.

## Result format

Record smoke ID, artifact/input hash or version, target, date, command/log,
elapsed seconds if measured, passed/failed/deferred/not-run, observed outcome,
known limitation and corrective next action. Put short sanitized summaries in
docs/evidence and keep raw logs outside Git. Deferred/not-run never counts as pass.
If every required B acceptance passes under this scoped policy, B13/G2 may pass
for the labeled experimental owner preview; owner-use coverage remains pending.
