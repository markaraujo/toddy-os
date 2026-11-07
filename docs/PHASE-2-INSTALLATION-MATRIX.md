# Phase 2 — Installation choices and offline behavior

Date: 2026-11-07. Selected behavior, not available packages. Machine-readable
[options](../config/phase2/install-options.json) use stable choice IDs; actual
versions, sizes, license terms and hardware compatibility must come from the
verified package/artifact catalog, never hard-coded promotional claims.

The installer is deterministic native software. It does not use an LLM to decide
partitions, execute installation steps or work offline. Optional assistant setup
is a separate software choice; absent connectivity never creates an AI requirement.

## Default installation

Minimal GNOME/Wayland, Firefox, files, terminal, simple editor, settings, essential
network/audio/accessibility, native packaging/recovery and a lightweight Toddy
setup/entry surface. Offline base does not require Flatpak or the agent broker/Pi/Node,
executor, inference engines, models, speech or plugins. Install these later through
verified native packages after explicit setup, without reinstalling the OS.
Keep the accepted foundation tools; avoid the full GNOME app collection. The
setup entry opens without the agent backend/credentials/model and explains what
is missing; it does not advertise working agent tasks. Default AI selection
is **later**. No provider contact, spending, recording or model download on boot.
Offer speech/accessibility setup without assuming a neural model is installed.
No office/games/extra browsers/IDEs/model weights in the base image.

| Choice | Default and dependency | Offline/interruption behavior | Evidence before offering Install |
| --- | --- | --- | --- |
| Configure later | Selected | Base installs and works without AI | B02/B06 desktop/setup proof |
| Agent backend | Off offline; explicit setup installs broker/worker/executor closure | Deferred until connectivity or an explicitly verified complete media pack | Native package ownership, authorization and basic task proof |
| External provider | Off; mutually exclusive initial AI setup choice | Save non-secret intention; collect key only in the installed user's protected store | Tested adapter, endpoint validation and locked/unavailable-keyring failure |
| Local AI engine | Off; capability/resource assessment first | Use explicit verified media pack or defer download; no fake ready state | Source/license/hash/runtime profile and authenticated local transport |
| Local model | Off; requires compatible local engine and explicit separate consent | Show size/terms/space before download; resume, verify bytes, then enable | Exact artifact license/hash/context/resource measurement |
| Docker Engine + Compose | Off; native rootless qualification target | Save choice; install only after installed-user review | Engine/Compose, authorization, startup/removal and resource proof |
| OpenCode | Off; independent of AI choice | Defer unavailable downloads; no base-install failure | Supported native install/launch/remove and terms/source closure |
| VS Code | Off; independent choice | Same; do not silently replace with Code - OSS or VSCodium | Exact distribution/marketplace terms and compatible package path |
| Firmware | Off; explicitly select applicable reviewed pack | Verified media pack if distributable, otherwise defer with honest networking warning | Device IDs, redistribution and actual package compatibility |
| Proprietary GPU | Off; only matching supported candidate selectable | Keep working open/text rescue, defer optional download | Exact kernel ABI/license/rollback; detection alone is not hardware proof |
| Codecs/other third-party software | Off; separate selection | Defer; no opaque omnibus acceptance checkbox | Review distribution/patent/license scope where applicable |
| Speech | Off; text always available | Engine/model/voice acquisition may be deferred independently | B09 actual supported EN/PT engine/audio/license checks |

Source-built native .deb/APT remains the package route. Do not enable Ubuntu or
Debian repositories, run unverified vendor scripts or replace libc to satisfy a
checkbox. Unsupported candidates are unavailable with a reason, never selectable
with an optimistic installation promise. Hardware fixtures remain labeled.

## State and consent

Choice availability: unavailable -> available -> selected. Execution:
selected -> installing -> installed, deferred or failed. A failed optional choice
can be explicitly retried after diagnosis; it never becomes installed because the
base finished. Only verified package/artifact postconditions earn installed.
Derived model/driver dependencies are shown in the summary, not silently selected.
Changing AI choice removes incompatible pending intent after confirmation without
removing already installed user software or deleting a model.

Separate disk confirmation, third-party terms, model download consent and eventual
provider spending. Default unchecked boxes cannot create standing administrative
grants. Installer contains no API key entry. Credential entry is in the installed
account after protected secret-store availability is established.

Preflight base media integrity, writable target identity, actual required space
and firmware boot scope before the final disk review. Ordinary extra-app packs
are checked later in the installed user session; essential hardware packs retain
their separate installation preflight. Required base failure is a failed installation with recovery, not a usable
completion screen. Network loss on optional downloads preserves a successful base
and records pending choices. Never auto-restart until the user chooses it.

## One persisted handoff

Use one atomic schema-versioned pending-choice manifest, owned by the installed
user, mode 0600, under `$XDG_STATE_HOME/toddy/setup/pending.json`. Fields: installation
ID, schema version, catalog revision, choice IDs, exact intended artifact IDs when
known, state, sanitized error code and explicit consent receipts. No keys, tokens,
passwords, transcripts, grants, root actions or raw download URLs with credentials.
Pre-user installer state stays in a private target staging location and transfers
only after actual UID/home ownership is known. Remove live-only staging.

The first-run UI revalidates catalog/artifact/compatibility and consent before
acquisition. The manifest is intent, never authority to install packages or spend.
Use the shared package/download backend and transaction IDs; deduplicate on the
actual verified transaction, not a UI click. A changed artifact/terms/price requires
new review. Declining optional setup leaves the base usable and the intent editable.

B01 locks candidate feasibility/catalog requirements. B11 prepares art; B12 joins
real backend, choice handoff and [visual sequence](../assets/brand/installer/README.md).
S18-S22/S26 prove disk/install/package/recovery behavior. No build/download or
working installer is claimed by this preparation.

## Shared optional software catalog

Follow [the shared catalog contract](PHASE-2-SOFTWARE-CATALOG.md). Git stays in
base; Docker/OpenCode are highlighted optional choices and mise is excluded.
After verifying base installation, save unselected-by-default optional app choices;
review/acquire them in the installed user's session, not the live installer.
The same agent-independent setup/controller serves user-requested agent suggestions.
Native packages handle core/CLI tools; qualified graphical extras may use per-user
Flatpak. Candidate breadth is not a new G2 gate. Keep hardware/firmware, models,
credentials and grants in their separate existing flows. No guest-start approval.
