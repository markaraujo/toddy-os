# Toddy OS — Product Requirements Document

Version: 0.1 · Planning baseline · Owner: Marcos Araujo · Date: 2026-11-05

## 1. Product vision

Build an independent Linux distribution from source following Linux From Scratch (LFS), then add a familiar desktop and an open, provider-independent personal agent. The agent supports development, automation and general computer use through text and voice, can administer the entire installed system under the owner's chosen policy, and can perform proactive maintenance. Toddy OS is named after the owner's Shih-tzu; the approved bespectacled mascot is included in assets/brand/.

The system is built from Linux, GNU and other upstream components, not a newly invented kernel. Ubuntu is a usability reference, not the parent distribution. Omarchy is an experience reference, not the implementation base. The Sagui Linux project inspired the delivery process: requirements, weighted milestone stories, resumable scripts, per-package logs, recorded corrections, VM tests and human hardware validation.

## 2. Confirmed requirements and delivery boundaries

- Publish the source and build process for community use. The owner authorized making this single repository PUBLIC on 2026-11-05 and publishing its dashboard with GitHub Pages. Never commit secrets or personal runtime data.
- All repository content, commits, technical documentation, progress labels and generated product copy are in English. The product supports Portuguese and English interaction.
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

Proposed desktop: GNOME/Wayland for Ubuntu-like familiarity, with a documented X11 fallback if necessary. Validate the build and VM support before committing the desktop ADR. Proposals are explicitly tracked in docs/OPEN-DECISIONS.md; routine selections may be resolved by the implementation agent with evidence, without inventing user approvals.

Logical components:

1. Build/release layer: versioned recipes, source manifests, checksums, package ownership, logs, image assembly and tests.
2. OS layer: kernel, libc, boot, service management, networking, desktop and native package management.
3. Agent service: task state machine, provider adapters, tools, policies, memory and scheduler.
4. Interaction: CLI/TUI, desktop panel and voice input/output.
5. Integration: documented plugin API and MCP adapter; terminal, files, applications and browser adapters.
6. Recovery: rescue boot, configuration backups, checkpoints and explicit restore procedures.

The OS remains bootable and usable if the agent, model service or network fails. llama.cpp supplies inference, not the complete agent harness. An existing open-source harness can be reused behind adapters if H/B evaluation proves it preferable to a small custom core. Do not require a proprietary coding assistant to operate the distribution.

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

## 6. Phase 2 — Desktop and agentic system

### FR-01 Desktop and essential software

Provide graphical login/session, network configuration, browser, terminal, editor, file manager, audio and basic development tools (Git, compiler and supported language runtimes). Preserve normal keyboard/mouse access independent of the agent. Integrate the approved Toddy OS artwork with usable contrast and documented branding paths. Current PNG studies require production size/vector work where appropriate.

### FR-02 First-run setup

Explain model and permission choices; allow API credentials, a local endpoint or deferred setup. Detect CPU, RAM and accelerator availability; recommend compatible models but never download large weights silently. Store keys in an OS secret service or equivalent protected mechanism, never in shell history or plaintext project configuration. A user can finish setup without purchasing any API service.

### FR-03 Provider independence

Define a stable adapter contract for messages, tool calls, streaming, cancellation, token/cost metadata and model capability discovery. Implement explicit provider adapters where wire protocols differ. Test OpenAI-compatible endpoints, OpenRouter, OpenAI, Anthropic and llama.cpp using mocks plus opt-in real tests. A local model must demonstrate actual tool calling before it is advertised as an agent-capable profile. Preserve model-specific context limits and advertise offline capability only for tested local configurations. Never silently send local-only tasks to a remote fallback.

### FR-04 Agent execution

Use a durable task lifecycle: queued, planning, running, waiting, completed, failed, canceled. Each task records intent, selected model, tool actions, results and final verification. Support bounded loops, deadlines, retry limits, subprocess exit tracking, output limits and idempotency keys for side effects. Continue tasks across service restarts without replaying non-idempotent actions. A spoken or typed stop request and a local kill switch must cancel work and revoke new privileged actions.

### FR-05 Full system administration

The owner can grant a full-administration profile spanning files, software, services, network and system configuration. Implement a separate privileged executor with authenticated local IPC, validated structured requests and recorded policy decisions. It must be able to execute the full administrative scope authorized by the owner; ordinary tasks should run with user privileges. The user can authorize a session or standing automation rather than approve every command individually.

External pages, emails, repository files and tool output are untrusted task data, not permission grants. Secret retrieval and outbound transfers must follow the owner's policy. Explain destructive changes before execution where policy requires it, offer dry runs when feasible, and prepare recovery points. Full root authority means local logs are not tamper-proof against that authority; do not promise otherwise. Control interfaces must not be exposed unauthenticated on the network.

### FR-06 Declarative configuration and recovery

Separate persistent desired configuration from one-off operations. Version non-secret configuration changes with origin, previous state and validation result. Reconciliation must report drift and avoid repeatedly fighting deliberate user changes. Verify rollback of representative configuration/package failures in a guest. Backups on the same disk do not count as disaster recovery. Preserve a rescue path if the agent cannot start.

### FR-07 Memory

Use a local canonical store for preferences, tasks, history and provenance; SQLite plus full-text search is the proposed minimum. Store long-lived knowledge separately from transient conversation context. Provide retention, export, deletion, user correction, per-user isolation and consistent backup/restore. Secrets must not become memory or embeddings. Retrieval must cite the source and distinguish facts, suggestions and untrusted documents.

