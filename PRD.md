# Toddy OS — Product Requirements Document

Version: 0.3 · Phase 2 execution reviewed · Owner: Marcos Araujo · Date: 2026-11-07

## 1. Product vision

Build an independent Linux distribution from source following Linux From Scratch (LFS), then add a familiar desktop and an open, provider-independent personal agent. The agent supports development, automation and general computer use through text and voice, can administer the entire installed system under the owner's chosen policy, and can perform proactive maintenance. Toddy OS is named after the owner's Shih-tzu; the approved bespectacled mascot is included in assets/brand/.

The system is built from Linux, GNU and other upstream components, not a newly invented kernel. Ubuntu is a usability reference, not the parent distribution. Omarchy is an experience reference, not the implementation base. The Sagui Linux project inspired the delivery process: requirements, weighted milestone stories, resumable scripts, per-package logs, recorded corrections, VM tests and human hardware validation.

## 2. Confirmed requirements and delivery boundaries

- Publish the source and build process for community use. The owner authorized making this single repository PUBLIC on 2026-11-05 and publishing its dashboard with GitHub Pages. Never commit secrets or personal runtime data.
- Canonical repository documentation, commits and technical evidence are in English. The owner approved a public portal in English, Brazilian Portuguese, Spanish, Simplified Chinese, Japanese and Russian, with browser-language detection and manual selection. The operating system still targets Portuguese and English interaction; portal translations do not expand its runtime/voice acceptance matrix.
- Follow two product phases: (1) a reliable LFS foundation; (2) desktop, agentic capabilities and an installable experimental daily-use release.
- Provide a familiar desktop, terminal-based prompts, basic development tools, automation, voice and a graphical agent entry point.
- Support external providers including OpenRouter, OpenAI and Anthropic, plus local inference through llama.cpp or interchangeable runtimes. Accounts and subscriptions are optional, never a boot dependency.
- Support a genuinely open-source runtime path. External code is allowed when its license is suitable; third-party does not mean proprietary. Model weights, voices and firmware have separate licenses.
- Give the owner's agent full system administration capability. Build revocation, audit and recovery into this power; do not silently replace the requirement with a permanently read-only assistant.
- Use pluggable integrations, persistent memory and user-defined background automation.
- Deliver an ISO first, then a graphical installation experience, and validate on the current machine after VM testing.
- This bootstrap delivers requirements and development infrastructure only. It does not authorize formatting the workstation, installing Toddy OS on it, launching a long build, or spending on hosted resources.

### Development AI autonomy

The owner authorizes the development AI, once implementation starts, to install, update and configure all necessary development/build/test dependencies, including required tools on the host and in the isolated target, using available administrative privileges. Routine project-related installations and reversible unblocking actions do not require repeated approval. The AI must diagnose, resolve, verify, record and continue instead of stopping at a missing package. Examples include QEMU, build tools, compiler prerequisites, image utilities and test dependencies.

Use trusted package/upstream sources, track versions and changes, and keep host provisioning separate from target-system recipes. Actual credentials/permissions still have to exist. Request user action only for a concrete unavailable authorization or credential, legal acceptance, paid resource or destructive action outside the designated target. Preserve physical disks, personal data, unrelated services and the frozen build baseline. This plan update does not itself start provisioning or compilation. See ADR-0003 and AGENTS.md for the execution policy.

## 3. Audience and first-release scope

Primary users are developers, software architects, Linux enthusiasts and local-AI users who accept an experimental release. The first supported target is x86_64 PCs and virtual machines. Broad hardware support is an ongoing program with a published test matrix; no promise to support every machine, GPU, architecture or peripheral at launch.

The daily-use experimental release must support persistent files, networking, a browser, a terminal, an editor, package installation, reboot, updates and recovery. Hardware-specific inference acceleration is optional. API mode must work in a VM without GPU passthrough. ARM64 and additional desktop environments follow later.

## 4. Architecture baseline and open decisions

Implementation baseline: LFS 13.1-systemd and matching BLFS 13.1 systemd edition, as observed on the official versioned pages on 2026-11-05. H01 must verify availability, errata, checksums and host compatibility before freezing the build lock. Never follow a moving stable URL during a build. The older Sagui reference uses 12.4 SysVinit; its scripts are evidence of process, not commands to execute blindly.

