# Native setup, conversation and profile entry

From the checkout:

```sh
python3 -m runtime.ui.app --locale en
python3 -m runtime.ui.app --locale pt-BR
```

Package-relative imports also support the installed `toddy.ui.app` namespace.
The lightweight UI needs only its setup/shared/connections helpers, GTK4 and
Libadwaita; it does not import the optional broker, Pi/Node, model or executor.
`--data-root` selects a tree containing the shared relative `ui/phase2/messages.json`
and `config/phase2/software-catalog.json` inputs. `--state-directory` can select a
new absolute private development directory; otherwise use
`$XDG_STATE_HOME/toddy/setup`. Actual packaging/launcher substitution, shortcut
conflict checks and native target qualification remain integration work.

Setup saves later/API/local non-secret intent and dismissal, preserves pending
choices, supports explicit reload after concurrent edits and leaves the desktop
usable without a backend. Current unqualified software candidates are informational
and have no install control. Provider credentials use a separate masked libsecret
form, never profile JSON or pending state; Save does not activate a provider or
authorize spending. Missing/locked secret services fail visibly without plaintext
fallback. [Protected-store details](../connections/README.md) describe exact scope.

The conversation entry enables only when the actual same-user service negotiates
`agent-text-v1`, advertises an available agent backend and identifies its selected
local/remote provider mode. Remote tasks require a fresh unchecked per-task consent;
local tasks always submit remote_consent=false. Without those capabilities, entry
stays unavailable while setup and the desktop remain usable. A separate explicitly
labeled read-only `system-info` native task does not pretend to be AI conversation.
Both use the same durable task snapshot, progress, visible Stop and uncertainty
handling; the UI never executes a shell/root tool directly.

`bridge.py` asynchronously authenticates the unique session-bus owner's Unix UID,
validates bounded capabilities and subscribes before snapshots. Status signals
carry no transcript. The negotiated `TaskTextChanged(task_id,sequence)` signal only
announces a private update; `GetTaskText(task_id,after_sequence)` returns bounded
pages. Each chunk is at most1024 UTF-8 bytes and a task's text at most256KiB.
`latest_sequence` drains backlogged pages; `complete` means text finalized, never
task success or page exhaustion. Text renders as plain GtkTextBuffer content,
not markup or executable instructions. Display updates coalesce to at most10Hz.
With history enabled, the window keeps at most eight recent task exchanges in
RAM and labels that choice. History off retains only the current response
temporarily, clears previous exchanges on the next task and negotiates
AcknowledgeTaskText after draining finalized text, allowing prompt broker erasure.
A lost acknowledgement is not blindly retried; bounded broker transient retention
remains the fallback. It does not claim a persistent full-history browser.

Reconnect fetches the existing task ID and text cursor without resubmitting work.
Loss of a submission reply holds unknown acceptance and blocks automatic replay.
Stop requests cancellation and reports actual state; no immediate reversal is
promised. Stale replies are ignored by service/task generation. Text-page failure
does not remove the independent Stop path. Explicit Refresh reads capabilities
and current work. Closing clears the credential field and cancels UI callbacks;
the broker retains authoritative task lifecycle policy.

Profile editing negotiates `profile-settings-v1`. GetProfileConfig reads actual
current JSON/revision plus at most32 prior revision IDs. Validation stages a
candidate against that exact revision; Apply uses the owner-bound staged token.
Editing invalidates a staged validation, and concurrent revision changes require
explicit reload rather than overwriting someone else's configuration. Restore
selects an actual prior revision through the broker's expected-revision guard.
Invalid configuration preserves the current profile. Existing running tasks retain
their pinned revision. This UI does not write the canonical database or grant root.
Full persona/bundle import/export and multi-profile controls remain separate work.

Checks:

```sh
python3 -m unittest discover -s tests -p 'test_setup_ui.py'
python3 -m unittest discover -s tests -p 'test_credentials.py'
python3 -m unittest discover -s tests -p 'test_ui_offline_imports.py'
python3 -m unittest discover -s tests -p 'test_phase2_copy.py'
dbus-run-session -- python3 tests/fixtures/setup-client/conversation.py
# Requires an actual GTK display; synthetic service, no provider or keyring access:
dbus-run-session --config-file tests/fixtures/setup-client/bus.conf -- python3 tests/fixtures/setup-client/conversation.py --gtk --locale pt-BR
```

The private-bus fixture drives real async client/native controls with synthetic
responses: Send, paged literal text, Stop, invalid config refusal, Validate/Apply,
Restore and owner loss/reconnect with exactly one submission. Protected-store
checks use a fake keyring; the credential adapter was not exercised on real keys. These do not prove native
guest/provider/model success. Actual installed S11/S12/S24, keyboard/focus/scale,
credential isolation, default-harness task and recovery evidence remain necessary
before B06 acceptance.

## Terminal client

`toddy --cli ask` reads one bounded prompt from standard input;
`--allow-remote` explicitly consents to this request's configured remote provider.
`task ID` drains private paged text and observes the durable task, `stop ID`
requests a safe-boundary Stop, and Ctrl+C requests Stop before a second interrupt
detaches. `profiles`, `create-profile ID`, `select-profile ID GENERATION`,
`history PROFILE` and `lookup PROFILE REQUEST` use the same canonical service.
Generation is an explicit compare-and-swap value from `profiles`. No graphical
libraries are imported by help or the terminal module.

The client pins the authenticated same-UID unique bus owner. A lost acceptance
reply causes only a read-only request lookup, never automatic resubmission.
An unresolved acceptance prints its profile/request IDs for later lookup.
Terminal control characters are filtered from provider/status output. Prompts
are not saved by this client; prefer standard input over command-line text if
process arguments should not expose them. No plaintext credential fallback is
provided. Native installed terminal lifecycle remains B06 qualification.
