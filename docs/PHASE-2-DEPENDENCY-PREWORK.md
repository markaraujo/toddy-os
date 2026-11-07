# Phase 2 — Dependency reuse and build preparation

Date: 2026-11-07. This is a preparation audit, not a new package lock or evidence
of a desktop build. The [selected baseline](PHASE-2-DESIGN-BASELINE.md) remains
unchanged. B01 still requires explicit owner continuation approval and its actual
spikes; preparing this document does not start a B story.

## Reuse the accepted foundation

The committed [component inventory](evidence/H11-components.json) contains 134
native packages. [H13](evidence/H13.md) binds that inventory to the accepted
foundation and 142 verified corresponding source inputs. The inventory's
`release_complete: false` does not mean the desktop exists: G1 covers the
foundation only. Package versions below include Toddy packaging revisions where
important; the inventory retains every exact revision and provenance hash.

| Existing native inputs | Concrete reuse | Limit of the evidence |
| --- | --- | --- |
| GCC 16.2.0, Glibc 2.44, Linux 7.1.8 | Existing compiler, libc and target kernel | New consumers still need compatibility checks; do not silently upgrade the foundation |
| Python 3.14.10-1+toddy2, libffi 3.8.0 | Broker/executor language and binding prerequisites | PyGObject and GLib/GIO are not installed |
| SQLite 3.53.4-1+toddy1 | Canonical task/profile/memory storage | Application migrations, concurrency, profile isolation and deletion remain new work |
| Meson 1.12.0, Ninja 1.13.2, CMake 4.4.2, pkgconf 3.0.5, Autoconf 2.73, Automake 1.18.1 | Reuse native build tooling across desktop, installer and ML sources | A build tool's presence does not satisfy each project's minimum version/options |
| D-Bus 1.16.2, Systemd 261.2 | Existing bus/service foundation | Typed GIO bindings, service activation and owner authorization remain unproved |
| OpenSSL 4.0.3, Curl 8.23.0, CA certificates, libuv 1.52.1, libseccomp 2.6.1 | Existing crypto/download/event/confinement primitives | libuv does not provide Node; libseccomp does not provide a plugin sandbox |
| Dpkg 1.22.22, APT 3.0.4, GnuPG 2.5.24 | Existing source-built package ownership and signed repository route | No Ubuntu binary/repository compatibility is implied |
| GRUB 2.14, e2fsprogs 1.47.4, util-linux 2.42.4, squashfs/media tools | Reuse boot, filesystem and ISO primitives | GUI partitioning, installed boot and recovery still belong to B12/B13 |

SQLite FTS5 is already enabled in the [native recipe](../scripts/build/h07/sqlite-inner.sh)
and passed an actual persisted FTS transaction and integrity check:
[postcheck](../scripts/build/h07/sqlite-check.sh), [H07 evidence](evidence/H07-progress.md).
Do not build another SQLite or add a vector database to obtain basic search.
B07 must still prove these operations through its own Python/application path.

The [frozen books](../config/books.lock.json), [source lock](../config/sources.lock.json)
and [supplemental inputs](../config/supplemental-sources.lock.json) remain the
starting point. Existing accepted recipes and component records are reusable;
an old source URL alone is not proof of current suitability. H13's Expat consumer
qualification remains open for new XML consumers.

## New chains to expose before large builds

None of the following selected application stacks appears in the accepted
component inventory. The dependency descriptions are preparation targets, not an
exhaustive or version-resolved bill of materials. B01 must derive the exact graph
from the frozen BLFS 13.1-systemd sections and the chosen upstream releases.

| Chain | Preparation that avoids later rework | Actual proof still required |
| --- | --- | --- |
| GLib/GIO → introspection/PyGObject; GTK4/Libadwaita | Resolve one shared binding/UI chain for broker, executor and interface; keep GTK/model imports out of root service | Python 3.14 binding/import compatibility, typed asynchronous calls and native ownership |
| Graphics/input → Wayland/Mesa/Mutter/GNOME | Separate minimal session requirements from optional GNOME applications; identify graphics compiler requirements from selected Mesa options | Real session, rendering/input, settings and shortcut fallback on the target |
| Firefox and its build toolchain | Identify the selected release's Rust and other build inputs early; account for any separate GNOME JavaScript consumer | Native build/launch, isolated profile and scoped accessibility on a local page |
| Node.js → Pi Core/Pi AI | Review Python-independent worker runtime, lockfile and transitive licenses; inspect OpenSSL 4 and existing libuv compatibility before choosing bundled/system libraries | Exact Node/Pi lock, framed stdio/tool spike, cancellation and aggregate resource measurements |
| Qt → Calamares and project modules | Identify actual selected Qt/module requirements and package footprint before desktop integration | B01 no-write startup/module spike; no installation or disk mutation during that spike |
| Audio/session integration → whisper.cpp/Piper or eSpeak NG | Separate capture/playback from inference and separate engine licenses from model/voice licenses | B09 device/EN/PT tests, cancellation, intelligibility and measured resources |
| llama.cpp and selected model | Keep CPU reference build options and model artifact separate; avoid incidental GPU/SDK dependency chains | B01/S05 target capability and local authenticated transport proof; approved artifact/hash/resource record |
| Bubblewrap and sandbox policy | Reuse existing kernel/Systemd/seccomp inventory as inputs, not proof of confinement | Namespace/capability and actual filesystem/IPC/network/credential denial tests; reviewed fallback if needed |

