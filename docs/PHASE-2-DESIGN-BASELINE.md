# Phase 2 — Closed design choices and implementation proof

Date: 2026-11-07. The owner requested that avoidable design decisions be settled
before guest implementation. These defaults close the selection questions; they
are not a claim that packages, models or hardware were tested. No owner product
choice is awaiting an answer. B01 is still responsible for locking compatible
versions/bytes and proving its small spikes before large integration builds.

## Selected baseline

| Area | Selected default | Fallback and proof gate |
| --- | --- | --- |
| Target | x86_64, accepted LFS/BLFS 13.1-systemd foundation, minimal GNOME/Wayland | Same foundation; documented affected security/ABI change only, never a silent distro/core upgrade |
| Native UI | Python 3 + PyGObject, GTK4/Libadwaita | Ordinary activatable window if global placement/shortcut backend is unavailable; no Electron app or Shell fork |
| User service | Python/GIO broker owns SQLite tasks/profiles/policy dispatch, secret-service access and UI state | No second canonical store; native dependencies locked in B01 |
| UI IPC | Asynchronous typed session D-Bus through GIO, task/request IDs and bounded events | CLI uses the same broker; reconnect attaches to existing task, never automatically replays it |
| Engine bridge | Pi Core/Pi AI in a managed Node.js worker using private stdin/stdout framed JSON; diagnostics on sanitized stderr | Freeze schema/runtime/limits in B01; no Node D-Bus addon or unauthenticated command port required |
| Engine execution | Sequential mutation, broker/executor resource locks and current grant checks | Parallel read-only work only after an explicit bounded implementation; upstream defaults do not set OS policy |
| Root service | Small separate Python/GIO system-D-Bus executor, authenticated caller and dedicated owner-policy authorization | No GTK/model imports in root service; no implicit root access from a profile/tool name |
| Model/provider path | Pi provider adapters; local llama.cpp, with Qwen3-1.7B-Q8_0 as the first CPU reference candidate | Official model card lists Apache-2.0 and Q8_0; pin artifact/license/context/resources and prove S05. No automatic model download or remote fallback |
| Local transport | Per-user authenticated local inference, with no privileged network control plane | Bind loopback only if authenticated transport is verified; private process transport otherwise. Never expose a wildcard listener |
| Memory | Per-profile versioned SQLite/FTS5 canonical store, inspectable preferences and source provenance | No mandatory vector database; USER.md is reviewed input, not a second authoritative store |
| STT | whisper.cpp with the multilingual Whisper base profile, push-to-talk | Text remains available; actual EN/PT/model/device proof in B09, no always-listening default |
| TTS | On-demand Piper from OHF-Voice; one licensed PT-BR and English voice profile | eSpeak NG built-in voices if neural runtime/voice terms/resources fail. Both are openly identified; no natural/celebrity-voice promise. Engine/model/voice notices stay separate |
| Installer | Calamares from current Codeberg upstream, project-owned modules/backend | B01 no-write spike first. A concrete blocker gets one documented alternative review, not an improvised destructive installer or skipped GUI acceptance |
| Disk/boot | Blank disposable disks, GPT/ext4, GRUB BIOS/UEFI using the accepted foundation's boot direction | No dual boot/encryption/Secure Boot initially; recheck exact disk identity before mutation and preserve previous boot/rescue |
| Packages | Existing native source-built .deb/dpkg/APT plus signed project repository | No Ubuntu repositories; optional app/driver candidate unavailable unless actual compatibility/license path is verified |
| Plugins | Bubblewrap-built sandbox with explicit filesystem/IPC/network/credential policy; stdio MCP first | If guest user namespaces/capabilities fail, a reviewed separate-UID managed sandbox is the bounded alternative. Unknown code stays disabled until actual denial tests pass |
| Browser MVP | Firefox in an isolated test profile; native launch plus scoped read-only accessibility bridge | Verify chosen GNOME/Firefox accessibility API on one local page; no owner authenticated profile, driver control port or general autonomous website matrix |
| Branding | Current navy environment and exact protected source logo/mascot | Supported GNOME settings, native app styling; no global Libadwaita CSS override |
| Validation | Focused S01-S26 stages, deterministic fixtures plus required real local/guest/install flows | No unchanged full foundation reruns; unresolved safety failure blocks the affected delivery and required G2 acceptance |
| Delivery | Risk-first playbook, one primary slice/writer, committed continuation card | Actual Git/target/job inspection after compaction; no replay based on chat summary or PID alone |

