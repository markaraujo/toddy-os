# Phase 2 — Preparation with practical execution value

Date: 2026-11-07. These are repository inputs and an execution-priority review,
not installed features or B-story acceptance. The owner requested useful parallel
preparation, including native GNOME branding. Guest implementation still requires
recorded explicit continuation under ADR-0063.

## Priorities and actual outputs

| Priority | Preparation | Practical benefit | What remains unproved |
| --- | --- | --- | --- |
| 1 | [Accepted dependency reuse and heavy-chain audit](PHASE-2-DEPENDENCY-PREWORK.md) | Avoid rebuilding accepted Python, SQLite/FTS5, build tools and package machinery; expose graphics, Firefox/Rust, Node and Qt chains early | Exact compatible graph, native recipes, resource limits and B01 spikes |
| 2 | [Semantic EN/PT messages and scenarios](../ui/phase2/README.md) | UI work can use consistent success, cancellation, uncertain-result and failure fixtures without a paid API or model download | Real service transitions, safe cancellation, credential and disk safety |
| 3 | [Native branding package inputs](../assets/brand/gnome/README.md) | Existing approved art already has a package map, wallpaper catalog and inactive defaults template | Actual GNOME integration, upgrade/removal, preference preservation and screenshots |
| 4 | [Stable application identity](../ui/phase2/identity.json) and [icon roles](../ui/phase2/icon-roles.json) | Avoid incompatible desktop/D-Bus/icon names and ad hoc icon replacement later | Native launcher activation, target theme lookup and readable production icon exports |
| 5 | Dependency graph and cache receipts described in the dependency audit | Schedule independent source/build branches without stale cache reuse or duplicate package writers | Target-dependent graph/receipt completion belongs to B01 |

Prepared copy contains 40 bilingual messages and 10 fictional semantic scenarios.
Fixtures are not wire payloads, executed tests or a substitute for runtime proofs.
Reuse them in the owning slice; do not build a second UI demo or testing framework.
Keep critical permission/error text neutral and Toddy's humor in optional narrative.

## Native branding decision

Use `toddy-branding` for owned wallpapers, background catalog, identity exports
and supported distribution defaults. Use Adwaita/Libadwaita light/dark/accessibility
behavior and app-scoped styling. Do not use a large Shell extension as the theme,
patch GDM resources, force settings at each login or copy website CSS into GTK.
User preferences must survive upgrades; do not lock dconf keys for decoration.
The assistant owns its launcher only once a real executable exists.

Application identity is `io.github.markaraujo.Toddy`; planned broker/executor
names are listed in identity.json. This uses the maintainer-controlled GitHub
namespace. Profile/persona changes do not rename the application. These identifiers
are selected integration inputs, not installed services or a frozen IPC schema.
A small version-pinned Shell extension is considered only for a demonstrated
shortcut/presentation gap; disabling it must preserve the ordinary launcher.
See [ADR-0108](adr/0108-native-branding-and-phase2-prework.md).

## Parallel work and serialization

Before guest start, independent asset provenance review, copy refinement,
dependency metadata review and fixture preparation can proceed in separate file
ownership scopes. Each produces a small diff with a narrow check and a handoff.
Do not invent future dependencies or export many assets before their native
consumer requirements are known.

After approval, B01 locks and probes the shared prerequisites first. Independent
source metadata and verified downloads can overlap when authorized, but compilation
concurrency requires measured RAM/disk/job budgets. Keep one package database and
image writer. Do not equate separate agents with safely concurrent guest installs.
The [execution playbook](PHASE-2-EXECUTION.md) controls eligible story ordering;
prework does not override prerequisites.

The biggest expected savings are accepted-package reuse, early compatibility
proofs and deterministic scenarios. Actual time savings are unmeasured. Spending
more time on decoration, a speculative dependency lock, broad new test suites or
model downloads now would not establish a faster critical path.

## Validation and handoff

Repository checks passed: `make check` (197 tests); wallpaper/source provenance,
icon-license references, catalog/placeholder parity and fixture references.
`desktop-file-validate` accepted a temporary rendered launcher using `/usr/bin/false`
as a syntax-only placeholder. `glib-compile-schemas --strict --dry-run` accepted
the defaults against temporary copies of host schemas. Neither command installed
files or changed settings; host schema compatibility is not target compatibility.
B11 must repeat validation against the locked guest schemas and actual package.

Keep original logo/mascot bytes. Existing wallpapers are 1672x941, not 4K;
small-size PNG icon exports, cropping/scaling and real light/dark/high-contrast
review remain B11. Website expression frames and concept screenshots are excluded
from the native package. Replace labeled design concepts with actual guest
captures only when the corresponding behavior exists.

All B stories remain not_started, G1 passed and G2 pending. No guest job, ISO,
model, provider call, runtime acceptance or hardware test was created here.
