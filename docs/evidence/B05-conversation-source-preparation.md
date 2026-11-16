# B05/B06 durable conversation and private output source preparation

Source-only integration, not installed/native B05/B06 acceptance. The actual
production worker/default provider adapter is wired through the same canonical
journal and independent native/root tools. No permanent system-info-only substitute,
provider fixture passed as inference, paid call, automatic model acquisition or
root-policy relaxation is introduced. Native model, keyring, UI and packaged session
qualification remain required.

The existing Service1 extension negotiates agent-text-v1/agent-text-ack-v1 and
profile-settings-v1. It adds separate bounded output paging/Ack and canonical
config read/restore, preserving the original fixture XML methods. Normal terminal
status follows final text commit. Equal-cursor text signals report completion
changes without inventing a chunk. UTF-8 page sizing matches actual reply encoding.
Profile changes keep running task pins. Default configure-later still works with no
model/provider and native sysinfo/file tools remain independent.

ConfiguredEngine uses explicit private non-secret connection metadata and the
existing frozen LocalRuntime in a fresh helper process. Startup integrity, CPU,
resource and private Unix authentication are reused; parent cgroup qualification
and actual local model are not inferred from source. Remote lookup uses the native
protected-store worker API; capabilities never retrieve a key. Missing/locked
credentials, consent or incompatible setup fail visibly without fallback. Endpoint
credentials/query tokens/plaintext metadata fields are refused. Local startup can
be canceled without waiting for the full readiness deadline.

Known current credential values are excluded from model input and tool output;
a sliding text guard blocks reflection even split across streamed frames before
persistence. This does not claim perfect redaction of arbitrary private content.
Task status/audit contain no model transcript. Assistant text alone is bounded in
its private spool; history-off/zero-retention is a five-minute-maximum handoff,
erased on drained Ack and terminal shutdown/restart cleanup per ADR-0233. Required
unknown-operation records are never removed to simulate cancellation or privacy.

The native broker2 review found a real duplicate-acceptance race: a task could be
completed durably while the pending worker slot had not yet cleared, and the
service rejected its duplicate as busy. Corrected with a pure exact-hash
accepted_request lookup before busy/stopping/session gates. Accepted IDs return
without any queue/dispatch; changed input/revision/tool metadata conflicts. New
requests still require current session and normal gates. Focused lookup/locked/
identity checks cover this without depending on timing. The missing ToolError
import in the async error handler is also corrected; an actual GIO setup failure
is held for review and subsequent service requests remain available.

Actual focused host results include canonical output/retention tests, three
synthetic-engine orchestration checks with real temporary file effects, connection
schema/privacy/consent and fresh-helper failure/cancellation checks, and known-key
fragment reflection refusal. An early text test matched the word 'line' in the
metadata field 'deadline'; its assertion was corrected to the actual output marker.
The initial source smoke extension failed to insert its new actions; that was fixed
before accepting its reported flags. Final executed source smoke below includes
all claimed actions.

- Actual GIO/private-session-bus/native-logind broker source smoke passed in0.209s:
  native sysinfo/file write/dedupe, unmanaged shell no effect, config get/apply/
  restore, missing engine setup held (not stranded queued), and empty transient
  output drained/Ack erased. No root, provider or target mutation.
- Actual production worker/default createProvider/Pi/private Unix HTTP synthetic
  protocol plus BrokerCore/canonical journal/text passed in0.183s: one actual
  temporary file effect, streamed text, clean model-worker completion, canonical
  task completion, Ack erasure and duplicate returning its existing task with exactly
  two generation requests/one effect. This server is synthetic, not a real model.

Next: coordinator native broker3 must recheck the exact duplicate race and package/
owner/cgroup boundaries. Then qualify this exact configured local helper/production
worker through native UI conversation, Stop, restart/effect reconciliation, protected
keyring failures and configuration recovery. No criterion is completed by this
source preparation alone.

Pinned active provider semantics additionally reject retries/noncompatible local or
context/output/tool limits before activation, preserving the working revision. The
installed worker directory fallback (`worker/` versus source `engine/`) has a focused
layout check. Actual protected-key lookup is deferred to the dispatch worker;
GetCapabilities reports checked-at-dispatch without retrieving a secret.

Repository `make check` passed519checks in9.569seconds on this source integration.
