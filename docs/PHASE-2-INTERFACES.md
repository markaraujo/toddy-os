# Phase 2 — Selected v1 integration contracts

Date: 2026-11-07. Design contracts with reusable fixtures; no service, validator,
transport or installed command is implemented here. B01 verifies these candidates
against the pinned native stack and records any necessary targeted revision.
Do not reopen settled product choices merely because runtime proof remains pending.

## 1. Profile and skill input

[profile.schema.json](../config/phase2/profile.schema.json) defines the candidate
v1 non-secret configuration. The [default example](../config/phase2/profile/config.json)
ships a deferred provider, one read-only tool/skill selection, disabled automation,
extensions and history, and no connection, credential or administrative grant.
The companion Markdown supplies editable persona/identity/preferences/instructions.
This is a starting preset, not a permanently restricted assistant: owner policy
can independently authorize full administration as required by the PRD.

IDs are lower-case ASCII letters/digits/hyphens, starting with a letter, at most
64 characters. Unknown properties/schema versions fail without altering the active
revision. Apply schema validation plus semantic validation: references must resolve
to installed/enabled compatible adapters/tools/skills; budgets cannot exceed
measured provider/context or independent owner-policy limits. A JSON Schema pass
alone cannot establish these facts, path containment, permission or concurrency.
Use offline bundled schemas only, bounded strict UTF-8 JSON, reject duplicate keys,
NaN/Infinity and recursive/pathological input. No remote schema retrieval at apply.

First-preview limits: config 64 KiB, each instruction file 32 KiB, skill metadata
4 KiB, skill body 32 KiB, reviewed skill resources 256 KiB each, full import 8 MiB
and 128 entries after expansion. Reject archives with symlinks/hardlinks, traversal,
absolute/duplicate paths, special files, undeclared payload or expansion beyond the
bounds. Hash canonical actual bytes; do not assume a matching filename is trusted.

`connection_ref` is an opaque per-user connection-store reference, not a URL, key,
password, secret-service value or portable credential. Connection settings and
provider endpoints are managed separately and validated by the broker. Default
exports remove connection refs and reset provider routing to deferred; import
requires explicit rebind/review. Private provider, persona and memory exports never
belong in Git. Do not import root policy or copy tokens from another profile.

The minimum SKILL.md subset is exactly the example's front matter: unique `name`
and plain `description`, then Markdown instructions and optional reviewed local
`references/` files. No executable hooks, YAML tags/aliases or automatic imports.
Use a bounded parser for this subset; do not add a general YAML execution feature.
Load metadata initially and body/resources only when selected. A skill cannot
expand tool availability, credential scope or executor grants.

The effective config is defaults -> selected profile -> explicit bounded task
options. Canonical revision = SHA-256 of a sorted relative-path/hash manifest of
validated config/Markdown/skills/workflows (excluding runtime state/secrets).
Use expected-revision compare-and-swap, preserve the previous valid revision and
atomically activate the complete new revision. Pin its schema/revision to each
task; running mutations never adopt a new profile mid-operation. Unsupported
workflows/hooks remain rejected or unavailable until their owning story exists.
The [harness contract](PHASE-2-HARNESS.md) controls recovery and migration.

## 2. UI / broker interface

Selected session bus name: `io.github.markaraujo.Toddy.Service`;
object `/io/github/markaraujo/Toddy/Service`;
interface `io.github.markaraujo.Toddy.Service1`. No HTTP listener. Use GIO async
calls and session peer ownership checks; authenticate the actual sender rather
than trusting profile/UID fields supplied by the caller. Bus unique-name changes
invalidate the connection; the client reattaches, not resubmits an operation.

Candidate typed method arguments use D-Bus `s` for bounded UTF-8 strings and `t`
for unsigned 64-bit sequence numbers. JSON strings below carry strictly validated
versioned bodies, not arbitrary commands. B01 emits the final introspection XML
and tests GIO signatures; the following names/types are the selected design.

| Method | Inputs | Result and invariant |
| --- | --- | --- |
| GetCapabilities | none | `s` versioned capabilities/limits JSON; mismatch disables dispatch with visible explanation |
| SubmitTask | `s request_id, s profile_id, s expected_revision, s input_json` | `s task_id`; persist accepted request and revision before dispatch |
| GetTask | `s task_id` | `s snapshot_json`; latest durable sequence, state, uncertainty and bounded summary |
| RequestCancel | `s task_id, s request_id` | `s acknowledgement_json`; accepted cancellation is not rolled-back/completed work |
| ValidateProfile | `s profile_id, s expected_revision, s candidate_json` | `s validation_json`; no activation, credentials or policy changes |
| ApplyProfile | `s profile_id, s expected_revision, s validated_revision` | `s result_json`; reject stale validation/revision and apply atomically |