Selected product direction: minimal GNOME/Wayland and native GTK4/Libadwaita Toddy UI. Preferred engine: replaceable Pi Agent Core/Pi AI modules behind a per-user service, with a separate privileged executor. Exact versions, compatibility and resource budgets are frozen by B01; a documented fallback requires an actual blocker. See ADR-0105 and docs/PHASE-2-PLAN.md. Do not install OpenClaw or Hermes as the initial assistant.

Logical components:

1. Build/release layer: versioned recipes, source manifests, checksums, package ownership, logs, image assembly and tests.
2. OS layer: kernel, libc, boot, service management, networking, desktop and native package management.
3. Agent service: task state machine, provider adapters, tools, policies, memory and scheduler.
4. Interaction: CLI/TUI, desktop panel and voice input/output.
5. Integration: documented plugin API and MCP adapter; terminal, files, applications and browser adapters.
6. Recovery: rescue boot, configuration backups, checkpoints and explicit restore procedures.

Offline installation provides the usable desktop and a lightweight assistant setup
entry. Agent backend/runtime, privileged executor, models and optional integrations
may be installed later through verified native packages, without reinstalling the
OS; the setup entry must work with those components absent. Optional software
choices are saved after base verification and acquired after installed-user review.
Git remains in base; Docker/OpenCode are optional. A shared catalog supports native
CLI/system packages and qualified per-user Flatpak graphical extras, independently
of the agent; agent recommendations are on request only.

The OS remains bootable and usable if the agent, model service or network fails. llama.cpp supplies inference, not the complete agent harness. The preferred Pi components are reused behind replaceable adapters; Toddy supplies durable tasks, policy, memory and recovery. Do not require a proprietary coding assistant to operate the distribution.

## 5. Phase 1 — Solid LFS foundation

### Outcomes

A source-built x86_64 Linux system and hybrid BIOS/UEFI live ISO, built in a dedicated guest environment. Every installed package has a source/version record, installation manifest and build log. The build resumes from a verified checkpoint; failed steps never become successful markers. Host and guest paths are checked before privileged operations.

### Work sequence

H01 verify the host and choose the build environment; H02 freeze books, source packages, patches and integrity data; H03 establish target directories, build user and package tracking; H04 build the cross-toolchain; H05 build temporary tools; H06 enter chroot and checkpoint; H07 build the final base and critical test suites; H08 configure identity, users, services and basic networking; H09 build the kernel and boot configuration; H10 assemble live root, initramfs and volatile overlay; H11 generate a hybrid ISO and SHA-256; H12 test BIOS/UEFI/USB boot and failure handling; H13 deliver the verified base and handoff report.

Book deviations needed for live media, networking or package tracking must cite their recipe source and be recorded in an ADR. Do not skip all toolchain tests to make an image finish faster. Any known expected upstream test failure must be identified and justified.

### Acceptance gate G1

- Clean build environment recorded, book versions pinned, package integrity verified before extraction.
- Boot and login pass in QEMU for BIOS, UEFI and virtual USB. Capture serial logs and the exact test invocation.
- uname, shell, filesystem, libc-linked program and a compiled C hello-world work in the guest.
- The final compiler and binaries do not depend on temporary toolchain paths or host libraries.
- Checkpoint recovery is demonstrated after one controlled failure; package manifests detect file ownership conflicts.
- ISO, checksum, component manifest, test summary and live-media instructions exist. No credentials are baked into a distributable image.
- A physical-machine result is separately marked passed, failed or pending; VM success never becomes an invented hardware pass.

Phase 2 development begins only after G1 passes and the owner explicitly approves continuation following their H13 testing. The owner requested this review boundary on 2026-11-06 (America/Sao_Paulo); see ADR-0063. Research may happen earlier; implementation must not destabilize an unfinished foundation or start B01-B13 before approval.

## 6. Phase 2 — Minimal desktop and native Toddy assistant

This section replaces the previous Phase 2 draft. The authoritative detailed
execution plan is [PHASE-2-PLAN.md](docs/PHASE-2-PLAN.md); scoped acceptance is
[PHASE-2-VALIDATION.md](docs/PHASE-2-VALIDATION.md). ADR-0105 records the owner's
2026-11-07 revision. Existing H01-H13 acceptance and G1 evidence remain unchanged.

