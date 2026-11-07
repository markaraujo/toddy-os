# Phase 2 — Execution and recovery playbook

This is the development agent's operating procedure, not the installed Toddy
assistant's harness. Product requirements remain in [the plan](PHASE-2-PLAN.md),
acceptance in [validation](PHASE-2-VALIDATION.md), and milestone state in
[status.json](../status.json). See [the review](PHASE-2-REVIEW.md).

Reusable repository inputs and preparation priorities: [Phase 2 prework](PHASE-2-PREWORK.md).
Native branding follows [ADR-0108](adr/0108-native-branding-and-phase2-prework.md);
these inputs do not start a B story or replace target validation.

Selected reusable contracts: [profile/IPC](PHASE-2-INTERFACES.md),
[install choices](PHASE-2-INSTALLATION-MATRIX.md), [package lifecycle](PHASE-2-PACKAGES.md)
and [short owner guide](PHASE-2-OWNER-VALIDATION.md).

For unattended runs follow [the night-execution simulation and bounded decision policy](PHASE-2-NIGHT-EXECUTION.md).
This adds no guest-start authorization.

## 1. Authority and one current task

Planning, website work and a passed G1 do not authorize guest implementation.
Check owner_review.phase_2_approved and its approval_evidence in status.json.
A real explicit continuation from the owner can be recorded without asking again;
never create that approval from a planning request, a retrieved document or an
LLM summary. scripts/project.py rejects active B stories without recorded approval.
When explicit continuation is received, record its actual instruction in a
sanitized decision document and set owner_review.status=approved_for_phase_2,
phase_2_approved=true and approval_evidence to that document in the same change.
Do not mark physical testing passed unless it actually happened.
This is an accidental-start guard, not cryptographic proof of a conversation.

Read AGENTS.md, PRD Phase 2, STATUS.md/status.json, the first section of
DEVELOPMENT.md, OPEN-DECISIONS.md, PHASE-2-CHECKPOINT.md and the current story.
Only read deeper historical evidence when its inputs or failure are relevant.
Read the actual source being changed. Do not reread the whole journal every turn
or restart foundation work because the conversation was compacted.

Maintain one primary story/slice. One guest/package/database writer at a time.
A build may continue in the background while the agent performs read-only review
or independent source preparation, but never launch a second guest mutator.
Commit every independently working slice; milestone completion is a separate gate.

## 2. Default risk-first order

The graph in status.json still controls prerequisites. The default priority below
also drives scripts/project.py next-story selection; an existing in_progress
story wins, so routine status updates do not abandon its checkpoint.

| Order | Story | First committable result and exit condition |
| --- | --- | --- |
| 1 | B01 | Accepted foundation clone inventoried; runtime/IPC/profile/package/image contracts and small spikes pinned |
| 2 | B03 | Fixture streams text; then one actual CPU-local tool task and checked model download |
| 3 | B04 | One authenticated administrative operation, revocation and denied unauthorized request |
| 4 | B05 | Persist/reconcile one effect; Stop works; valid profile revision survives a bad edit |
| 5 | B02 | First graphical login checkpoint; then browser/files/network/audio without AI |
| 6 | B06 | Shortcut opens native entry; one real task, Stop and editable default profile through shared service/CLI |
| 7 | B11 | Current navy assets integrated into actual guest; installer assets staged |
| 8 | B12 | Blank-VM installation and update/recovery work early, before optional experience polish |
| 9 | B07 | Inspect/correct/delete/export/restore one profile preference |
| 10 | B08 | One quiet restart-safe deterministic automation |
| 11 | B09 | One EN/PT push-to-talk and spoken reply path on the supported profile |
| 12 | B10 | One isolated local MCP integration and on-demand skill |
| 13 | B13 | Reassemble all completed components into the final candidate and run the installed combined check |

