# Phase 2 — Shared software selection and recommendations

Date: 2026-11-07. Accepted preparation, not installed software or new guest-start
approval. The catalog remains open; candidates are not availability promises.
[software-catalog.json](../config/phase2/software-catalog.json) contains 28 named
candidates, six categories and EN/PT descriptions. No release is qualified yet.

## One flow, independent of the agent

After base installation has been verified, show optional software selection with
nothing checked. Git remains a base requirement and is not reinstallable through
an extra-software checkbox. Docker and OpenCode are highlighted optional choices;
mise is excluded. Keep the existing OpenCode/VS Code IDs. Category shortcuts only
select visible eligible items after review; no hidden bundles or dependencies.

Save choice IDs in the existing private versioned pending manifest, then let the
user finish/restart. No extra-app download or installation runs in the live
installer. At first login, show one dismissible setup invitation; never reopen it
every login after dismissal. A launcher/settings entry remains available. Read
catalog and package state without loading Pi/Node/model/executor. Review selection,
actual availability, source, terms, permissions, download/installed size and disk
space before confirmation. Unknown size is shown as unknown and resolved before
dispatch, not invented. The native backend's ordinary authorization path acquires
missing components; it cannot depend on the absent Toddy executor.

Offline choices remain pending. Explicit verified local package packs may satisfy
them after installed-user review. Pending state is intent, never standing consent
or authority. Revalidate changed catalog/artifact/permissions/terms; ask again for
material changes. Network failures do not damage a completed base. Retrying uses
actual transaction identity/postconditions and cannot duplicate installs. Removal
is explicit and preserves user data by default; no whole-system rollback promise.

Drivers/firmware required for boot/connectivity keep the existing hardware flow.
Model weights, provider keys, privileged grants and voice assets retain separate
consent/validation. Do not defer essential networking firmware simply because
ordinary applications now install after reboot.

## Catalog contract and qualification

Separate curated candidates from qualified release records. Candidate fields name
the app/category/purpose/project and intended backend/channel; null artifact,
origin/license/permission review and empty evidence mean unavailable for install.
A priority flag never changes that. Preserve stable IDs when wording changes.

Before publishing a qualified record, bind app ID to one backend and actual origin,
architecture, stable version, dependency closure, integrity, license/source notices,
permissions, acquisition sizes and evidence. Native entries bind owned package
names/versions and project repository trust; Flatpak entries bind exact application
ID, configured remote identity, branch and commit. Do not guess Flathub IDs or
publish package URLs merely because a project offers an Ubuntu .deb. Project links
are information, not an executable command source. No remote shell installers.

Use project-controlled authenticated catalog metadata through the verified release
route; reject untrusted/tampered metadata. Flatpak transport verifies its own remote
artifacts. A verified publisher badge identifies a publisher, not a blanket safety
approval. Existing core packages/runtimes cannot be replaced by developer tool
selection. Changing a release record does not silently upgrade installed apps.
LTS applies to developer Node candidates; no mise/bootstrap of global environments.

Reuse existing selection states and the pending manifest. Installed state is
observed from the selected backend and actual launch/postconditions, not inferred
from the manifest. An already installed matching app is not reinstalled. An app
installed from another origin is disclosed; no silent migration/duplicate copy.
Native/Flatpak version schemes remain distinct. No new network agent control API.

## Backends and trust

Native packages handle core services, CLI tools and Docker. Flatpak is per-user
for qualified graphical extras. Acquire its required native runtime/portal closure
on explicit first use, outside the offline-base dependency set. B02 provides shared
session infrastructure where already required; do not assume existing Bubblewrap
alone establishes a working Flatpak deployment. Qualify GNOME portals, file picker,
launch and network/permission behavior on the real target. Do not install a second
software center/PackageKit stack just to draw this selection screen.

Native package mutation stays serialized. Flatpak operations also use the shared
setup queue and disk preflight; avoid racing downloads/installs with native image
writes. Rootless Docker is the qualification target; never silently enable a
rootful daemon or grant docker-group root-equivalent access. If prerequisites fail,
keep Docker unavailable with its reason until a reviewed supported route exists.
Compose compatibility is separately checked. No automatic account sign-in, provider
spending, shell-hook execution or daemon activation from a catalog recommendation.

The agent recommends only on request, including an explicitly requested task
requiring an absent app. It looks up catalog IDs and explains suitability; it
cannot generate install commands, grant permissions or select an arbitrary origin.
User review/normal policy still controls dispatch. No background usage scanning,
periodic prompts, recommendation analytics or new LLM service.

## Visual and terminal preparation

Use native searchable categories with names, short descriptions, explicit status
and per-app selection; show review/progress separately. Use text fallback until
icons have reviewed provenance. Do not recolor third-party app logos to mimic
Toddy. Prepare EN/PT copy and existing semantic fixtures; no new standalone demo
site or full marketplace. Portal languages do not expand native runtime scope.

Keep Bash and native GNOME terminal, with navy defaults that respect user edits.
Starship and fzf/ripgrep/fd/zoxide/tmux/btop are optional qualified tools. Use an
ASCII-compatible prompt fallback; no mandatory Nerd Font or downloaded shell
framework. Apply hooks only to interactive user shells with explicit selection;
no system /bin/sh replacement, global aliases shadowing standard commands, history
upload or model execution on each prompt. Bound expensive Git/prompt modules.

## Owning slices and proportionate proof

- B01 reviews backend feasibility/contracts; optional catalog breadth cannot block
  its core acceptance. Exact qualification happens in the owning implementation.
- B02/B06 provide terminal defaults and the shared agent-independent controller.
- B11 uses existing identity, categories and native presentation.
- B12 joins final selection, pending handoff, acquisition/review/removal and agent
  recommendation entry using existing policy/tool boundaries, not a second shop.
- B13 proves the scoped catalog on the exact installed candidate.

First qualification priorities: Docker, OpenCode, VS Code and LocalSend (first
Flatpak path). Do not make all 28 candidates mandatory release gates. Unsupported
candidates stay clearly unavailable. A failed Flatpak qualification blocks that
advertisement, not offline boot or unrelated native paths. Each advertised supported
app still needs its S20 install/launch/remove proof; fixtures cannot replace it.

S19/S20/S21/S26 cover offline/save/reboot/recover, skip/dismiss, absent agent,
confirmation, bad integrity, network loss, low space, duplicate requests and removal.
Include one native and one Flatpak path when both are advertised, backend/origin
mismatch and a recommendation that cannot escalate privilege. Native visual checks
cover focus, EN/PT wrapping and visible progress. Reuse unchanged evidence; do not
rerun OS builds for catalog copy edits. Repository preparation itself runs only
catalog/reference/translation integrity and existing make check.