`validated_revision` identifies a broker-staged validated candidate, not arbitrary
caller filesystem bytes. Each stage is owner-bound, bounded, expires after 10
minutes and is checked again for exact bytes/revision at apply. Profile Markdown
and import/export operations use the same validated staging mechanism; final
file-selection/FD details are pinned in B01, never arbitrary root filesystem paths.

Signal `TaskChanged(s task_id, t sequence, s snapshot_json)` reports authoritative
persisted state. Every snapshot has protocol version, pinned profile revision,
task ID, sequence, state, cancel_requested, result_uncertain, summary and current
operation ID. Subscribe before GetTask; discard signals at or below the snapshot's
sequence. On gaps/reconnect obtain another snapshot. Chat output can be paged
separately; it is never an authorization channel. Do not send tokens, raw tool
traces, credentials or unlimited transcripts over a status signal.

Initial bounds: input text 16 KiB, SubmitTask body 64 KiB, status snapshot 32 KiB,
summary 4096 characters, worker frame 1 MiB and tool output 256 KiB per call before
explicit truncation/spooling to private bounded storage. Coalesce display updates
at up to 10 Hz; cap each subscriber queue at 256 events. A slow UI is disconnected
and recovers via GetTask, never blocks execution or forces unbounded buffering.
Persistent task/event retention is bounded by a separately reviewed store policy;
minimum reconciliation/audit records cannot disappear while an outcome is unknown.

No automatic retries of dispatch: request IDs are unique per authenticated user
and profile. Persist request hash/task binding; same ID+same validated input returns
the same task, same ID+different input is rejected. Retain binding through the
task's documented retention window; an expired/unknown ID must not be silently
replayed by clients. UI timeout means unknown acceptance until reconciled.

Task states stay queued/planning/running/waiting/completed/failed/canceled.
`waiting` covers permission/input/reconciliation reasons. Uncertainty is a
separate visible flag, not success or a new terminal state. Cancellation prevents
new dispatch, requests worker abort and waits for an in-flight write's safe commit
point. Verify the postcondition before any terminal result. A restart reconciles
the durable operation ID; it does not repeat the operation to discover its result.

## 3. Broker / Pi worker and executor

Private worker stdin/stdout uses a 4-byte unsigned big-endian length followed by
strict UTF-8 JSON, at most 1 MiB including the JSON body. No banner on stdout.
Kinds: hello, run, text, tool_request, tool_result, cancel, done, error. Every
non-hello message carries protocol version, worker/run/request IDs and monotonic
per-run sequence. Unknown versions/kinds, oversized/truncated frames, duplicate
JSON keys and out-of-run messages stop dispatch and surface a classified error.
Hello must arrive within 5 seconds; idle does not mean an active run timed out.
No unbounded queue: at most 32 pending worker messages; abort/reconcile rather than
silently losing a tool request. Stderr is bounded/sanitized, not a secret log.

The worker requests a declared tool with structured validated arguments. Only the
broker can route it; only the executor can carry out an authorized root operation.
Tool output is untrusted data. The worker never owns the canonical task database,
root credentials, keyring handle or policy. One mutating operation at a time;
executor resource locks and current-grant checks remain authoritative even if a
worker requests parallel work. A crashed worker cannot justify repeating a write.
B01 freezes per-kind schemas/actual Pi callbacks in a tiny deterministic spike.

The root interface uses system bus `io.github.markaraujo.Toddy.Executor`, object
`/io/github/markaraujo/Toddy/Executor`, interface
`io.github.markaraujo.Toddy.Executor1`. It receives a broker operation ID, operation
kind and bounded validated arguments, binds actual caller identity, checks current
owner policy and records before/after postconditions. The request cannot carry a
self-approved UID/grant. A full-administration grant remains possible through the
authenticated dedicated policy surface; persona/imported text cannot create one.
Root service imports no GTK, model or plugin code. Actual authorization/operation
methods, crash journal and revocation denial proof belong to B01/B04/B05; this
preparation is not a new root API implementation.

## 4. Proof and fixture ownership

[ipc-examples.json](../config/phase2/ipc-examples.json) demonstrates benign task
state/cancel/reconciliation semantics. All IDs and revision hashes are fictional;
the fixture is not an executed event log. B01 must add the final required envelope
fields and strict per-kind schemas when freezing transport. The examples share UI
state names, not its semantic-scenario format or a production persistence schema.

B01: bounded framing, invalid/version/duplicate input, tiny tool and no-write
installer spikes. B03: adapter/local proof. B04/B05: independent authorization,
revocation, durable idempotency/reconciliation. B06: async UI, cancellation and
reconnect. B10: actual plugin isolation. Do not add live endpoints or download a
model to validate these repository examples.

References checked 2026-11-07: [JSON Schema draft 2020-12 core](https://json-schema.org/draft/2020-12/json-schema-core)
(schema dialect, not a guest dependency lock). D-Bus signature details must be
verified against the actual GIO/D-Bus target during B01; no current-target transport
proof is inferred from this document.
