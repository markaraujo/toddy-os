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

Parent integration remains: advertise only registered workflows in trusted profile
capabilities; bind authenticated owner/standing policy and managed session timer;
use actual `DesktopNotifier` only when qualified; expose inspect/disable/Stop and
review/storage codes through bounded native APIs. Native persistent automation,
real service observations, notification display and restart proof remain required
before B08 acceptance. Current tests use actual local statvfs plus explicitly
labeled service/notification fixtures and canonical SQLite/lease concurrency.
