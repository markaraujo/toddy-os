# ADR-0106: User-customizable harness with profiles and skills

- Date: 2026-11-07 America/Sao_Paulo
- Status: Accepted owner requirement; exact schema/API implementation pending
- Extends: ADR-0105 and current Phase 2 plan; no change to foundation evidence

The owner explicitly requested user customization of the personal assistant's
harness and asked to follow Hermes/OpenClaw patterns. Adopt independent named
profiles, editable persona/identity/user instruction files, validated versioned
configuration, on-demand SKILL.md bundles and inspectable profile-scoped memory.
See docs/PHASE-2-HARNESS.md for the complete contract and upstream sources reviewed
2026-11-07. Borrow conventions; do not install those products or promise direct
compatibility with all their plugins, configuration fields or internal runtimes.

Keep the Pi engine behind the replaceable Toddy interface. The user can change
persona, providers, tools, skills, memory, workflows and bounded execution settings.
Use XDG per-user configuration/state separation and default secret-free exports.
B01 defines contracts; B05 provides atomic revisions/rollback/task pinning; B06
provides UI/CLI profile controls; B07 scopes memory; B10 provides skill/plugin
extensions. S24 is a small targeted check, not a new exhaustive ecosystem suite.

Customization cannot grant authority. Administrative policy, credential isolation,
Stop and authenticated IPC remain independently enforced. Arbitrary extension code
runs outside UI/GNOME/root processes. Invalid imports/config leave the current
profile working; provide recovery/reset without changing provider or spending.

Rejected alternatives: fixed prompts require OS changes for personal behavior;
arbitrary in-process/root plugins defeat the safety boundary; copying a full
external assistant contradicts the chosen initial implementation. A visual agent
builder and simultaneous multi-agent management add unnecessary preview scope.

Plan verification is repository consistency only. No product profile was created,
no engine installed and no runtime acceptance claimed by this ADR.