The [execution review](docs/PHASE-2-REVIEW.md) and
[resume playbook](docs/PHASE-2-EXECUTION.md) refine delivery order, staged checks,
IPC/confinement and installed-image closure. They preserve required product scope
and the owner-start boundary; repository checks do not constitute guest acceptance.

### FR-01 Minimal graphical desktop

Deliver GNOME/Wayland, one browser, file manager, terminal, simple editor,
settings, networking/audio and required accessibility components. Ubuntu is a
usability reference, not a binary repository. Keep the application set small;
OpenCode and VS Code are optional installations, with exact packaging/license
status disclosed. The desktop stays usable without Toddy, a key, a model or network.

### FR-02 Installation and first-run choices

Offer API key, local AI and configure-later choices. Detect CPU/RAM/GPU/storage
before model suggestions; downloads require explicit selection and integrity
verification. Store API credentials in the installed user's protected OS secret
service, never live-image state, installer logs or project files. Defer secret
entry to first login. Optional app/model downloads can resume after offline setup.

### FR-03 Replaceable engine and independent providers

Prefer Pi Agent Core/Pi AI after B01 pins compatible versions and licenses. Toddy
owns its engine interface, persona and policy. Support explicit provider adapters
for OpenAI, Anthropic, OpenRouter and compatible endpoints with focused fixture
contracts; disclose live-unverified paths without requiring paid tests. Optional
llama.cpp with one tested licensed local profile must demonstrate a real offline
tool task. No silent cloud fallback, bundled model or proprietary runtime requirement.

### FR-04 Durable tasks and visible control

Persist queued/planning/running/waiting/completed/failed/canceled states, intent,
model, tool actions and verified outcomes. Bound retries, context, output and
deadlines. Reconcile interrupted effects before retry; uncertain outcomes wait for
review. A visible Stop and independent local cancellation path prevent new actions
and terminate or report managed subprocesses. Do not promise reversal of every effect.

### FR-05 Full administration with revocable owner policy

The unprivileged conversational service uses a separate authenticated local
executor for validated administrative tools covering packages, files, services,
network and configuration. The owner can grant session/standing full administration
and revoke future actions. External documents/tools cannot grant authority. Protect
secrets and enforce outbound policy. No unauthenticated network control listener.
Unrestricted root authority cannot promise tamper-proof local logs or universal rollback.

### FR-06 Configuration and recovery

Track non-secret desired configuration separately from one-off actions; record
origin, prior state and postcondition. Report drift without fighting deliberate
user changes. Verify one broken-configuration restoration and preserve a manual
rescue path plus recoverable update/boot checkpoints. Same-disk backups are not
disaster recovery.

### FR-07 Local inspectable memory

Use canonical per-user SQLite/FTS storage for preferences, history, tasks and
sources, with inspection, correction, retention, deletion, export and restore.
Keep secrets out. Retrieval cites provenance and preserves untrusted-data status.
Semantic adapters are a later measured enhancement, not a required vector daemon.

### FR-08 Quiet automation

Persist schedules, event triggers and last results. Deterministic disk/service
checks avoid unnecessary LLM calls. Prevent overlapping/replayed actions; enforce
owner policy, budgets/backoff, disable/stop controls and meaningful-change-only
notifications. Validate one representative automation before expanding coverage.

### FR-09 Toddy quick entry, personality and optional voice

Build native GTK4/Libadwaita quick-entry/main windows plus CLI/TUI. Provide a
conflict-checked configurable shortcut, launcher, conversation/task progress,
history, errors, provider status and Stop. Exact Spotlight-like placement is a
presentation enhancement with ordinary app activation as fallback. Optional
push-to-talk STT/TTS supports Portuguese/English with visible microphone state
and separately evaluated model/voice licenses. No mandatory always-listening.
Toddy is an affectionate, needy, witty nerdy Shih-tzu; humor must not obscure
warnings, permissions, uncertainty or real task outcomes.

### FR-09a User-customizable harness

Provide independent named profiles, editable SOUL.md/IDENTITY.md/USER.md/task
instructions, validated versioned configuration and on-demand SKILL.md bundles
inspired by Hermes/OpenClaw. Users can customize persona, model/provider, enabled
tools, skills, memory, workflows and execution budgets without rebuilding the OS.
Ship a working Toddy default with settings/CLI controls, secret-free import/export,
atomic apply, previous-revision restore and broken-profile recovery. Pin profile
revisions per task. Extensions use isolated versioned plugin processes; imported
instructions/config cannot grant root or bypass credential/Stop policy. See
[the harness contract](docs/PHASE-2-HARNESS.md) and ADR-0106. Full external ecosystem
compatibility and a visual workflow builder are not preview requirements.

