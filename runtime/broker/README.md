# Toddy user broker source

This source implements durable native tasks and the production engine bridge.
Installed/native integrated acceptance remains separate. The default profile uses
configure-later; the broker does not download a model, start a remote request or
create an administrative grant automatically.

The session Service1 interface authenticates the actual peer UID. Capabilities
advertise current profile/revision, provider mode, native tools and negotiated
text/settings features. Agent tasks require the explicit body
`{"version":1,"text":"...","agent":true,"remote_consent":false}`.
Remote mode additionally requires fresh per-task consent and enabled profile
spending; local mode rejects remote consent and never falls back. Protected
credentials are looked up in the dispatch worker, never retrieved synchronously by
GetCapabilities. Locked/missing secret service fails visibly without plaintext.

Configured connection metadata is a private owned0600 regular JSON file under
XDG_CONFIG_HOME/toddy/connections/<connection_ref>.json. It contains no key, token,
password, grant or executable hook. Local metadata has exactly version1,adapter_id,
model_id and canonical model_path; the initial supported local model is the frozen
B03 model, rehashed by the actual LocalRuntime before use. Remote metadata has
exactly version1,adapter_id,model_id,base_url,context_tokens and max_output_tokens.
The endpoint must be HTTPS without credentials, query tokens or fragments.
Protected credential entry/removal uses the native keyring surface separately.
Connection setup/acquisition UI qualification remains pending; do not advertise
manual source metadata preparation as a completed installed first-run experience.

Local loading runs in a fresh private helper process, preserving the accepted
LocalRuntime integrity/CPU/resource/Unix-socket boundary and avoiding preexec_fn in
a threaded broker. Model helper/worker descendants belong to the installed user
unit's control group; no lingering user service is enabled. The actual source
runtime must be qualified with the frozen model in the designated target before
claiming the integrated local path.

Only the broker invokes native tools and the independent root Executor1. Pinned
profile availability never grants privileges. Durable operation IDs precede every
effect; uncertainty blocks replay and survives restart. A worker done event cannot
hide a missing postcondition. Shell exit alone does not prove arbitrary effects.
The managed ordinary shell requires the verified user-systemd scope/parent; there
is no production process-group fallback.

TaskChanged contains fixed state/IDs only. GetTaskText pages private assistant text
separately, with independent cursors and latest_sequence. TaskTextChanged can repeat
a cursor when only the complete flag changes. The default output is a temporary
handoff: Ack of the complete drained cursor deletes it, with a five-minute terminal
maximum and shutdown/restart cleanup. Positive explicit history retention follows
its selected days. Required operation metadata remains separate. See ADR-0233.