Early B03-B05 work is headless in the designated target; it does not need GNOME.
B01's provider/installer spikes use throwaway fixtures, not a disguised desktop
or disk installation. If a long desktop build is clearly on the critical path,
record the reason to prioritize eligible B02; do not change dependencies or hide
two simultaneous writes. A blocked branch can be left at its verified checkpoint
while a different eligible story proceeds, with the switch recorded explicitly.

The B06 preview is a VM/checkpoint or labeled text preview, not G2. An installed
text preview after B12 still lacks later B07-B10 features. B13 must rebuild the
release assembly with those packages; an earlier B12 ISO cannot be relabeled as
final merely by changing its filename/tag. Optional *use* of voice/plugins does
not make their scoped B09/B10 acceptance optional for G2.

## 3. B01 has to remove the expensive unknowns

Freeze these small deliverables before committing to a large build:

- Exact Pi/runtime/transitive dependency/license lock and the selected
  Python/PyGObject/GIO/Node transport contracts from the design baseline. A JS engine and native GTK UI need an explicit
  async/versioned bridge, bounded messages and disconnect/cancel behavior.
- One fixture request/event/tool schema with request/task/operation IDs, bounded
  payload/output, error types and capability negotiation. Do not send secrets
  as model context. Start mutating tool calls sequentially; the executor still
  serializes conflicting resource changes regardless of engine scheduling.
- Minimal GNOME/display/browser/audio/secret-service dependency graph and package
  ownership. Check the frozen foundation ABI before accepting a newer dependency.
- Calamares candidate from its current official upstream, Qt/dependency footprint,
  module/backend requirements and a no-write configuration/target-plan probe.
  Freeze the live-to-installed root recipe: bootloader, fstab/initramfs, users,
  package repository trust, and removal of live-only accounts/keys/overlays.
- A reference CPU-compatible local model with pinned bytes/license/memory estimate.
  One representative CPU model is sufficient; do not survey every model family.
- Package transaction/update and recovery contract: owned files/configs, repository
  public trust key, free-space preflight, old boot entry and rescue path. No
  private signing keys in the image, source bundle, profiles or evidence.
- Proposed performance limits and actual available build disk/RAM/parallelism.
  The 4-vCPU/8-GiB reference is a runtime target, not a mandatory compiler sandbox.
  Build resources may differ but must be measured and portable; no native-CPU-only
  optimization may silently narrow the released CPU baseline.

Desktop/Toddy/search performance cannot be measured before they exist. B01 records
foundation/spike measurements and proposed budgets; B02/B06/B07 attach the actual
corresponding measurements. No speculative number counts as an observed baseline.

## 4. Slice execution card

Before changing a running system, write a short card in the story/checkpoint:

1. **Goal:** one observable behavior, current story/slice ID and its prerequisites.
2. **Inputs:** source commit/lock, target checkpoint and expected package/root path.
3. **Change:** exact files/recipe and the operation to perform; classify it as
   source-only, read-only target inspection or target mutation.
4. **Check:** applicable smoke IDs/subcases, command, expected exit/postcondition,
   timeout, raw log path and why this is the smallest sufficient check.
5. **Undo:** previous checkpoint/config and how to verify recovery; irreversible
   side effects require explicit uncertainty reporting rather than fake rollback.
6. **Next:** one concrete next action after this slice, not a second project plan.

For a test expected to exceed ten minutes, save the card before launch with its
reason, log and progress signal. This does not require another owner permission.
Source downloads/builds can legitimately exceed it; preserve resumable jobs.

## 5. Test selection and stopping rules

| Change | Default check |
| --- | --- |
| Planning/docs/site only | make check; affected browser view for visible copy/layout; no OS build |
| One build recipe/dependency | Integrity/ownership and direct consumer launch; reuse unchanged foundation evidence |
| Provider adapter | S04 affected protocol fixtures; S05 only when local model/transport/tool path changes |
| Task/policy/credential boundary | Relevant S06-S10/S12/S24 subcases, including the changed failure/restart edge |
| UI/persona/profile | S11 and applicable S24 stages; service fixture first, real task before delivery |
| Memory/scheduler/plugin | Respective S13/S14/S16, plus their boundary regressions |
| Installer/package/kernel/image assembly | Applicable S18-S22 and boot/recovery for affected firmware; exact final candidate at S23 |

