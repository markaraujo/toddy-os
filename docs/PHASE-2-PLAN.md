# Phase 2 — Toddy desktop and personal assistant

Revision: 2026-11-07. Owner-approved product direction; implementation candidates
remain subject to B01 verification. See [ADR-0105](adr/0105-toddy-assistant-and-owner-preview.md).
This document refines [PRD.md](../PRD.md); milestone state remains authoritative
in [status.json](../status.json). No application or guest build is implied by a
planning change or an artwork preview.

## 1. Product outcome and scope

Ship an experimental, installable x86_64 desktop with Ubuntu-like everyday
usability and a deliberately small application set. Toddy is the device user's
personal assistant: recognizable mascot, concise helpful personality, Portuguese
and English, text first and optional speech. OpenClaw, Hermes and Siri/Jarvis are
experience references, not bundled implementations or claims of equivalent capability.

Default applications: one browser (Firefox preferred, subject to pinned BLFS
integration), file manager, terminal, simple text editor, settings, network/audio
controls and essential accessibility/runtime components. Do not install the full
GNOME application collection, office suite, games, multiple browsers, developer
IDEs or model weights by default. Keep underlying required dependencies explicit.
Retain the existing compiler/package foundation; no unnecessary rebuild or removal.

Offer OpenCode and VS Code as optional development applications. VS Code upstream
binary branding, marketplace and distribution terms must be distinguished from
Code - OSS/VSCodium; do not substitute silently. Verify a supported package path
and its removal/update behavior before presenting a working install option.

The OS must boot, browse files and use its desktop with no API key, no downloaded
model, no network, or the Toddy/inference services stopped. Network-dependent
browser requests may fail normally while the desktop stays usable.

## 2. Architecture and ownership

| Component | Initial direction | Responsibility and boundary |
| --- | --- | --- |
| Desktop | GNOME/Wayland | Familiar session, supported settings, minimal extensions; no shell fork |
| Toddy UI | GTK4/Libadwaita native application | Quick entry, conversations, tasks, history, settings and stop; no required Electron/web server |
| Agent engine | Pi Agent Core + Pi AI, provisional | Provider adapters, model/tool loop and streaming; wrap behind a replaceable internal interface |
| Toddy service | Unprivileged per-user service | Personality, durable jobs, bounded context, routing, memory and schedules |
| Privileged executor | Separate small authenticated local service | Owner policy, structured operations, argument validation, revocation and audit |
| Local inference | llama.cpp first | Optional model process; hardware-specific profiles; unload/idle policy |
| Memory | SQLite + FTS5 | Canonical per-user preferences/history/task provenance; no mandatory vector daemon |
| Speech | whisper.cpp candidate plus separately licensed TTS | Optional on-demand input/output; no always-listening default |
| Integration | Native tools first, replaceable MCP adapter | File/package/service tools; optional connectors with separate credentials |

B01 must pin exact upstream commits/releases, transitive dependencies, license
inventory and supported target runtime. The Pi repository/package namespace has
changed; resolve actual package names from the selected source rather than copying
old examples. Reuse only required modules. Pi's in-memory state/abort support is
not a durable job store, privilege boundary or exactly-once execution guarantee.
No mandatory Vercel, paid gateway, proprietary assistant, OpenClaw or Hermes install.

Use authenticated local IPC with peer identity and per-user access control. Do
not open a network control listener for the first release. Separate UI/engine
interfaces so a future engine replacement does not replace policy or stored data.
Use OS-supported session activation and an independently protected executor.

## 2.1 User-customizable harness

The assistant harness is user-customizable from its first usable preview, following
Hermes/OpenClaw profile, persona-file and on-demand skill patterns. Read the full
[PHASE-2-HARNESS.md](PHASE-2-HARNESS.md) contract: editable persona/instructions,
provider/tool selection, per-profile memory/workflows, budgets, validated config,
secret-free import/export, revisions, rollback and recovery mode. Customization
must not grant privileges or inject arbitrary code into GNOME/the root executor.
B01 freezes these contracts before the UI/service schemas harden. This is a core
requirement, not a cosmetic future settings panel.

## 3. User experience

### 3.1 Quick access and main application

Register a configurable shortcut; propose Super+Space only after checking conflicts
with keyboard/input-method bindings. Open a compact native Toddy window with text
entry, microphone button and current provider/local status. Escape closes the entry
surface; it does not silently cancel an existing job. A visible Stop action cancels
work. The main window exposes conversation, task progress, history and settings.