Python 3.14 and OpenSSL 4 are compatibility review priorities, not observed
failures in these unbuilt consumers. Piper's selected packaging/runtime must be
checked against the native Python/ABI/CPU target; a downloaded wheel is not an
accepted native dependency closure. Likewise, do not assume one SpiderMonkey or
Rust version satisfies all unrelated consumers. A concrete incompatibility
reopens only its affected choice through an ADR.

## Prioritized work that saves execution time

1. **Build the graph before fetching or compiling.** For each new package record
   source/version/hash, required and optional edges, consumer, license, build
   tool requirements, configure options, installed ownership and smallest useful
   postcheck. Mark edges as verified or unresolved. Resolve shared GLib/binding
   and graphics dependencies once; identify independent Firefox, Node and Qt
   chains early. Do not create another framework survey.
2. **Reuse accepted packages and verified inputs.** Compare the graph against the
   134-package inventory before scheduling a recipe. Reuse the existing
   [staging/ownership machinery](../scripts/build/stage_package.py) and
   [step runner](../scripts/build/run_step.py), rather than installing untracked
   payloads or rebuilding the base. Preserve existing source/recipe provenance.
3. **Make cache eligibility explicit.** Record target architecture, source and
   patch hashes, recipe/supporting-recipe hashes, options, compiler and relevant
   dependency versions in a build receipt. Reuse only a matching package with
   intact hash/ownership/postconditions. Keep verified source archives separate
   from mutable build trees. A stale marker, host binary or successful previous
   PID is not a cache hit. Changed dependencies trigger affected consumer checks,
   not an automatic unchanged full compiler/libc rebuild.
4. **Put heavy build branches on the critical-path review.** Record measured
   available RAM/disk and bounded job limits before Rust/Firefox, graphics,
   Qt or neural-runtime compilation. Do not promise a duration before measuring.
   Keep one guest/package writer; independent documentation or source metadata
   review may proceed alongside it, while competing installers may not.
5. **Keep optional bytes optional.** Model/voice weights, GPU backends and developer
   applications do not enter the default ISO merely to simplify testing. Maintain
   an artifact/source/license manifest and verified acquisition policy, with
   secrets and large archives outside Git. No model download or automatic remote
   fallback is authorized by this audit.
6. **Use narrow proofs and retain failures.** Reuse G1 evidence for unchanged
   foundation packages; test the new dependency boundary and its affected
   regressions. Boot/install, privilege/credentials, cancellation/replay and
   recovery gates remain mandatory. Follow the existing
   [validation stages](PHASE-2-VALIDATION.md) and
   [execution/resumption rules](PHASE-2-EXECUTION.md).

## Preparation boundary and handoff

**Safe preparation now:** this inventory comparison, a draft dependency graph,
package naming/ownership review, build-receipt field definition, license/source
metadata review and deterministic IPC/UI fixtures. These are independently
reviewable slices. They must retain unresolved/version-dependent edges rather
than present a speculative package list as a completed lock.

**After explicit approval, in B01:** inspect the actual restored target, lock
compatible release/commit/hash bytes, review new-consumer security/ABI/license
closure, verify sources before extraction, prove the smallest native binding,
worker/provider, local-model and no-write installer spikes, and record measured
build/runtime limits. Exact recipes and cache eligibility become reliable only
against that locked graph and observed target.

**Later stories:** B02 builds the real minimal desktop; B06 proves the service;
B09 adds measured optional speech; B11 integrates branding into the guest;
B12/B13 prove installation, boot and recovery. Repository preparation does not
complete their criteria. [B01](../stories/B01.md) and the
[execution playbook](PHASE-2-EXECUTION.md) remain authoritative for ordering and
continuation; this audit adds no new acceptance gate or broad test matrix.
