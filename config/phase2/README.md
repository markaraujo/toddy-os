# Phase 2 reusable contract inputs

Selected v1 design candidates, not installed configuration or executed fixtures.
Do not copy this directory to host XDG paths or activate it during planning.

- profile.schema.json and profile/: non-secret profile schema, editable Markdown
  preset and one instruction-only skill. No credentials or executor grants.
- ipc-examples.json: fictional cancellation/reconciliation examples; not a log.
- install-options.json: selected defaults/states, not an availability catalog.
- packages.json: exclusive project path ownership and offline dependency split;
  symbolic upstream capabilities are not a final dependency lock.

Canonical semantics: [interfaces](../../docs/PHASE-2-INTERFACES.md),
[installation](../../docs/PHASE-2-INSTALLATION-MATRIX.md),
[packages](../../docs/PHASE-2-PACKAGES.md), and
[owner guide](../../docs/PHASE-2-OWNER-VALIDATION.md).
B01 must prove native compatibility, freeze actual schemas/versions and record any
necessary targeted change. Static/schema checks cannot establish authorization,
path containment, crash safety or working IPC. Keep all public fixtures fictional;
never contribute personal profiles, runtime state or connection credentials.