### FR-10 Native tools and bounded plugins

Start with native file, shell, package, service and browser integration. Use
versioned manifests/schemas, process/credential boundaries, timeouts and revocable
capabilities. Ship one actual local MCP integration through a replaceable adapter.
Connector discovery or plugin installation grants no account/root access. Email,
calendar and cloud connectors remain optional future extensions.

### FR-11 Guided installer, third-party support and experience previews

Evaluate Calamares first. Show the exact selected disk plan before destructive
operations; implement user/locale/timezone/boot setup, safe cancellation and
persistent blank-virtual-disk installation. Offer optional AI and developer apps,
and explicit compatible third-party firmware/video-driver/software packs with
hardware detection, license/source/size disclosure, exact kernel/ABI guards and
rollback/rescue. Do not enable Ubuntu repositories or silently replace core ABI.
Actual GPU/Wi-Fi support needs hardware evidence; fixture/VM results are labeled.
Encryption, dual boot and Secure Boot remain unsupported until separately verified.

Include an installer slideshow with realistic GNOME/Toddy scenes and short
humorous nerdy-dog copy. Simulated screens are labeled design previews until actual
guest captures replace them. Use coherent navy assets, preserve exact approved
logo/mascot and keep progress/errors/disk warnings unobscured. No advertised feature
may appear implemented solely because it is pictured in a design preview.

### FR-12 Packages, updates and experimental owner delivery

Extend the already selected native source-built .deb/dpkg/APT strategy and signed
project repository. Verify representative install/remove/upgrade, config
preservation, signature/conflict rejection and failed-update recovery. Review
third-party applications/drivers separately; .deb format does not establish Ubuntu
compatibility. Deliver small working commits and interim owner previews, then a
basic-tested installed ISO under G2 with explicit deferred owner-use validation.

## 7. Nonfunctional requirements

- Reliability: task state survives agent-service restarts; no duplicate side effects; boot works without inference.
- Security: explicit trust boundaries, protected credentials, local-first data, authenticated control, user isolation and prompt-injection regression scenarios.
- Performance: capture boot time, idle RAM/CPU, tool latency, retrieval latency and inference measurements on identified hardware. B01 establishes numeric budgets and test loads; release requires no unexplained regression above the recorded tolerance.
- Portability: no hardcoded author home directory or machine-specific CPU compilation flags in release recipes. Record supported CPU baseline and optional acceleration profiles.
- Rebuildability: versioned recipes, source hashes, build environment and artifact manifest; first aim for a repeatable successful build. Do not claim byte-for-byte reproducibility until separately measured.
- Accessibility: keyboard navigation, scalable text, visible focus, screen-reader feasibility and readable voice-state controls.
- Privacy: no mandatory telemetry, no hidden cloud fallback, inspectable memory and outbound provider policy.
- Maintainability: a clean checkout documents exact setup and next task; decisions and failures are searchable; components have explicit update ownership.

## 8. Development and release workflow

The development-start instruction authorizes autonomous implementation and dependency installation through H13. Resolve ordinary failures, verify outcomes and regularly commit/push progress without routine milestone approval. After H13/G1, deliver the foundation ISO and evidence, then pause for owner testing and explicit approval before B01-B13, as requested in ADR-0063. Phase 2 requirements and basic-preview acceptance are revised by ADR-0105; H13 does not complete G2. The current owner request authorizes replanning and repository navy brand/UI/page work, not guest provisioning or a claim of completed hardware testing. Concrete external dependencies may still require user action. Session limits are real constraints; preserve restartable state rather than promising uninterrupted execution.

Use one story per milestone with goal, prerequisites, steps, acceptance criteria, evidence and recovery notes. status.json is the progress source of truth. STATUS.md and dashboard/index.html are generated from it. Completed work counts only after evidence exists; unfinished work does not earn arbitrary fractional credit. Phase percentages are calculated separately from bootstrap readiness. No promise of completion time until a baseline build is measured. Prefer small independently reviewable delivery slices and bounded focused checks; do not wait for a full B story to commit a working boundary.

