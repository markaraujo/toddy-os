# Phase 2 — Additional operational decisions

Date: 2026-11-07. Follow-up to the five integration inputs. These close design
ambiguities without adding a framework, guest build or broad validation matrix.
No runtime behavior is claimed. Existing story gates remain authoritative.

## Findings and selected behavior

| ID | Gap beyond existing contracts | Selected default | Owning proof |
| --- | --- | --- | --- |
| O01 | History retention and indispensable operation records were not distinguished | Optional conversation history can be off; minimal task/idempotency/reconciliation metadata remains separate and disclosed | B05/B07; S08/S24 |
| O02 | Lock/logout and interrupted inference could leave unclear execution ownership | Lock blocks new interactive dispatch and stops capture; logout stops user agent work safely; no background session lingering by default | B05/B06/B09; existing cancellation/restart checks |
| O03 | Cost budgets lacked a rule when provider prices/usage are unknown | No remote spending by default; explicitly consented request/token limits, estimates labeled; unsupported monetary enforcement never advertised as a hard billing cap | B03/B06; S04/S12 |
| O04 | Deferred downloads lacked explicit metered-network and trust behavior | Ask before large downloads on metered/unknown networks; verified private staging, space preflight, no execution before final integrity check | B03/B12; S05/S19/S21 |
| O05 | Compatibility and diagnostic details could drift across UI/broker/packages | Capability handshake includes protocol/profile/store versions and actual availability; mismatch opens setup/recovery and blocks affected dispatch | B01/B05/B06; S01/S08/S24 |
| O06 | Support evidence could become an accidental data export | Local opt-in diagnostics preview, explicit allowlist, no automatic upload, no transcripts/persona/keys by default | B06/B13; existing secret/export checks |

## Storage and interrupted work

Initial per-profile limits: sanitized rotating logs 20 MiB total, temporary tool
output/spool 64 MiB, ten prior non-secret profile revisions within 16 MiB. Stop
accepting additional output/revisions visibly when safe cleanup cannot fit; never
truncate the active revision or reconciliation journal to force success. Optional
models/downloads have separate actual-size preflight and do not consume these
small text-state budgets. B01/B05 measure and justify any adjustment.

Retain terminal task/idempotency metadata for 30 days by default, independently of
optional conversation retention; do not store prompt/output text in that minimum
metadata. Unknown/in-flight outcomes stay pinned until reconciled. User-requested
history deletion removes conversation data while explaining retained minimal
operation records. If retained records reach the initial 64 MiB per-profile budget,
stop new task acceptance with a cleanup/recovery explanation rather than discard
live records. B05 must account for database/WAL/spool space before dispatch.

After metadata expiry, clients never automatically resend an old request ID;
unknown task status requires inspection or a separately confirmed new task.
Import/restore does not resume tasks, reuse active operation IDs, enable schedules
or restore grants. Full disk or database-write failure before durable preparation
prevents dispatch. Failure after an effect is uncertain until reconciled. Never
claim that disabling chat history disables the safety journal or provides forensic
secure erasure of SSDs/backups. Canonical SQLite backup must use a consistent native
snapshot, not copy a live database file while ignoring its WAL.

## Session, power and time

Closing the window leaves the authenticated user-session broker available for
already accepted tasks. Screen lock blocks new interactive/provider/tool dispatch
and stops microphone capture; an in-flight mutation reaches its safe boundary.
Standing automations need explicit independent authorization to operate while
locked, and cannot borrow unlocked-session interactive consent. Unlock does not
restart a stopped recording or silently resume a paused task.

Logout stops capture/inference and requests safe task shutdown; no default user
service lingering. Preserve uncertain operation state. A protected system executor
write may finish its safe commit independently and must be reconciled on next login.
Before suspend, stop capture/new dispatch and persist state; do not assume a network
stream survives wake. Reattach/reconcile after wake; no automatic provider retry.
Broad device suspend qualification remains owner backlog; basic state handling is
part of existing cancellation/restart checks.

Use monotonic elapsed deadlines for running requests, UTC timestamps for evidence
and explicit timezone for schedules. Default missed-run policy is skip with one
inspectable skipped result; no burst catch-up after reboot/time correction.
An explicitly chosen run-once catch-up needs a bounded window and operation dedup.
Clock/TLS errors are visible setup/download failures, never grounds to disable
certificate checks or silently change the frozen system.

## Acquisition, cost and diagnostics

Remote request consent names the destination/model and data scope. Disabling
spending blocks new dispatch but cannot guarantee cancellation of already billed
provider work. Unknown price is shown as unknown; token/request bounds remain
honest independent controls. Provider-issued account limits, when available, are
separate from Toddy estimates. No implicit paid test is needed for this prework.

Downloads bind artifact ID/hash/license and expected length; revalidate resumed
bytes, handle changed range/ETag responses safely, check space including staging
and extraction, and atomically promote only after final verification. Do not trust
an ETag as a signature. Proxy credentials/redirect query tokens cannot enter logs;
HTTPS redirects cannot silently downgrade to HTTP or forward credentials to a new
origin. Local endpoint configuration is validated separately from public artifact
acquisition; neither external content nor a profile import can broaden egress.

Diagnostics preview includes release/package versions, capability availability,
sanitized error codes, smoke IDs and selected hardware IDs only. Exclude environment
variables, authorization headers, endpoint query strings, user paths, persona,
profile content, database dumps and raw command output by default. Preview and
explicitly select any extra evidence; never silently post it to an issue. Redaction
is defense in depth, not proof that arbitrary logs are safe to publish.

## Execution value and scope

Use these decisions when implementing the affected existing slices; do not create
six new milestones or repeat all prior suites. The smallest affected check proves
the boundary (for example full-store refusal before tool dispatch, or a fake
unknown-price display). No new screenshots, providers, model downloads or release
acceptance are needed to complete this review. Target measurements remain pending.
