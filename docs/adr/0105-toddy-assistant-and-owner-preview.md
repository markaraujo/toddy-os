# ADR-0105: Native Toddy assistant and focused owner-preview validation

- Date: 2026-11-07 America/Sao_Paulo
- Status: Accepted product direction; engine/runtime versions provisional
- Refines: PRD Phase 2 and B01-B13; supersedes exhaustive Phase 2 validation as a preview prerequisite
- Preserves: ADR-0063 guest-implementation boundary and historical H01-H13/G1 evidence

## Context and owner instruction

The owner accepted the analyzed architecture and requested a detailed Phase 2
plan, then a navy brand revision preserving the logo. The assistant should behave
as a device-native Toddy with a Siri/Jarvis-style entry point, minimal Ubuntu-like
GNOME desktop, optional OpenCode/VS Code and API/local/deferred AI setup. OpenClaw
and Hermes are references, not initial bundled assistants. The owner additionally
requested installer support for third-party packages such as video drivers.

The owner explicitly prioritizes performance, security and basic working tests;
longer and broader validation should happen during owner use. This is approval
to revise acceptance, not permission to fabricate results or omit fundamental
privilege, secret, cancellation, installation and recovery checks.

## Decision

Adopt docs/PHASE-2-PLAN.md and docs/PHASE-2-VALIDATION.md as the Phase 2 execution
and scoped acceptance contract. Keep B IDs/weights and foundation progress intact.
Use GNOME/Wayland, a GTK4/Libadwaita Toddy UI, an unprivileged user service, a
separate privileged executor, SQLite/FTS memory and optional llama.cpp inference.
Pi Agent Core/Pi AI are the preferred reusable engine, subject to B01 pinning,
license/compatibility review and minimal target spike. Keep it replaceable.

Add configurable quick entry, explicit Stop, optional speech, app choices and
hardware-aware third-party firmware/driver/application choices. Third-party
support requires compatible owned packages and license review, not adding Ubuntu
repositories. Hardware detection/VM selection tests do not establish GPU support.

Deliver an experimental owner preview after focused smoke checks; preserve a
visible owner-use backlog for broader devices, models, soak and subjective UX.
Retain all security-critical acceptance, exact artifact identity, honest result
classification and rescue access. Do not rerun unchanged full foundation suites.

The current request authorizes planning and repository brand/UI design assets.
It does not ask to provision/build the Phase 2 guest now; do not treat it as proof
of completed owner foundation testing. B01-B13 remain unstarted. Brand preparation
is not B11 guest acceptance. Start guest implementation when explicitly requested.

## Alternatives and consequences

Bundling a complete OpenClaw/Hermes install adds a second product identity and
integration surface contrary to the requested initial direction. Rewriting every
provider/agent primitive wastes effort. A cloud-first runtime conflicts with the
local/provider-independent requirement. A fully custom GNOME shell adds upkeep.

The chosen architecture still needs durable operation reconciliation, policy,
packaging and security work; a library does not supply those guarantees. Basic
validation shortens the feedback loop and reduces coverage; disclose untested
areas rather than representing the preview as fully qualified. No wall-clock
completion estimate is credible before the first desktop integration measurement.

## Sources and verification

Official sources reviewed 2026-11-07; these are moving documentation, not frozen
release inputs. B01 must record exact selected versions and package names:

- Pi toolkit: https://github.com/earendil-works/pi (MIT; former badlogic/pi-mono).
- Agent core: https://raw.githubusercontent.com/earendil-works/pi/main/packages/agent/README.md
- Providers: https://raw.githubusercontent.com/earendil-works/pi/main/packages/ai/README.md
- GNOME GTK4/Libadwaita guidance: https://developer.gnome.org/hig/
- Shortcut support: https://help.gnome.org/gnome-help/keyboard-shortcuts-set.html
- Custom styling constraints: https://developer.gnome.org/hig/guidelines/ui-styling.html
- Local inference: https://github.com/ggml-org/llama.cpp

This ADR records a plan, not a runtime benchmark or implementation test. Repository
consistency is checked with make check; story acceptance is updated together with
status.json and generated dashboard. No workstation RAG registration/sync.