Piper voice candidates are PT-BR faber/medium and EN-US ljspeech/high. Their model
cards describe dataset terms (CC0/public-domain respectively); this alone is not
a blanket legal conclusion about every derived artifact. B09 must record the
actual voice/model distribution terms and hashes. If permission cannot be
established, do not redistribute that voice; the verified eSpeak path keeps basic
speech work possible without waiting on a paid account or mandatory legal click.
Voice likeness is not intended to imitate a person, celebrity or trademarked voice.

The service split reuses Python/GIO already selected for the native desktop,
keeps Pi replaceable and avoids another web runtime/controller. These are
engineering choices, not measured performance claims. The aggregate service/worker
idle measurement still belongs to S01-C; separating processes does not exempt them
from the existing budget.

## What is closed and what still requires work

**Closed:** product architecture, default component families, first test profile,
IPC direction, supported initial disk/boot policy, optional-software policy,
confinement strategy, fallback rules, execution order and validation responsibilities.
No framework/TTS/memory/installer survey or owner preference question is needed to
start the approved B01 inventory/spikes.

**Implementation prerequisites:** exact compatible release/commit/source hashes,
transitive build/license closure and target capability checks in B01. Downloaded
bytes must be verified before extraction. Do not call the moving upstream 1.5.0
metadata a completed lock or fetch/install it blindly. A proved incompatibility
reopens only its affected decision through an ADR; unrelated choices remain fixed.

**Runtime release gates:** actual latency/RAM, successful tool execution, sandbox
denials, audio intelligibility, installed boot/update/recovery and identified
hardware. They stay not-run until measured. Security advisories such as the
existing Expat consumer exposure remain explicit engineering obligations; a
closed design table cannot close a vulnerability or certify a release.

**Execution authorization:** the current planning request does not change
owner_review in status.json. Record an explicit guest-continuation instruction
before any B story starts. Approval is not a substitute for B01 proof either.

## Sources checked

Moving official sources reviewed 2026-11-07; exact selected build inputs are future
B01/B09 records, not silently frozen by these links:

- [PyGObject](https://pygobject.gnome.org/): Python bindings include GTK/GIO and use LGPLv2.1+.
- [Pi Core](https://raw.githubusercontent.com/earendil-works/pi/main/packages/agent/README.md): observed namespace @earendil-works/pi-agent-core; use only the required modules.
- [Qwen model card](https://huggingface.co/Qwen/Qwen3-1.7B-GGUF): official Q8_0 artifact and Apache-2.0 metadata; performance remains unmeasured.
- [Piper](https://github.com/OHF-Voice/piper1-gpl): neural TTS engine with separate voice selection; GPL-3.0 source.
- [PT-BR voice card](https://huggingface.co/rhasspy/piper-voices/raw/main/pt/pt_BR/faber/medium/MODEL_CARD) and [English voice card](https://huggingface.co/rhasspy/piper-voices/raw/main/en/en_US/ljspeech/high/MODEL_CARD): dataset/provenance inputs for later artifact review.
- [eSpeak NG](https://github.com/espeak-ng/espeak-ng): compact formant synthesis; explicitly less natural than recorded-voice systems, usable as a transparent fallback.
- [whisper.cpp](https://github.com/ggml-org/whisper.cpp): source/runtime choice; no model or hardware result claimed.
- [Calamares](https://calamares.io/): official development points to Codeberg.
- [Bubblewrap](https://github.com/containers/bubblewrap): sandbox-construction tool, not a ready-made policy. Modern upstream requires user namespaces; do not assume historical setuid mode exists.
- [Firefox accessibility](https://firefox-source-docs.mozilla.org/accessible/index.html): source documentation to inspect during the selected target bridge spike, not proof that a specific guest API works.
