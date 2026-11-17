# First actual MVP ISO: minimal manual smoke

Use the actual MVP ISO/hash and existing owned UEFI first-install controller.
No fifth candidate-desktop boot or strict AT-SPI focus gate is required here.
The old core4 result remains: broker capabilities/shortcut registration passed;
window activation/focus was not verified. Its raw packet already used the correct
NUL delimiter, so that hypothesis does not explain the deadline.

## Open the installed frontend as the real live user

The reviewed live controller exposes only this additional fixed command:

```sh
python3 scripts/host/native_installer_live.py --mvp send assistant-launch \
  --request-id mvp-ui-open-1
python3 scripts/host/native_installer_live.py --mvp send capture \
  --request-id mvp-ui-frame-1
```

The root probe reauthorizes the actual active LIVE UID1000 session, drops to that
user/group with no supplementary groups, closes inherited descriptors and launches
only `/usr/bin/toddy` in its fixed real Wayland/session-bus environment. It neither
starts a provider/model nor changes system policy. The returned PID means launch
requested, not a visible/focused window. Review the actual captured frame and record
what is visible: Toddy window, setup/conversation tabs, service availability and any
visible error. Do not turn an unreviewed capture into a GUI pass. The normal desktop
launcher, or `/usr/bin/toddy` from the logged-in user's terminal, is also valid.

## Existing owner service and deterministic native task

Choose the existing activation button, or explicitly run the existing user unit
command from that user's terminal:

```sh
systemctl --user start toddy-agent.service
/usr/bin/toddy --cli profiles
```

This is opt-in user-service activation, not root authorization or inference. In the
same real user's terminal, the following uses the shipped same-UID/unique-owner
session client and existing canonical API; it introduces no test endpoint:

```sh
/usr/bin/python3 -I - <<'PY'
import json, sys, uuid
sys.path.insert(0, '/usr/lib')
from toddy.ui.cli import Session
from toddy.ui.task_state import capabilities
session = Session()
cap = capabilities(session.call('GetCapabilities'))
print(json.dumps(cap, sort_keys=True))
assert 'system-info' in cap['tools']
request = uuid.uuid4().hex
print('Request', request, 'profile', cap['profile_id'], flush=True)
body = json.dumps({'version': 1, 'text': 'MVP manual native inspection',
                   'tool': {'kind': 'system-info', 'arguments': {}}})
try:
    identity = session.call('SubmitTask', '(ssss)',
        (request, cap['profile_id'], cap['profile_revision'], body))
except Exception:
    print('Acceptance unknown: use the printed profile/request with lookup; do not resubmit.')
    raise SystemExit(3)
print('Task', identity)
PY
/usr/bin/toddy --cli task ACTUAL_PRINTED_TASK_ID
```

Record the actual task ID, terminal result and displayed native result. `system-info`
is a real deterministic tool path and needs no provider, Qwen model, network call
or privileged grant. It does not prove model inference. If acceptance is uncertain,
use `/usr/bin/toddy --cli lookup ACTUAL_PROFILE ACTUAL_REQUEST`; never retry a write
just because its reply was lost.

The existing Stop command is `/usr/bin/toddy --cli stop ACTUAL_TASK_ID` for an
actually running task, followed by `task ACTUAL_TASK_ID` to inspect its result.
A fast system-info task may finish before Stop; that is not cancellation proof.
Do not manufacture a long model call, change tool permissions or claim a successful
Stop from a late request. Existing source/archive-bound native B03/B04 inference,
Stop, restart/no-replay and executor evidence remains separately identified in
[the B03 evidence](evidence/B03.md) and [the B04 evidence](evidence/B04.md). Reuse
only the cases whose installed package/code/configuration pins are unchanged;
never relabel them as reruns on this final ISO.

API/local onboarding remains explicit and manually observable via the existing
[opt-in instructions](mvp-preinstalled-profile.md). No Qwen weights are bundled;
license-approved cached qualification data is optional and does not activate a
model. Capture actual installer/boot/settings results separately. This minimal
manual smoke creates no B-story/G2 completion or physical-machine claim.

## Ordinary interactive opening, without an accessibility focus deadline

For the first actual ISO, use the normal live GNOME desktop. Press Super, search
for Toddy and open its launcher, then click its visible window. This tests ordinary
opening independently of shortcut registration or accessibility focus reporting.
Do not infer a window crash from the old core4 observer deadline: its stricter
probe required an accessibility `FOCUSED` widget, an independently matched
GApplication process and visible translated labels. A failure there does not
identify which of those postconditions failed.

If a window is not visible, open the live user's Terminal and run these commands
as `toddy-live`, without sudo, pkexec, `dbus-run-session`, a substituted HOME or
injected session variables:

```sh
id -u
printf 'Session: %s\n' "$XDG_SESSION_TYPE"
/usr/bin/toddy --cli --help
/usr/bin/toddy --locale en
```

The expected live UID is 1000 and normal graphical session is Wayland. The last
command opens the same installed frontend and retains its actual startup error
on that terminal if startup fails. If another Toddy process already owns the
GApplication name, invocation activates that instance; exit 0 alone is not visible
opening proof. Select the actual Toddy window from GNOME's overview. Record the
visible screen and the specific startup failure if one occurs. Do not delete setup
state, kill user services or change desktop security to make the check pass.

The fixed `/usr/bin/toddy` launcher uses Python isolated mode and the installed
`/usr/lib/toddy` namespace. Setup can open while broker, model, executor and Secret
Service are absent. API credential access starts only when explicitly requested
on a worker thread; a missing or locked keyring is not an expected prerequisite
for opening the setup window. The protected-store path deliberately never creates
a plaintext fallback or unlocks a collection implicitly. The passwordless live
account does not imply a usable unlocked default collection; if API binding reports
that condition, keep it unavailable and use Later or an explicitly configured local
model. Do not ask for or invent a live login password.

If the window opens but native task controls are unavailable, explicitly activate
the user agent through the guided setup button or the user-unit command above,
then press Refresh service. For basic non-secret diagnostics only:

```sh
systemctl --user show toddy-agent.service \
  --property=LoadState --property=ActiveState --property=SubState --property=Result
/usr/bin/toddy --cli profiles
```

These distinguish frontend opening from service availability. They neither start
a provider nor grant privileged authority. Use the deterministic system-info
submission above before attempting model onboarding. Its default profile exposes
only system-info; do not silently enable shell or privileged tools just to prolong
a task for cancellation evidence.

For an explicitly configured local or API conversation, submit a normal request
in Conversation and press Stop while the task is actually running. Observe its
actual terminal state. The same known task can be inspected with `--cli task ID`
and stopped with `--cli stop ID`; the first Ctrl+C during `--cli ask` requests Stop
and waits, while a second Ctrl+C detaches without claiming cleanup. A completed
short request is an ordinary success, not a Stop test. Missing backend, locked
keyring, unknown acceptance and a task that ends too fast remain distinct outcomes;
record them honestly and never replay an uncertain submission.

For the first UI-only ISO whose packaged installer is the preserved older version,
keep `installer_ready:false` and disclose its known finalizer ownership bug. Correct
build-time image finalization does not repair that packaged installer or prove an
installation. Do not exercise Install from that ISO or advertise it as installable.