First implement an ordinary activatable compact window. Exact Spotlight-like
placement, focus and overlay behavior are subject to Wayland/GNOME verification.
If required, add one small version-pinned Shell extension for presentation only;
never put model calls, secrets or privileged execution inside the shell process.
A shortcut opening the regular app is the documented fallback. A launcher and
keyboard-accessible entry must always work without an extension.

Show actual states: queued, planning, running, waiting, completed, failed,
canceled; model loading, microphone recording, network failure and missing setup.
Do not show success until tool postconditions pass. Explain what changed and any
incomplete step. The Toddy persona must not obscure warnings or invent actions.

### 3.2 Setup, installer and optional software

The installer offers three assistant choices: use my provider key, configure local
AI, or configure later. Prefer collecting API keys in the installed user's first
session, never in shared live-image configuration or installer logs. If setup is
requested in the installer, persist only a non-secret choice and defer credential
entry to the installed account. Detect CPU/RAM/GPU/free space before suggesting a
local profile. Show model size, license, download and runtime requirements before
consent; interrupted downloads resume with integrity verification before use.

llama.cpp is an inference runtime; a Llama-family model is a separate choice, not
a mandatory download. Offer another local endpoint through a compatible adapter;
additional managed runtimes such as Ollama are follow-up candidates, not required
for the first preview. Local-only mode must never switch to an API silently.

Optional application choices include OpenCode and VS Code, independently selectable.
A deferred network download must be labeled pending, resumable after first boot,
and must not make an otherwise valid base installation fail. Reuse the same
package/download backend in the installer and first-run UI. Offline installation
must remain possible; never label an untested optional package as supported.

### 3.3 Third-party drivers, firmware and packages

Provide an explicit installer page similar in purpose to Ubuntu's optional
third-party software choice. Detect PCI/USB hardware IDs and distinguish the
currently bound driver from candidate support. Present separate choices for:

- Redistributable firmware needed for detected Wi-Fi, graphics or other devices.
- Optional proprietary GPU drivers, when an exact compatible and licensed package
  exists; NVIDIA is an evaluation target, not a universal support claim.
- Optional third-party applications/codecs, only where distribution is permitted.

Show source, license, purpose, download size, required reboot and support status.
Do not equate detection with a tested driver. Use trusted upstream/project package
sources, pinned versions, verified integrity/signatures and project-owned package
manifests. An Ubuntu .deb may have incompatible ABI, dependencies or maintainer
scripts; never enable Ubuntu/Debian repositories or replace core libc to satisfy it.

Keep open core and optional restricted packs separate. Do not redistribute a pack
whose license disallows it; use a reviewed user-initiated upstream installation
path where lawful, or mark unavailable with an explanation. Mandatory click-through
terms cannot be silently accepted. No license acceptance is requested merely to
write or test the installer with fixtures.

For external kernel modules, bind the package to the exact kernel/ABI, rebuild or
block incompatible kernel updates, and retain a previous bootable entry. Verify
initramfs/module dependencies, display-manager start and a text/rescue rollback.
Secure Boot signing/enrollment is unsupported unless separately implemented and
verified. Do not weaken global security or promise signed drivers by default.

VM testing verifies the selection UI, compatibility guards, package transaction,
deferred/offline behavior and rollback with fixtures. Actual GPU acceleration and
Wi-Fi firmware require identified hardware evidence. Show unverified choices as
experimental/unavailable; never offer a nonfunctional default or claim VM tests
prove physical support. First delivery may use an open graphics fallback.

## 4. Security and task behavior

The user can grant a full-administration profile by session or standing policy.
The conversational process runs without root; the separate executor checks every
request against current policy, authenticated identity, tool schema and target.
Grant scope, expiry and revocation are visible. Do not reduce the requirement to a
permanently read-only agent or prompt for every command after a standing grant.

Route privileged actions through the executor. An unrestricted root shell, when
explicitly authorized by the owner profile, remains full authority and must be
clearly identified; arbitrary root shell access cannot coexist with a guarantee
that every possible side effect is constrained or reversible. Local root can
alter local logs. Revocation blocks new actions, terminates managed processes
where feasible, and reports effects already committed or still in progress.

