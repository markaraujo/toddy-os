# Phase 2 native UI preparation

This directory contains reusable design inputs for the future native desktop,
assistant setup and graphical installer. It does not implement the UI, start a
B story or establish runtime acceptance. Native product copy currently covers
English and Brazilian Portuguese; the public portal's additional languages do
not expand this scope.

## Copy catalog

`messages.json` is the canonical English source with `pt-BR` locale data. Stable
semantic IDs let future components share reviewed wording without embedding it
in screenshots or duplicating strings. `schema_version` describes this asset
format only, not the assistant protocol or profile format. Context and severity
are editorial metadata, not authorization decisions.

Use named placeholders (`{provider}`, `{disk}`, and so on) with identical names
in every translation. Treat substituted values as untrusted text and escape
according to the target widget. Never pass secrets, command output or raw error
traces as placeholder values. Catalog values contain no credentials or actual
devices. `disk` must eventually be a verified, unambiguous target description;
a friendly label alone is not sufficient for destructive confirmation.

Keep IDs stable when refining wording. Add a new ID when the meaning changes.
Do not concatenate fragments to build translated sentences. The consumer must
handle missing translations explicitly; this catalog does not prescribe a
runtime fallback algorithm.

Critical controls, disk warnings and credential errors deliberately use neutral
language. Toddy's personality belongs in optional welcome text, tips and
installer narrative, never in the meaning of a permission, destructive action or
failure. The catalog does not replace final user review of the native UI.

## State meanings

The seven task-state IDs are `task.queued`, `task.planning`, `task.running`,
`task.waiting`, `task.completed`, `task.failed` and `task.canceled`. They are copy
bindings, not a transition table or wire contract. Show completed only after
verification. Stop prevents further dispatch; an in-flight write may need a
safe stopping point. Cancellation does not imply rollback. An interrupted action
with an unknown result must remain visibly uncertain until reconciliation;
reconnection must not create a second operation.

Provider setup can be deferred. A local-only policy never silently falls back to
an external provider. A locked or unavailable secret store never permits
plaintext credential storage. Runtime capabilities and exact recovery behavior
remain subject to the B-story implementation and validation plan.

## Semantic scenarios

`scenarios.json` supplies fictional inputs, expected UI states, catalog references
and safety invariants for future component previews and focused integration
checks. These are **not executed tests, acceptance evidence, commands, backend
payloads or a service protocol**. Setup and installer labels in `expected_states`
are descriptive fixture labels, not new task states. No real target path,
credential or person is included. Rendering a fixture must have no side effects.

Use these scenarios when implementing the relevant B-story slice. Runtime tests
must independently prove cancellation, reconciliation, credential handling and
disk safety. Preserve their real evidence under the validation plan instead of
changing the fixture's `execution_status` to imply they ran.

Run the lightweight catalog integrity check from the repository root:

```sh
python3 -m unittest discover -s tests -p 'test_phase2_copy.py'
```

This checks locale/placeholder parity, task-state coverage and fixture reference
integrity. It does not execute an agent, installer or guest OS.

## Native integration inputs

`identity.json` selects stable app/icon and planned service names. The desktop
entry remains an unresolved template until the assistant executable exists.
`icon-roles.json` maps semantic controls to installed GNOME theme lookups; vendored
SVGs retain mockup provenance, not a second runtime icon theme. Native branding
package ownership and defaults are documented in
[the branding inputs](../../assets/brand/gnome/README.md).

Application IDs follow [GNOME guidance](https://developer.gnome.org/documentation/tutorials/application-id.html);
launcher syntax follows the [Desktop Entry Specification 1.5](https://specifications.freedesktop.org/desktop-entry/latest/).
These references are not exact guest-version locks.

Software scenarios now include deferred offline choices, setup without an agent
and unavailable unqualified candidates. The open catalog/qualification boundary is
[documented here](../../docs/PHASE-2-SOFTWARE-CATALOG.md); these are not executed
package tests or an installer protocol.
