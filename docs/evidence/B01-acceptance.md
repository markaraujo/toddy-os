# B01 acceptance audit

Date: 2026-11-07 America/Sao_Paulo. Scope: architecture candidates/contracts and
native feasibility, as required by B01. This does not accept B02–B13 or G2.
Owner implementation authority is [ADR-0113](../adr/0113-owner-authorizes-phase2-implementation.md).
Historical G1 evidence remains unchanged; physical foundation tests are pending.

| B01 criterion | Actual evidence and selected contract |
| --- | --- |
| Pinned GNOME/native UI/Pi candidates, successful tool spike, license/runtime review | [Thirty-one authenticated source identities](../../config/phase2/sources.lock.json), [desktop root legal notices](B01-desktop-root-notices.json), [Pi archive/file/license inventory](B01-engine-components.json), [native eleven-case tool/cancel/disconnect/protocol proof](B01-pi-native-fixture.json), [ten owned native packages](B01-native-packages.json). GTK4.22.4/Libadwaita1.9.3/GNOME50 roots are candidates, not working desktop claims. No mandatory hosted/proprietary runtime. |
| Minimal default applications, optional developer and hardware policy, no Ubuntu repositories | [Frozen root/ABI/package contract](../../config/phase2/architecture.lock.json), [shared catalog](../../config/phase2/software-catalog.json), [installation matrix](../PHASE-2-INSTALLATION-MATRIX.md). One Firefox-source browser, Nautilus, GNOME Terminal, Text Editor, settings/network/audio/accessibility; Git base, Docker/OpenCode optional, mise excluded. Exact source versions/hashes are frozen. Browser source-build default branding preserves upstream trademark limits. Unqualified app/firmware/driver packs stay unavailable; no broad hardware claim or all-catalog G2 gate. |
| Reference target, measured baseline, numeric budgets and small slices | [Cold foundation clone](B01-foundation-clone.json), [actual baseline](B01-foundation-inventory.json), [native Pi timing/RSS](B01-pi-native-fixture.json), [build/runtime budget and next-slice contract](../../config/phase2/architecture.lock.json). Builder12vCPU/12GiB, runtime reference4vCPU/8GiB, Node4/Qt6/generic8 build jobs. Initial full snapshot18.714s. Native Pi eleven cases0.643s/65,912KiB child peak, on the builder. Desktop/service/model/reference performance remains staged S01-B/C/D/B03/B13, not fabricated from these numbers. |
| Customizable profile/config/skill interface, precedence/revision/policy | [Interfaces](../PHASE-2-INTERFACES.md), [profile schema](../../config/phase2/profile.schema.json), [secret-free preset](../../config/phase2/profile/config.json), [harness](../PHASE-2-HARNESS.md), [architecture lock](../../config/phase2/architecture.lock.json). Defaults→profile→bounded task, validated SHA256 revision/CAS, bounded instruction-only skills, no imported credential/root grant. Full administration stays possible through independent authenticated/revocable owner policy. B01 reviews these contracts; it does not claim future S24 UI/store operations passed. |
| UI/engine bridge, installer/package/image feasibility, CPU model and no-write evidence | [Installed async GIO/actual peer/signal/sealed FD proof](B01-gio-installed-bridge.json), [versioned typed XML](../../runtime/broker/io.github.markaraujo.Toddy.Service1.xml), [strict framed Pi worker](../../runtime/engine/fixture-worker.mjs), [native Calamares/PythonJob/JobResult/typed JSON target-plan proof](B01-calamares-native-probe.json), [native prerequisites](B01-installer-prerequisites.json), [ADR-0116](../adr/0116-native-installer-feasibility-and-json-plan-boundary.md), [CPU model/runtime artifact contract](../../config/phase2/local-model.lock.json). Existing accepted H13 image/boot/trust machinery plus verified own native archives remains the assembly route; explicit builder/offline/live/acquisition roots and account/boot/package-trust closure are frozen. [Frozen installed-root recipe](../PHASE-2-ROOT-RECIPE.md) covers GPT/ext4, UUID fstab/installed initramfs, GRUB BIOS/UEFI, fresh owner identity, public Signed-By trust, rescue/update and live-state removal. Final image/install/recovery proof is B12, model inference/tool proof B03. |

The selected assembly contract uses verified native own archives and explicit
per-image allowlists. Preserve accepted required foundation tools and existing
QA/credential exclusions. Do not treat a dirty development-root copy followed by
secret removal as the sole release closure. New build SDKs, live accounts/autologin,
signing keys, caches, copied machine identity and implicit grants are excluded.
Offline desktop/setup does not depend on Node/Pi/executor/model/voice/Flatpak.
The installed user reviews later acquisition through the agent-independent
native package route. Linux account authentication belongs to its dedicated
installer flow; the no-provider-credentials rule does not prohibit creating the
target owner's login credentials in B12.

Reuse the accepted BIOS/UEFI media-integrity route and frozen kernel ABI. B12
must prove the new installed root's bootloader, UID/home/machine identity, signed
package trust, persistence, cancellation/replay and recovery. No new Phase2 ISO,
graphical installer, native GNOME session or physical hardware success is claimed.

Source qualification remains incremental: B01 freezes top-level candidates and
actually tested shared inputs, not every optional/recommended BLFS package.
Resolve a consumer's required feature edges before its build; authenticate/pin
new transitive archives, retain per-file/bundled notices, stage/inspect ownership,
and run the smallest affected native consumers. The [scoped required/capability graph](../../config/phase2/desktop-dependencies.json)
is generated from frozen package sections, selecting GNOME/Wayland requirements
and the source-verified editor/spelling edges. GNOME Shell supplies notifications;
GNOME portal is selected from alternatives. No LXQt/KDE desktop is pulled in.
Aggregated Xorg pages represent capabilities, not a mandate to install every
listed package. Native feature qualification/source integrity still gates each build.
The earlier rough whole-book discovery is not an approved build lock. No full KDE/QtWebEngine/PySide stack is
introduced by the CoreAddons/Qt probe. Keep full-root native transactions until
optimized path coverage is qualified; old compiler harness receipts are not new
cache qualification. Final image integrity/ELF/dependency audits remain mandatory.

All original failures and successful corrective steps are preserved in [B01](B01.md),
[errors](../errors.md) and the local per-cause ledger. Unchanged long foundation
suites were not repeated. Repository delivery uses `make check`; native evidence
above comes from actual source-built LFS userspace, not the host's Python/Qt.

Next independently reviewable story: B03 by the default risk-first selector.
Start with pinned local CPU runtime/source staging and a real offline inference
boundary; reuse the native Node/Pi/GIO packages. B04 is also eligible after B01,
but B05 still requires B03+B04. B02 may advance as an eligible graphics branch;
the short continuation card must preserve whichever slice is actually active.