External pages, repository instructions, documents and tool output cannot grant
permissions or authorize sending secrets. Keep credentials in the OS secret
service, out of prompts, logs, memory and exports. Enforce data egress according to
owner policy. No silent telemetry or cloud fallback. Lock down plugins separately.

Persist task intent, selected provider/model, policy reference, operation IDs,
results and verification. Use bounded retries, timeouts and output/context limits.
On restart, reconcile an interrupted side effect using its postcondition before
retrying; mark an uncertain operation for review instead of replaying blindly.
Stop prevents further dispatch independently of LLM cooperation. Preserve a manual
rescue path and bounded configuration backups before system changes.

## 5. Performance policy

These are provisional engineering targets, not measured claims. B01 records an
identified reference guest and freezes feasible budgets before claiming support.
Start with a 4-vCPU/8-GiB QEMU/KVM guest with no GPU passthrough; physical hardware
has its own baseline. Keep build time separate from runtime measurements.

| Measurement | Initial target and measurement |
| --- | --- |
| Desktop cold boot to login | <=45 seconds on the reference guest, excluding model loads |
| Desktop idle memory | <=2 GiB used after settling, no model/voice weights loaded; record method/cache accounting |
| Toddy service idle | <=250 MiB RSS and <=1% of one CPU core averaged over 60 seconds after settling |
| Warm quick-entry activation | <=300 ms to visible, focused text entry; measure cold launch separately |
| Deterministic simple tool | <=1 second excluding network, package work and inference |
| Local memory lookup | <=200 ms on a fixed 1,000-record text fixture; report fixture and query |
| Model and voice | Report load/first-token/transcription latency and peak RAM for the tested profile; no universal target |

Inspect unexpected regressions once, fix the cause or record a justified budget
revision with evidence. Do not add elaborate benchmarking infrastructure or chase
micro-optimizations before the basic flow works. Models/voice load on demand with
an explicit keep-warm preference; the tradeoff between memory and first response
must be visible. Load only the tools and bounded memory relevant to a task.

## 6. Delivery sequence and milestone handoffs

Keep B01-B13 IDs and weights; do not create false completion credit for planning.
Dependencies in status.json are mandatory, not a requirement to bundle every
optional feature into one first preview.

1. B01: feasibility spike, pinned engine/UI/provider contract, minimal package set,
   license/driver policy and measured resource baseline. Reject a candidate only
   for a documented blocker, compare one suitable alternative, and avoid an
   open-ended framework survey.
2. B02: graphical login, basic applications and normal use without AI. Preserve a
   working guest checkpoint before optional drivers or desktop customization.
3. B03-B05: provider contracts, one working local profile, executor and durable
   tasks. Text/API development is first; local inference must pass before local
   agent capability is advertised. Retain a deterministic provider fixture for CI.
4. B06: native Toddy entry/main UI, CLI/TUI, protected first-run setup and three
   setup paths. Produce the first text-assistant owner preview after the critical
   applicable smoke tests pass; this is an interim snapshot, not G2.
5. B07-B08: inspectable local memory and one quiet deterministic automation.
6. B09-B10: push-to-talk speech and one end-to-end plugin/MCP integration. Keep
   both optional to use; never make voice or a connector necessary for boot.
7. B11 (after B02/B06): integrate the navy brand into the actual guest. Repository artwork and UI
   previews may be prepared earlier; they do not complete runtime integration.
8. B12: guided installer, optional apps/AI/third-party choices, blank-disk install,
   persistence, one supported update/recovery path and a rescue route.
9. B13: run the focused installed-image checklist, publish an experimental owner
   preview ISO/checksums/build/license inventory and a concise owner validation
   guide. State VM-only until physical testing actually occurs.

Optional app packaging can be prepared in B02; installer integration is B12.
B12 depends on B03/B06 as well as B02/B11 so its choices use verified backends.
B13 depends on every remaining B milestone so no package is omitted accidentally.

## 7. Basic testing, time control and owner validation

Tests take real time. The owner's priority is a working experimental delivery
with focused developer checks and broader validation during personal use. Follow
[PHASE-2-VALIDATION.md](PHASE-2-VALIDATION.md): one reference VM, representative
happy paths plus a few essential failure cases. Do not repeat accepted compiler,
libc or full upstream desktop suites for unchanged foundation inputs. If a core
component changes, select affected checks and document why they are necessary.