Record chronological activity in docs/journal.md and each failure as symptom, cause, correction and verification in docs/errors.md. Record architecture in docs/adr/. Follow commit-sized changes and never commit secrets, whole chats, downloaded third-party source trees, model weights, build disks or ISOs. Release artifacts belong in a release store with checksums, licenses, source notices and component inventory.

## 9. Focused test and acceptance plan

Foundation evidence is accepted and preserved. Do not repeat unchanged full
compiler/libc or other long upstream suites for Phase 2 work. Changing core
components requires a documented selection of affected regressions.

The owner explicitly requested basic working checks before delivery and broader
validation during personal use. Follow [PHASE-2-VALIDATION.md](docs/PHASE-2-VALIDATION.md):
one reference guest, short scoped fixtures and representative real flows; measure
test durations and diagnose timeouts before retry. No broad hardware/provider
matrix, long soak or exhaustive suite is a preview prerequisite. Boot/install,
secret/privilege boundaries, Stop/revoke, restart safety, local-only egress and
representative recovery remain mandatory for affected advertised capabilities.

Make every small working boundary independently committable, with commands,
results, checkpoint and next action. Basic checks do not guarantee absence of
failures. Deferred/not-run tests stay explicit; owner feedback drives targeted
follow-up regressions. No expensive OS build belongs in repository bootstrap CI.

## 10. Phase 2 experimental owner-preview gate G2

Every B story passes its revised scoped acceptance with linked evidence. The
exact image installs to a blank virtual disk, boots without ISO twice, preserves
data and passes the focused mandatory matrix. Publish hashes, source/build/license
inventory, recovery and owner-use instructions, known issues and live-tested versus
fixture-only capabilities. Label VM-only until actual identified hardware passes.

G2 now means a basic-tested experimental owner preview, not exhaustive daily-use
qualification. Broader GPU/Wi-Fi, suspend/resume, models, accessibility and long soak
remain a visible owner-use backlog. Never convert deferred coverage or a critical
failure to passed. No paid provider or broad physical matrix is required to hand
over the preview; unsupported advanced installer/boot features are explicit.

## 11. Risks and responses

| Risk | Response |
| --- | --- |
| Independent distro maintenance exceeds image creation | Package ownership, update/rebuild recipes, security advisories and release ownership are first-class work. |
| Full-power agent damages the system | Guest-first tests, explicit policy, cancellable executor, recovery checkpoints and documented limits. |
| Model tool use varies | Capability profiles, contract tests and a tested baseline model per mode. |
| Closed firmware needed on target hardware | Separate optional hardware packs and disclose licenses; decide policy before distribution. |
| GNOME/installer scope expands | Time-box feasibility work; record fallback and tradeoffs in an ADR without changing product intent silently. |
| Local GPU unavailable in VM | Test providers via API or a protected host endpoint; validate acceleration on actual hardware later. |
| Borrowed package repositories break core dependencies | Own packages or isolated foreign environments; no unmanaged core replacement. |
| Artwork lacks production sizes | Preserve approved originals; derive reviewed vector/small-icon/production exports in B11. |

## 12. Out of scope for the first release

A new kernel from scratch; compatibility with every device; ARM64; enterprise support; a proprietary service requirement; autonomous irreversible host-disk installation; an app marketplace business; guaranteed support for every MCP server or model; mandatory always-on microphone; guaranteed byte-identical builds; untested dual boot or signed Secure Boot.

## 13. Decision register and sources

Confirmed decisions are captured in ADR-0001 and the user requirements above. Technical proposals and feasibility work are in docs/OPEN-DECISIONS.md. Canonical sources and exact consulted versions are in docs/references.md. H01 checks the selected versioned candidate; H02 freezes downloaded inputs. Every build story after H02 must consult the frozen relevant book section before writing/executing recipes.


### Current Berkeley DB delivery validation (2026-11-07)

The owner explicitly approved focused Berkeley DB validation for this experimental
delivery. ADR-0092 supersedes earlier instructions requiring the complete standard
Tcl suite before production. Preserve the cancelled and failed full runs as such;
require native C tests, production transaction/reopen/rollback/crash recovery,
actual APT cache interruption/rebuild and existing signed-repository/HTTPS/package
checks before H07 acceptance. All other critical suites and H13/G1 gates remain.
See [ADR-0092](docs/adr/0092-focused-berkeley-delivery-validation.md).
