# B04/B05 authenticated native broker source preparation

This is source preparation with actual development-host execution. It does not
claim native target acceptance, B04/B05/B06 completion, a model-backed assistant,
an installed runtime package or G2. The source service advertises
`agent_backend:false`; the enabled default action is explicitly native system
information, never synthetic AI success.

`runtime/broker/service.py` implements the existing authenticated Service1 session
D-Bus interface for capabilities, submit/query/cancel and bounded config
validate/apply staging. The actual bus sender must have the broker's nonroot UID.
Logind's same-UID local active unlocked display session gates interactive dispatch;
missing logind/session fails closed. This user-session check never substitutes for
independent root policy. Root operations always go through the actual root-owned
Executor1 system-bus name and its current grant checks; clients supply no identity,
session, grant or arbitrary root callback. The executor independently authenticates
the broker and resolves session lifetime.

The shared canonical database stays in XDG_DATA_HOME/toddy/profiles/toddy-default,
matching the harness contract. Default workspace is the private owner ~/Toddy
folder. A lifetime broker lock and one-worker/one-pending-task dispatch preserve
bounded execution. Signals are coalesced at at most 10 Hz; snapshots contain fixed
sanitized state codes and IDs, never prompts, tool arguments/results or exception
text. The UI must reattach the existing task after disconnect, not replay submit.

`core.py` routes actual unprivileged system information, scoped file read/write
and explicit argv tools, plus enabled root configuration/command/package/service/
network adapters. Pinned profiles restrict tool availability, but enabling a root
tool grants nothing. Config stages are bound to the caller's unique bus name and
expected revision, expire after ten minutes, and cap at eight. Complete filesystem
bundle import/export and broader profile management remain unavailable. A small
follow-up rejects unsupported schema keywords inside condition/not rules instead
of treating those failures as a conditional mismatch.

Known configuration/package/service effects require an adapter's actual verified
postcondition. Arbitrary shell/root-command exit does not prove arbitrary side
effects and remains uncertain. Read-only executor inspection can reconcile a known
completed root effect without dispatching it again. Stop reaches the managed
ordinary process and sends independent executor cancellation; package/boot commits
remain subject to their safe boundary. Native source user-service templates retain
KillMode=control-group. Ordinary arbitrary detached-child containment is **not**
proven by process-group cleanup: production per-tool user scopes and their actual
Stop/restart denial tests remain required before advertising that guarantee.

Focused core checks passed six tests in 0.039 seconds. They include actual temporary
workspace write/read postconditions, pinned selection, unavailable/locked routing,
metadata-aware request deduplication, and adapter-only root inspection/dispatch
separation. Adapter-only root tests perform no privileged host filesystem change.
Nine affected profile checks passed in 0.084 seconds.

Actual source smoke command:
`dbus-run-session -- /usr/bin/python3 tests/fixtures/broker-service/smoke.py`.
On the development host UID 1000 it passed in 0.323 seconds using real GIO,
a private session bus, actual native logind and a temporary private workspace.
It completed system information, staged/applied config, wrote a file and deduped
its task, stopped an actual sleeping command and verified its PID disappeared,
then killed the broker after a real fsynced file effect. Restart held the task
uncertain and repeated submit returned its existing ID without writing another
byte. The raw arbitrary-shell outcome stayed uncertain throughout. No root call,
model/provider/network request or guest mutation occurred in this source smoke.

Next: install/qualify this exact broker and independently packaged root executor in
the designated target's real session. Run native same/wrong-user routing,
lock/logout/revoke, Stop, crash-effect/reconcile and config recovery; integrate the
native UI TaskClient against this actual service. Then wire the accepted provider/
local worker behind the journal before enabling conversation. Preserve source-only
versus installed/native results and do not award unfinished story criteria.

Repository `make check` passed 411 checks in 6.734 seconds for this source slice.
