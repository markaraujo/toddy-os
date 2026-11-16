# Deterministic scheduled health binding

`Automation` binds the existing canonical `Scheduler` to one actual profile DB.
It registers only `disk-health` and `service-health`. `NativeHealth` reads local
root filesystem statistics and fixed selected systemd service ActiveState values;
it never starts a service, runs imported commands, reads user files, loads a model
or invokes a provider. Conditions drive notification fingerprints; changing free
byte counts alone never create repeated alerts.

The constructor creates private metadata tables but starts no task, timer or
notification. The service must supply independent current authenticated-owner and
standing-policy predicates. `configure` saves a disabled schedule and creates no
grant. `enable` requires current profile automation enabled, a registered selected
workflow ID and current standing authorization. Every actual dispatch/notification
checks that policy again. Config/import/clone reset does not inherit or create a
standing grant. Current locked-session background permissions belong to that
independent policy, never prompt/profile text.

The service may explicitly call `poll()` from a managed worker or `serve()` from
its managed user-session lifecycle. Never run either on a blocking GTK main-loop
callback. A private owned 0600 flock lease prevents overlapping poll/recovery
instances. Each tick considers at most two due jobs and four pending notices;
health budgets are at most 10 seconds per workflow, systemctl reads have at most
2 seconds each, and the default native service list has NetworkManager and GDM.
The optional service loop waits 30 seconds by default and never enables lingering.
No SQLite write transaction is held during a probe or desktop transport call.

An observed condition, its bounded latest details, the changed-state fingerprint
and any notification intent commit atomically through
`Scheduler.observe_in_transaction`. Unknown/full storage rolls back those records
and leaves the failed run for review; it does not quietly drop the warning or
repeat the same operation. Source-only profile revision/owner policy changes do
not authorize a workflow. Native package/root changes still use the independent
executor; this read-only monitor is not a restricted replacement agent.

Notifications have durable pending/sending/sent/denied/uncertain states.
`DesktopNotifier` provides the actual optional session D-Bus Notify roundtrip with
a 2 second bound and EN/PT copy; no email, shell command, external account or cloud
fallback. The service must supply it explicitly after native qualification.
A missing notifier keeps inspectable pending events without pretending delivery.
A lost acknowledgement remains uncertain and is never automatically sent twice.
Job cancellation atomically denies its queued pending notices. Current action revocation blocks pending sends; a send already admitted can
finish and cannot be claimed undone.

Call `recover()` only after proving the previous canonical writer is gone; the
lease must be available. Running checks and interrupted sends become uncertain,
with no replay. For the two registered read-only actions only, explicit owner
`acknowledge_read_only_failure` can retire an uncertain run as failed, retaining
history and disabling pending notices; a new run still needs a new slot/current
enable. Unknown notification outcomes stay uncertain. Stop disables new dispatch
and requests active cancellation at its safe boundary, reporting that an active
read may finish. It never advertises rollback of an already emitted notice.

History inspection is bounded and reports total run count. Explicit owner cleanup
prunes only terminal records older than 30 days; pending/running/uncertain outcomes
are never erased to restore capacity. Underlying Scheduler deduplication, skip or
bounded run-once missed policy and run/output budgets remain authoritative.
Configure/import cannot reuse an existing accepted slot to discover its outcome.

Native qualification remains: current root standing policy and managed session
timer, actual health observations, notification display and restart proof before
B08 acceptance. Source tests use actual local statvfs, explicitly labeled
service/notification fixtures and canonical SQLite/lease concurrency.

## Captured broker service binding

The service now constructs one Automation and AutomationControl per captured
ProfileRuntime context and reconciles it once under canonical service lifetime
ownership. `owner-automation-v1` advertises the bounded owner API. Registered
workflow IDs are disk-health/service-health; the existing profile validator now
recognizes exactly those workflows. This does not grant standing permission.

`StandingPolicy` calls the actual privileged executor's
`GetStandingAuthorization(action_id)` through RootClient. RootClient checks the
system-bus owner UID is root. Every predicate call requires the exact versioned
response `{version:1, action_id:<same action>, allowed:<boolean>}`. Unknown action,
malformed/mismatched/extra response fields, unavailable executor or any failed
inspection returns false. There is no cached authorization, supplied UID/session,
credential, grant creation or delegation. Owner profile text/config cannot
substitute for current root-owned standing policy. This independent policy may
permit unattended checks while the interactive owner session is locked; editing,
enabling, inspection and review still require the service's current unlocked
local owner session.

`GetAutomation(profile_id)` returns jobs, bounded last 32 runs/notifications,
latest observations, total run count, stopped state, registered workflows and last
worker tick state. The encoded inspection is at most 60000 bytes.
`ConfigureAutomation(profile_id, expected_revision, operation_json)` requires
version 1 and an exact operation schema:

- `configure`: job_id, action, interval, next_due, missed, catchup, seconds, max_runs.
- `enable` / `cancel`: job_id.
- `stop` / `prune-terminal-history`: no additional fields.
- `review-read-only`: operation_id.

Configure is always disabled and creates no grant. Enable requires current root
standing authorization and current profile workflow. Owner Stop denies
pending notices, disables schedules and requests active safe cancellation. A
later explicit owner Enable can reset the local Stop barrier, while unknown
outcomes still require review. Configure/enable/review never replay an old slot.
Root inspection occurs before the scheduler write transaction; dispatch checks
current policy independently again. Schema errors/storage/busy outcomes are
reported, never interpreted as success or automatic permission to retry.

The real service registers a 30 second GLib timer. Its callback only submits a
captured tuple of contexts to one dedicated AutomationRuntime worker and returns.
Probes, root IPC and desktop notification roundtrips happen in that worker, with
no model/provider calls and no overlapping tick. Context selection cannot move a
scheduled job into another profile. Owner configuration also requests one worker
tick without waiting for it. AutomationChanged signals contain only profile ID;
no callback diagnostics or document text is emitted.

A service lifecycle shutdown first closes new worker admission and sets each
context's cancellation barrier, then waits for the current safe boundary before
releasing canonical lifetime locks. An idle enabled schedule survives a normal
service restart. An interrupted admitted read retains uncertain state and cannot
be replayed; explicit owner Stop separately disables future schedules. No user
lingering or system-wide timer is enabled by this source change.

The optional real DesktopNotifier is wired to the service's user-session bus;
configured transport is not a claim that a notification was displayed. Pending,
sending and uncertain receipts retain the earlier no-replay rules. Required
native tests remain: current root grant/revoke and expiry, real selected service
observations, managed session timer/restart/Stop, quiet changed-state notification
display and profile isolation. Host service tests prove absent-executor denial,
configuration/worker lifecycle and durable disabled schedules; they do not grant
standing policy or fabricate a notification/native B08 acceptance.