Support a replaceable semantic search adapter. Qdrant is a candidate optional backend for larger document libraries, not a mandatory daemon on every PC. Derived vector indexes must be rebuildable from canonical data and tied to an embedding-model version. Validate relevance, latency, memory use and deletion propagation before selecting a backend. Bind services locally and authenticate remote access. Publish an evaluation dataset and measured results rather than claiming universal fastest/best performance.

### FR-08 Proactive automation

Provide schedules and event triggers for disk usage, service health and user-defined tasks. Use deterministic probes for system metrics; an LLM interprets and plans only when useful. Persist schedules and last outcomes, prevent overlapping duplicate runs, apply backoff and user-defined budgets, and notify on meaningful changes. Silent monitoring must stay quiet when nothing actionable changes. No paid model call is needed to discover that a disk threshold has not changed.

### FR-09 Text and voice

Provide a CLI/TUI as a first-class interface and an accessible desktop entry point. Voice includes speech-to-text, text-to-speech, device selection and clear microphone state. Proposed offline components are whisper.cpp and a separately evaluated open-source TTS engine/voice. Begin with push-to-talk; always-listening mode requires an explicit preference. Test Portuguese and English. Treat transcripts as text input under the same policy; background audio never grants new privileges.

### FR-10 Integrations and plugins

Define versioned plugin manifests, capabilities, input/output schemas, process boundaries, timeouts and installation provenance. Support MCP via a replaceable adapter plus direct native tools. Initial tools cover files, terminal, package manager, services and browser; email/calendar/cloud integrations are optional. Discovering a connector never grants account access. Plugin install/update must not silently inherit administrative policy.

### FR-11 Installation and persistence

First ship a live ISO, then an installer that supports guided installation to a selected virtual/physical target, user creation, locale, time zone, partition plan, bootloader and encrypted-disk option if validated. Calamares is a candidate framework; do not clone Ubuntu's installer blindly. Test actual installation onto a blank virtual disk, remove the live ISO and reboot into the installed system. The installer must show the exact disk plan before destructive operations. Dual boot and Secure Boot are separate future gates unless fully implemented and tested.

### FR-12 Package installation and updates

Decide package ownership before final-system builds. APT/dpkg and .deb are reusable tools/formats, but Ubuntu/Debian binary repositories assume their own dependency versions, filesystem conventions and maintainer scripts. Native compatibility is not guaranteed by installing apt. Default proposal: package our own source-built components and operate a signed project-controlled repository; evaluate feasibility before adoption. Applications may additionally use Flatpak or isolated Debian/Ubuntu developer environments if tested.

Require install, remove, upgrade, configuration preservation, dependency/conflict handling, integrity verification and a tested failed-update recovery path. Do not mix foreign libc/core packages into the host. Publish actual compatibility constraints rather than claiming full Ubuntu package compatibility. The agent invokes the package system; it must not invent untracked system changes as a replacement for it.

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

The development-start instruction authorizes autonomous implementation and dependency installation through H13. Resolve ordinary failures, verify outcomes and regularly commit/push progress without routine milestone approval. After H13/G1, deliver the foundation ISO and evidence, then pause for owner testing and explicit approval before B01-B13, as requested in ADR-0063. The full experimental release requirements remain unchanged; H13 does not complete G2. Concrete external dependencies may still require user action. Session limits are real constraints; preserve restartable state rather than promising uninterrupted execution.

Use one story per milestone with goal, prerequisites, steps, acceptance criteria, evidence and recovery notes. status.json is the progress source of truth. STATUS.md and dashboard/index.html are generated from it. Completed work counts only after evidence exists; unfinished work does not earn arbitrary fractional credit. Phase percentages are calculated separately from bootstrap readiness. No promise of completion time until a baseline build is measured.

Record chronological activity in docs/journal.md and each failure as symptom, cause, correction and verification in docs/errors.md. Record architecture in docs/adr/. Follow commit-sized changes and never commit secrets, whole chats, downloaded third-party source trees, model weights, build disks or ISOs. Release artifacts belong in a release store with checksums, licenses, source notices and component inventory.

## 9. Test and acceptance plan

Foundation: host prereqs, source integrity, package manifests, critical upstream suites, compiler checks, checkpoint recovery and boot matrix.

Agentic: unit tests for deterministic boundaries; provider contract tests; full tasks in a disposable guest; restart/cancel/idempotency; malicious document/tool-output scenarios; memory isolation and deletion; offline execution; notification deduplication; voice transcription/action separation; plugin and privilege revocation.

Installer: guided disk plan, cancel path, install to a blank virtual disk, first boot without ISO, persistence across reboots, failed-update recovery and documented disk-encryption behavior where supported.

Representative end-to-end tasks: prepare a development workspace; diagnose and restart a deliberately broken guest service; install/remove a managed package; persist a theme preference; retrieve a sourced project decision; execute a scheduled disk warning once; interrupt a long task; recover from a bad configuration.

Physical hardware tests record exact CPU, RAM, GPU, storage, network and result. QEMU/KVM is primary; VirtualBox is a compatibility target. Docker can host build/test processes but shares a host kernel, so it does not validate a new kernel, ISO boot, firmware or installer by itself.

## 10. Phase 2 release gate G2

All B stories pass with linked evidence. An installed guest survives multiple reboots with persistent data; agent/provider/voice/memory/automation scenarios pass; stop/revoke and recovery are tested. At least one physical machine has a documented daily-use smoke result, or the release is explicitly labeled VM-only. Publish known issues, source/build instructions, license inventory and hashes. The owner can review and test the first ISO; repository visibility is already public by owner decision. Experimental daily-use is not an enterprise-support or universal-hardware claim.

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
