# Phase 2 — Focused developer checks and owner validation

Accepted validation policy, 2026-11-07. See
[ADR-0105](adr/0105-toddy-assistant-and-owner-preview.md) and the
[implementation plan](PHASE-2-PLAN.md). Tests take time: prioritize one working
reference configuration and essential safety behavior, then let owner use expand
coverage. This policy changes Phase 2 acceptance, not historical G1 evidence.

Execution sequencing and resumption follow [the playbook](PHASE-2-EXECUTION.md).
The [review](PHASE-2-REVIEW.md) records corrected gaps; no runtime result is implied.

## Change-based test decision at each work boundary

Follow [ADR-0110](adr/0110-isolated-package-builds-and-change-based-validation.md).
Every interaction decides whether evidence was invalidated; it does not run all
tests. Inspect actual diff/input identities and any unresolved failure first.

| Trigger | Required scope |
| --- | --- |
| Explanation/status only, unchanged inputs | Reuse identified evidence; no test run |
| Docs/planning-only delivery | make check; no guest build |
| Visible UI/site change | Affected behavior/layout/locales/accessibility plus repository checks |
| Local tool/recipe change | Changed behavior, negative case and direct consumers |
| Shared protocol/schema/ABI/store or sandbox/policy change | Affected consumer closure and changed safety/restart edges |
| Package/boot/kernel/installer change | Affected transaction, boot/install/recovery and relevant integrity checks |
| Unexplained regression or unknown impact | Diagnose/trace closure, then broaden the affected integration set |
| Final candidate | Existing combined release gate on the exact artifact |

Record scope/checks/reused evidence in the existing slice card, not a new checklist
per chat. Do not rerun passing unchanged checks for reassurance. A changed package
or dependency invalidates its consumers' relevant evidence, not every unrelated
foundation result. Cheap required repository checks still run before delivery.

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
| S01 | B01/B02/B06/B07 | Stage measurements as components become real: foundation/spike in B01, desktop in B02, service/entry in B06, lookup in B07; explain a budget miss |
| S02 | B02 | Login, keyboard/mouse, open browser/file manager/terminal/editor, resolve network and play a short audio sample |
| S03 | B02/B06 | B02 proves desktop without any agent/model installed; B06 stops the actual services and reaches deferred setup without a model |
| S04 | B03 | Fixtures for advertised protocol families: text streaming, structured tool call, cancellation and invalid/error reply |
| S05 | B03 | One actual local profile completes a harmless file-tool task offline; no remote request on local-only failure |
| S06 | B04 | Authenticated allowed file/package/service action succeeds; wrong user, malformed arguments and revoked grant are denied |
| S07 | B04 | One malicious document/tool output asks to elevate or leak a dummy secret; policy prevents the unauthorized operation |
| S08 | B05 | Restart mid-task and reconcile one known side effect without duplication; uncertain result waits for review |
| S09 | B05/B06 | Stop during a long managed task prevents a queued action and terminates/reports the active child; revoke blocks new privileged work |
| S10 | B05 | Break one guest configuration, restore its recorded prior state and verify the service works |
| S11 | B06 | Shortcut activates focused entry; type request, view progress/history/error and Stop; keyboard navigation and EN/PT copy smoke |
| S12 | B06 | API/local/later choices persist per user; dummy key is absent from logs/export and cannot be read by another test user; locked/missing secret service never causes plaintext fallback |
| S13 | B07 | Store/retrieve/correct/delete one preference with source; export/restore it and verify isolation and deletion from FTS |
| S14 | B08 | One schedule survives restart, runs once, avoids overlap and remains quiet when disk/service state has not changed |
| S15 | B09 | Short EN/PT push-to-talk samples transcribe, produce an intelligible response, show mic state and stop; same action policy |
| S16 | B10 | One real local MCP/plugin fixture invokes its tool; timeout/removal/revocation work; sandbox denies out-of-scope files, dummy-secret access and undeclared egress |
| S17 | B11/B12 | B11 inspects actual login/desktop/Toddy and staged installer assets; B12 inspects the running installer. Logo/navy/focus/light/dark remain readable |
| S18 | B12 | Review exact blank virtual disk plan, reject unsafe target/cancel before mutation, install, detach ISO, reboot twice per advertised firmware and retain file/settings; reject mounted/source targets and recheck disk identity before writes |
| S19 | B12 | Select/skip optional AI, apps and third-party packs; offline deferral and incompatible driver/kernel rejection are honest and recoverable |
| S20 | B12 | One representative optional app install/launch/remove path per advertised supported app; unsupported candidates clearly unavailable |
| S21 | B12 | Install/remove/upgrade a native package preserving config; invalid signature/conflict rejected; low-space preflight and one controlled interrupted update restored and boots |
| S22 | B12/B13 | Third-party selection uses device fixtures and a reviewed package transaction; previous kernel/text rescue remains available; hardware status is explicit |
| S23 | B13 | Exact final image: boot/live networking, installed basic desktop plus text-agent task and all required S05-S22/S24-S26 scenarios; installed package closure, hashes/license inventory match |
| S24 | B05/B06/B07/B10/B13 | A: revision/apply/import/recovery in B05/B06; B: memory/profile isolation in B07; C: skill/extension containment in B10; combine at B13, with no implied early acceptance |
| S25 | B10 | One opt-in browser tool navigates/reads a harmless local page using an isolated test profile; Stop/error work and page text cannot authorize another action |
| S26 | B12/B13 | Installed image has no live autologin/default accounts, inherited secrets/machine identity/private signing keys or volatile-only persistence; normal/recovery startup is documented |

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


