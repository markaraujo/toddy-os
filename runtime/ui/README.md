# Native setup and task entry

Run from the checkout with the user's GTK4/Libadwaita session:

```sh
python3 -m runtime.ui.app --locale en
python3 -m runtime.ui.app --locale pt-BR
```

`--data-root` selects a directory preserving the repository-relative
`ui/phase2/messages.json` and `config/phase2/software-catalog.json` layout.
`--state-directory` can select a new absolute private directory for development;
otherwise state goes to `$XDG_STATE_HOME/toddy/setup`. Package installation,
launcher substitution, shortcut conflict checks and exact guest qualification
remain separate integration work. No executable is invented in the prepared
`.desktop` template.

The GTK4/Libadwaita window provides native setup preferences, later/dismissal,
saved-state reload and optional software review without loading Pi/Node/models or
an executor. API/local selections save non-secret intent only; they neither
activate a backend nor acquire credentials/models. The AI conversation entry is
visibly unavailable because the conversational service is not yet integrated.
Current catalog candidates are informational, never installable/selectable.
Corrupt/private-state failures preserve the original state rather than resetting
it. Concurrent edits require explicit reload. EN/PT copy uses the shared catalog;
untrusted values use plain widget text, not markup.

A separate **Native system task** section can perform an explicit read-only
`system-info` task through the actual session broker. It explains that this is a
native tool rather than an AI conversation. It remains disabled until the service
provides compatible native-task capabilities. The broker runs unprivileged and
owns tool dispatch/outcome verification; the UI does not launch a shell or root
operation. This demonstration does not establish general conversational tasks,
provider setup, profile editing, credential storage or complete B06 acceptance.

`bridge.py` watches the canonical Service1 session-bus name without autostart,
authenticates its actual unique-name Unix UID and checks bounded capabilities.
Calls are asynchronous with a five-second timeout. TaskChanged is subscribed
before fetching snapshots; stale sequences are discarded and signal gaps trigger
a snapshot fetch. Reconnecting retrieves the existing task ID using GetTask;
it does not resubmit. Loss of the acceptance reply holds the submission as unknown
and disables new dispatch. Refresh only reads capabilities/current task. Stop
requests cancellation and displays the actual returned state; it promises neither
immediate termination nor reversal. Service loss invalidates pending callbacks.
The adapter uses the B05 service's actual input/schema and advertises no LLM backend.

Host checks:

```sh
python3 -m unittest discover -s tests -p 'test_setup_ui.py'
python3 -m unittest discover -s tests -p 'test_phase2_copy.py'
dbus-run-session -- python3 tests/fixtures/setup-client/smoke.py
```

The session-bus smoke uses the real asynchronous client and a synthetic same-user
service: one submission, cancellation and two snapshot fetches across name loss
and reacquisition. It is not a real broker, model or guest outcome. The model
checks cover deferred persistence, concurrent edits, unavailable software,
bounded snapshots, uncertain acceptance and reconnect projection. Actual host
GTK/Adw widget construction was checked for EN/PT and deferred save. Native guest
interaction, keyboard/focus/scale/capture, real broker tasks/Stop/reconnect and
protected credential/profile integration remain required before B06 acceptance.