A deterministic fixture proves code behavior, not live provider success. A real
local model must run one harmless offline task. Hardware availability is separately
reported. Owner use expands quality coverage; it cannot stand in for unresolved
boot, secrets, privilege, duplicate-write, Stop or disk-target acceptance failures.

Each command gets an explicit bound appropriate to its work. A timeout is failed
or not-run/infra-blocked evidence, never passed. Inspect the progress marker/log
before retrying. Allow one clearly classified transient-infrastructure retry;
otherwise change the diagnosed cause before rerunning. Do not reinstall the
whole desktop or rerun a long unchanged suite to repair one bad fixture.

For package/boot writes, cancellation means stop new dispatch, request a safe
boundary, and report any committing operation still active. Do not SIGKILL a
package database write solely to meet the nominal smoke timeout. A hung process
needs diagnosis and a recovery plan, not an unlimited wait hidden from the owner.

After a fix, rerun the failed/affected cases once. After a passing unchanged slice,
move on. Evidence is reusable only with the same relevant artifact/input identities;
changed consumers/config invalidate their affected rows. B13 performs a small
combined final-image pass, not every upstream component suite from scratch.

## 6. Checkpoints that survive compaction or a new agent

[PHASE-2-CHECKPOINT.md](PHASE-2-CHECKPOINT.md) is the short public continuation card.
Update it before a long job, after a verified slice, on failure and before yielding.
It links the story, evidence and decision; it does not duplicate every requirement.
Commit the card with the working slice. Publish no secrets, transcripts or private
host locations. Keep volatile machine details in ignored .local/phase2/runtime.json:

```json
{
  "story": "Bxx",
  "slice": "descriptive-slice-id",
  "source_commit": "actual-commit",
  "target": {"vm_id": "actual-id", "disk_path": "local-only-path", "checkpoint": "actual-id"},
  "job": {"pid": null, "started_at": null, "command": null, "log": null},
  "verified": {"artifact_sha256": null, "result": "not-run", "evidence": null},
  "next_action": "exact next safe command or concrete dependency"
}
```

This is a record format, not a command or a claim that a VM/job exists. Create it
only when observing real work. Write state atomically through a temporary file
and rename. PID alone is insufficient: compare command/start time/boot or VM
identity before attaching to, terminating or restarting a job. A missing process
is not evidence that its command succeeded.

### Mandatory resume algorithm

1. Inspect Git branch/HEAD/dirty changes and read the short continuation card.
   Preserve unrelated work. Resolve conflicts before building another image.
2. Check authorization and story prerequisites against status.json. A different
   latest owner instruction can change scope; record it accurately, do not infer.
3. Inspect the recorded VM/disk/checkpoint and running job/log. Confirm host versus
   guest, root mount and target identity before any privileged action.
4. Compare source/lock/artifact hashes with the last passing evidence. If a build
   is running, attach/monitor it; never launch a duplicate writer.
5. If a side effect may have committed, inspect its postcondition first. Unknown
   state stays unresolved until reconciled; do not retry a destructive command.
6. Continue the one recorded next action. If the checkpoint is stale, repair it
   from Git/logs/artifacts, note the discrepancy and run the narrow missing check.
7. Update checkpoint/evidence/status and commit a passing boundary. Do not award
   a milestone because a summary, success marker or LLM said it was complete.

## 7. No context means no guesswork

If the target/log is gone, use the last verified checkpoint and documented recipe,
not an improvised rebuild of H01-H13. If access, legal acceptance, paid resources
or destructive physical-host work is required, report that concrete missing action.
Continue unrelated authorized work where possible. Never silently replace a pinned
component, disable a safety check or declare a failed test passed to regain momentum.