## Stage boundaries that prevent premature tests

- S01-A (B01): identify foundation/CPU-spike target and separate build/runtime
  budgets. S01-B (B02): measure actual desktop. S01-C (B06): measure real service
  and entry activation. S01-D (B07): measure the fixed lookup fixture. B13 reuses
  stable component measurements and checks unexpected image regressions.
- S17-A (B11): guest branding and installer scene assets. S17-B (B12): actual
  running installer. Do not create a B11 -> B12 -> B11 acceptance cycle.
- S24-A: create/clone/select without inherited credentials/history or grants,
  persona/model/tools edits, bad config, concurrent edit detection, atomic
  revision/restore, secret-free import/export and traversal rejection. B01 only
  reviews the schema/fixture; it does not run future UI/memory/skill acceptance.
- S24-B: switch between two profiles and two users, inspect/correct/delete/export
  and restore memory, verify FTS deletion and no stale retrieval/cache. Same-UID
  profile separation is logical; do not claim protection from that user's own
  arbitrary code or unrestricted root.
- S24-C: load one skill only when relevant; reject undeclared executable hooks
  and out-of-root imported resources; verify containment with dummy data. Unknown
  plugin code stays disabled if the actual guest cannot enforce the boundary.
- S25 is a narrow browser bridge, not autonomous logins, financial transactions,
  messages or a broad website matrix. Reuse existing policy/provider cancellation
  checks rather than testing every website. No owner browser profile is used.

B06 requires the applicable A-stage checks only; B13/G2 requires A+B+C and all
required rows, including optional-to-enable voice/plugins. Disabling a required
component can permit a smaller labeled interim snapshot, not a completed G2.

## Essential failure edges, sampled rather than multiplied

Use deterministic local fixtures to keep these checks small:

1. B04/B05: a grant revoked between planning and dispatch is rejected; the model
   cannot race a second writer around the executor lock. Start mutating tools
   sequentially even if the selected engine supports parallel calls by default.
2. B05: terminate/restart after an effect but before result recording. Verify a
   known postcondition and no duplicate; an ambiguous action stays pending review.
   A success file alone is insufficient if command status/postcondition is absent.
3. B06: disconnect UI/IPC and reconnect; retrieve the same task ID, not start a
   second task. Missing/locked keyring and missing local model lead to setup/error,
   not secret logging, silent cloud fallback or fabricated success.
4. B07: interrupt one schema migration/restore and retain the last valid database;
   explicit preference deletion must not reappear from the editable USER.md input.
5. B08: one overdue scheduled occurrence has an explicit skip/run-once policy,
   with no import/clone activation and no concurrent repeat after service restart.
6. B12: inspect the immutable selected disk identity again immediately before the
   first write; reject the live source, mounted root and incompatible firmware.
   Test one faulted update using a disposable disk snapshot and the documented
   offline rescue/previous-kernel path. A same-disk backup is not disaster recovery.
7. B12/B13: inspect the *installed* configuration for image-only autologin, users,
   cached tokens, machine IDs and signing secrets; verify correct regeneration
   and persistent account state after the two reboots.

These checks belong to their existing smoke IDs and do not authorize endless
fault matrices. Save the injection point, expected state and exit/postcondition;
reuse unchanged cases. Firmware coverage is BIOS+UEFI by default, inherited from
the foundation. A narrowed advertised boot scope must be an explicit decision.

## Candidate identity and reuse rules

A result binds source/recipe/dependency lock, package/config identity, root/image
hash, firmware/VM setup and test fixture version. During development, rerun only
changed consumers and safety boundaries. At B13 freeze a candidate with all B
packages and assemble it once; run a compact combined installed-image pass on
that candidate. A subsequent fix gets a new candidate hash and affected tests.
No test passed on the B06/B12 text-only snapshot is evidence that later packages
were present in the released image. Corresponding source/license inventory must
match the actual included components, models/voices and third-party packs.

Owner delivery checklist: [short guide](PHASE-2-OWNER-VALIDATION.md). Include offline
base installation followed by later agent acquisition, with setup working while
broker/Node/Pi/executor are absent; map these to S18/S19/S26.

Native graphical slices follow [the readiness review](PHASE-2-READINESS-REVIEW.md):
actual native interaction plus affected functional checks; browser mockups do not
prove GNOME/GTK/Qt behavior. No full visual rerun for unchanged internal code.

Shared app selection, deferred acquisition and on-request recommendations follow
[the software catalog contract](PHASE-2-SOFTWARE-CATALOG.md); candidates are not
installed packages or new mandatory breadth. Reuse existing S19/S20/S21/S26.
