# Toddy — User-customizable harness contract

Revision: 2026-11-07. Accepted owner requirement, implementation pending.
This extends [the Phase 2 plan](PHASE-2-PLAN.md) and replaces any assumption of a
fixed persona/tool loop. See [ADR-0106](adr/0106-user-customizable-toddy-harness.md).
The user can meaningfully change how their assistant works without rebuilding
Toddy OS. Personal customization must not become a hidden administrative grant.

## 1. Borrow patterns, not complete products

Use the documented Hermes and OpenClaw patterns: independent named profiles,
editable identity/persona/user-context documents, a versioned non-secret config,
load-on-demand skills and an inspectable memory layer. Do not install either
product, copy its whole default tool catalog or claim binary/config compatibility.
Use the selected Pi libraries behind an internal adapter; Toddy owns this contract.

Official sources reviewed 2026-11-07, moving documentation rather than pinned
implementation dependencies:

- [Hermes profiles](https://hermes-agent.nousresearch.com/docs/user-guide/profiles/): separate configuration, persona, sessions, skills and memory per profile.
- [Hermes skills](https://hermes-agent.nousresearch.com/docs/user-guide/features/skills/): progressive on-demand skill instructions.
- [OpenClaw workspace](https://docs.openclaw.ai/concepts/agent-workspace): editable SOUL.md, IDENTITY.md and USER.md conventions.
- [OpenClaw skills](https://docs.openclaw.ai/tools/skills): SKILL.md with metadata, supporting resources and explicit discovery/loading rules.
- [OpenClaw memory](https://docs.openclaw.ai/concepts/memory): distinguish compact curated knowledge from exhaustive transcripts; provenance matters.

These are patterns adapted to Toddy, not a statement that current upstream APIs
are interchangeable. B01 pins the engine and documents the minimum supported
SKILL.md subset (name, description, instructions and local resources).

## 2. User-facing customization

| Surface | User can change | First-preview limit |
| --- | --- | --- |
| Persona | Name, tone, language, response style and personal instructions | A useful Toddy preset is supplied; OS brand/logo stays separate |
| Model routing | Provider/model, compatible endpoint, context and usage budgets | Only tested adapters/profiles advertised; no silent remote fallback |
| Tools | Enable/disable installed tools and group them by purpose | Availability never overrides executor permissions |
| Skills | Create/edit/import/remove instruction bundles and supporting resources | Imported helpers do not execute on import; installation is separate |
| Memory | Inspect/edit preferences, retention, export/delete and profile scope | Canonical SQLite/FTS remains authoritative; no duplicate truth |
| Automation | Named schedules/workflows and trigger/resource limits | Actual execution requires applicable current owner grants |
| Execution | Deadline, retries, output/context budgets and enabled extension hooks | Validated safe bounds; security enforcement is outside prompt text |
| Extensions | Add a versioned external tool/plugin process | B10 capability/credential/process isolation; no arbitrary in-process UI/root hook |

Ship a sensible default rather than a blank builder. First-preview profile
management supports create, clone without credentials/history, select, export,
import, restore and reset. A single active conversational profile is sufficient;
simultaneous multi-agent delegation/gateway management is not a preview requirement.
Existing jobs retain their pinned profile/revision and state when the UI switches.
Never run two writers against one profile store without an explicit lock strategy.

## 3. Planned on-disk convention

Paths below are the intended product layout, not instructions to create host
profiles during planning. Respect XDG equivalents when configured.

```text
~/.config/toddy/profiles/<profile-id>/
  config.json                 # versioned schema; references secret-service IDs only
  SOUL.md                     # editable persona and conversational style
  IDENTITY.md                 # assistant name and presentation preferences
  USER.md                     # explicit stable preferences, with provenance
  AGENTS.md                   # user-selected task instructions; not root policy
  skills/<skill-id>/SKILL.md   # metadata + instructions, loaded when relevant
  skills/<skill-id>/references/
  workflows/                  # validated declarative schedules and actions
~/.local/share/toddy/profiles/<profile-id>/
  state.sqlite                # tasks/history/memory/provenance, versioned schema
  revisions/                  # previous valid non-secret config/skill snapshots
  exports/                    # user-requested exports, no credentials by default
~/.local/state/toddy/profiles/<profile-id>/
  logs/                       # bounded sanitized logs
```

Require valid profile IDs and canonical path containment; reject traversal,
out-of-root symlinks and duplicate/conflicting import paths. Keep per-user access
and logical per-profile isolation. Same-UID profiles are not a security boundary
against arbitrary code owned by that user or an unrestricted root grant. Exports contain config/persona/skills by default;
include memory/history only through an explicit separate choice. No API keys,
secret-service values, root grants, automatic token copying or auto-running imports.
Do not upload personal profiles/memory to the public project repository.

SQLite stores canonical structured memory. USER.md is an editable input whose
changes create versioned preference records. Optional MEMORY.md is an export or
review surface generated from canonical records; do not create two unsynchronized
stores. A future importer can review/adapt external Markdown without copying
credentials or granting imported instructions trust automatically.

## 4. Configuration, precedence and safe application

B01 defines a schema with explicit version, provider/model references, enabled
tool/skill IDs, context/retry/time/cost budgets and workflow declarations. JSON
keeps the initial config dependency small; Markdown skills can follow the usual
metadata/body convention without importing a whole framework.

Resolution order: shipped defaults, explicitly selected user profile, and
explicit per-task options within permitted limits. Show the effective value and
its source. A workspace's AGENTS.md or fetched document is task data by default;
it is not a silently higher-priority owner profile or permission source. The user
can deliberately adopt/review an instruction file into their profile.

Each apply is validate -> show changed effective settings -> save a prior valid
revision -> atomically activate -> report result. Invalid/unsupported settings
leave the current profile working and identify the problematic field/file.
Detect concurrent edits instead of silently overwriting them. Record schema and
revision hash with each task; new persona/tool/model settings apply to new tasks
or an explicit safe boundary, never mutate a running privileged operation.

Model/persona/tool selection and routine limits are editable from the settings UI;
advanced file editing uses the same validator. CLI profile/config validation,
export/import and restore commands use the same service backend. Planned command
names must be frozen in B01 before being advertised as installed tools.

Profile schema migrations are transactional with backup. A broken custom profile
must not block GNOME boot or access to settings: start Toddy in recovery mode with
the last known good profile, tools/automation disabled until reviewed, and a reset
option. Do not silently change provider, spend money or resume jobs on reset.

## 5. Extension and permission boundaries

A skill provides knowledge/instructions, not authority. Only relevant metadata is
included initially; full instructions/resources load on demand within explicit
size/context limits. A selected skill may invoke only tools available to that
task under current policy. No startup script or package installation is run just
because it appears in SKILL.md. Imported bundles require provenance and review;
unknown hooks remain disabled until a separate plugin activation action.

A separate process alone does not isolate credentials. A B10 plugin must have a
verified filesystem/IPC/network boundary, a scrubbed environment and only the
explicitly scoped input/credential access it needs. Probe attempts to read another
profile dummy secret, contact the secret service and send undeclared network data.
If the selected guest cannot enforce containment, leave untrusted code disabled;
do not describe it as isolated merely because it has another PID.

Code extensions run as B10 external plugin/tool processes with declared schemas,
limits, credentials and capability grants. Keep arbitrary user code outside
GNOME Shell, the UI process and the root executor. This still allows advanced
custom harness behavior through versioned hooks rather than patching the OS.
Do not implement a visual workflow builder or an open plugin marketplace for the
first preview.

Executor policy and credential isolation are enforced outside persona/config
text. Editing SOUL.md to say 'ignore permissions', importing a profile or enabling
a tool cannot elevate privileges. The owner may change administrative grants via
the dedicated authenticated policy interface, including full administration as
already required. Clearly disclose unrestricted-root consequences.

## 6. Delivery slices and focused validation

- B01: freeze profile/schema/adapter/skill contracts and one tiny profile fixture.
- B03: provider references and budgets come from the selected validated profile.
- B04: profile selection cannot change executor grants or secret ownership.
- B05: atomic validated revisions, rollback and task revision pinning.
- B06: default profile, basic settings and profile create/select/import/export/reset.
- B07: inspectable per-profile memory, explicit export and deletion.
- B08: profile-scoped workflows with independent standing authorization.
- B10: minimum SKILL.md load-on-demand and one bounded extension/MCP process.
- B13: one integrated S24 check; broader profile/skill ecosystems remain owner use.

S24 is staged to avoid depending on features that do not exist yet. B01 reviews
contracts only. B05/B06 run S24-A (revision/apply/recovery and editable defaults),
B07 runs S24-B (canonical memory/profile isolation), B10 runs S24-C (on-demand
skills/import containment), and B13 combines them. The B06 preview does not claim
B07/B10 functionality; these controls are absent or explicitly pending.

S24 is a small fixture sequence: edit persona/model/tool selection, reject invalid
config without losing the working profile, restore a revision, import/export with
no dummy secret or root grant, check a traversal attempt, switch profile without
memory bleed and verify an imported instruction cannot grant privilege. Record
elapsed time. Do not add hours of ecosystem compatibility testing to the preview.
Test one skill loading only when selected; plugin code still follows S16 isolation.

The first harness will evolve. The goal is a reliable default and safe inexpensive
adjustments, not perfect autonomous behavior on the first release. Use owner
feedback to improve presets/skills in small traceable commits without recompiling
the desktop or resetting user configuration.


## Development harness: release maintenance

The project development agent must update and verify the public landing page for
every published release, following [the release handoff](RELEASES.md). This owner
instruction covers version/download/checksum/scope/limitation copy, translations,
regeneration, checks, commit/push and actual public deployment verification.
It is separate from the installed assistant's user profiles and permissions: do
not bake project publishing tokens or automatic website authority into Toddy OS.
A future user-configured release skill needs that user's explicit repository and
publishing authorization through the normal tool/policy/credential boundaries.