Unresolved disk-target safety, leaked secrets, unauthorized privilege use, broken
boot/install, duplicate destructive action, ineffective Stop/revoke or silent
local-to-cloud transfer blocks the affected release capability. Performance and
hardware unknowns must be labeled; tests never become passed by timeout or owner
handoff. Deferred coverage is recorded as deferred, not evidence of acceptance.

Owner usage covers broader GPU/Wi-Fi/audio/device matrices, suspend/resume, longer
conversations, model variety, multi-monitor, accessibility depth and daily-use
soak. Clearly disclose basic-tested versus untested functions. The owner can
report a reproducible issue; add a targeted regression only when it protects
meaningful behavior. No assertion that basic tests guarantee absence of failures.

## 8. Brand and UI direction

Preserve the exact approved logo and transparent mascot. Navy replaces beige/brown
as the environment's predominant color, not the dog's natural colors or the logo
pixels. Use midnight/navy surfaces, restrained clear-blue accents and cool light
surfaces. Preserve accessible focus, contrast, high-contrast mode and status colors.

Update wallpapers, boot/login background, UI tokens and dashboard coherently.
Keep original assets/provenance archived and record generated dimensions honestly.
The Toddy app and a static UI design preview may use the full palette; avoid global
CSS hacks that break unrelated Libadwaita apps. Dark/light preference must work.
Brand work does not rebuild or change the already published foundation ISO.

## 8.1 Installer storytelling and realistic scenes

The installer slideshow sells the intended experience while actual installation
progress remains visible. Use short cards: minimal GNOME desktop, quick Toddy
entry, a real task/progress view, optional local/API setup and optional development
tools. Show third-party choices in the setup UI, not as a promise of universal GPU
support. Keep scene duration independent of installation work; never delay install
to finish a presentation. Respect reduced motion; no background video is required.

Toddy's voice is an adult bespectacled Shih-tzu: clever, affectionate, a little
needy and amused by his own technical competence. Sample English product copy:
"I watch your processes. You watch my snack bowl.", "Less bloat. More room for
belly rubs.", "Local brain or cloud brain. Still your dog.", and "Dependencies
resolved. Attention requirements remain high." Avoid childish barking in every
message, unverified speed claims or jokes inside destructive confirmations.
Localize the meaning naturally for Portuguese in the runtime UI.

Scenes must use GNOME-like top bar, window chrome and actual planned components,
consistent navy tokens and the unchanged original mascot. No invented macOS or
Windows screen presented as GNOME. Repository concept images are explicitly
labeled "Design preview — not a running build". Replace with real screenshots
as soon as the corresponding guest feature works; retain provenance. A mockup
never counts as a desktop/installer/agent test. Prepare initial static UI scenes
as part of the brand refresh without scaffolding the application itself.

## 8.2 Small traceable delivery policy

One commit should express a coherent behavior, dependency or correction. Prefer
slices such as "graphical login works", "browser launches", "Toddy entry opens",
"fixture streams text", and "Stop blocks queued action" over a single entire
B02/B06 change. Include the observed result and next action in the story/journal.
The B milestone earns its weighted points only when all scoped acceptance passes.

Target basic per-slice checks in minutes. These are planning expectations, not a
guarantee: investigate an unexpectedly long check rather than expanding the suite.
A foreground check expected to exceed 10 minutes needs a reason, progress/log path
and a checkpoint before launch; this is a documentation rule, not a permission
prompt. Build/download jobs may take longer and should be resumable and monitored.
Do not install a new test stack or rerun broad accepted suites for cosmetic edits.

## 9. Required evidence and handoff

Each story records exact input versions, commands, exit status, observed
postconditions, one recovery note and applicable smoke IDs. Keep large logs and
model weights outside Git. Record elapsed test time where available; an estimate
is never an observed duration. Evidence tables use passed/failed/deferred/not-run.

At each boundary save checkpoint identity, next command, outstanding blocker and
log path. Regenerate status/dashboard, run make check for repository changes, and
commit/push validated changes through the authorized workflow. No new workstation
RAG registration. No new test service, framework or paid resource solely to manage
this plan. New untrusted XML consumers retain the existing bounds-review obligation.

Current authorization: plan revision and repository branding/UI design preparation.
Guest development is not started by these edits. B01-B13 remain not_started until
explicit implementation continuation; no claim that the owner already completed
foundation hardware testing. The owner can authorize that continuation separately.
