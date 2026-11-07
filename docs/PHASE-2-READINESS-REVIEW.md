# Phase 2 — Implementation readiness and graphical delivery review

Date: 2026-11-07. This closes the latest whole-plan review after ADR-0110.
Phase 2 is a graphical product as well as an agent/backend integration. Review
includes the story graph, native UI, installer/brand, offline setup, package/build
strategy and validation/resumption rules. This is planning evidence, not a claim
that an unbuilt desktop is correct or performance has been measured.

## Remaining execution gaps and dispositions

| ID | Risk | Selected correction and owner |
| --- | --- | --- |
| V01 | Code/unit checks could pass while the real window is unusable | B02/B06/B11/B12 require actual native view/interaction for affected graphical slices; HTML concepts are design inputs, not native acceptance |
| V02 | GTK assistant and Qt installer could diverge or require fragile global styling | Reuse semantic brand roles, artwork and motion intent; adapt with supported native controls per toolkit. Do not port web CSS or force identical pixel geometry |
| V03 | Designing only happy-state screenshots defers UI restructuring | Before B06 widgets harden, bind existing semantic fixtures to empty/deferred/loading/running/waiting/uncertain/error/canceled/completed states and recovery actions |
| V04 | Model/IPC work or unbounded response rendering could freeze the visual shell | Keep I/O/inference off the UI loop, bounded update coalescing, paged history and bounded visible output. No database write or full Markdown re-render per token |
| V05 | Fixed-size concepts hide small-screen, scaling and translation failures | Early native layout check uses EN/PT, long text, 1280x720 and a reduced effective viewport; support scrolling/reflow and keep primary actions reachable |
| V06 | Animation and screenshots can dominate startup or conceal progress | Lazy-load decorative scenes, use static fallback/reduced motion, pause hidden motion. Real installer progress/errors/Stop never depend on scene timing |
| V07 | Final art preparation could become speculative rework | Preserve approved masters, use native theme icons, export only sizes actually consumed; real captures replace concepts only after native behavior exists |
| V08 | Many review documents could make the development agent reread/replan indefinitely | Use the short navigation below. Treat selected decisions as settled; revisit only on a measured failure or changed requirement, not every turn |

## Graphical definition of a working slice

A backend slice can be headless. A graphical slice needs both its data/function
check and one actual native interaction on the relevant supported target. Record
which UI/toolkit/artifact was observed. A browser screenshot proves the browser
study only; it cannot validate GNOME focus, Qt controls or native service binding.
Do not create a second screenshot framework or broad pixel-perfect golden suite.

For each affected graphical delivery, inspect only the relevant path:

- Open via the real launcher, navigate with keyboard and activate the primary
  action; focus is visible and the window remains responsive during work.
- Show the applicable missing-backend/offline/error or uncertain state with a
  clear next action. No fake successful progress; model loading and task progress
  have distinct meanings. Critical disk/permission text is plain and visible.
- Check the changed screen in normal and relevant light/dark/high-contrast modes;
  larger text and EN/PT wrapping must not hide Stop, Back or disk confirmation.
  Basic checks are scoped; deeper assistive-device coverage remains owner backlog.
- Capture a representative actual screen after the path works. Keep fake values
  labeled, exclude secrets/private data, and retain exact artifact identity.

A slice that changes only a backend algorithm does not rerun all graphical checks.
A shared layout/theme/icon/text change invalidates the affected visual surfaces.
A native release gate still needs its small integrated graphical path. If display
or tooling is unavailable, record the missing native validation and continue other
eligible work; never substitute a fabricated screenshot or declare visual success.

## Native rendering decisions to settle before screen proliferation

Use system font/settings and logical sizing. Do not require downloading a website
font for login or the installer. Native GTK/Qt standard widget metrics take
precedence over web mockup dimensions. Small logo exports must be checked at actual
launcher sizes, without modifying approved master pixels. Images preserve aspect
ratio and cannot determine minimum window width; provide readable fallback text.

Use UI copy IDs and escaped plain values from ui/phase2; localize full messages,
not concatenated fragments. Installer narrative may be playful; permission,
credential, disk and recovery meanings remain neutral. A changed action is labeled
according to actual capability, especially offline setup with the backend absent.

For long tasks, append bounded/coalesced output rather than rebuild the whole view.
Start with one visible conversation and a page of up to 50 history entries; load
more explicitly. Do not load all SQLite history at startup. Apply selected profile
budgets separately from rendered text limits; truncation/paging must not alter task
state or hide an unresolved operation. B06 records actual startup/input/streaming
response against the plan's reference budgets; these are design choices, not
measured speedups. No mandatory browser/Electron runtime for the native interface.

## Short reading map and freeze boundary

The development agent reads AGENTS, status and the continuation card, then the
current story. Use PHASE-2-PLAN as requirements and PHASE-2-EXECUTION as procedure.
Read only the specialist contract needed by the current slice:

| Current work | Targeted reference |
| --- | --- |
| Dependency/build/package graph | PHASE-2-DEPENDENCY-PREWORK, PHASE-2-CRITICAL-PATH, ADR-0110 |
| Agent/profile/IPC | PHASE-2-INTERFACES and PHASE-2-HARNESS |
| Native visual/installer assets | assets/brand/gnome and assets/brand/installer README files, ui/phase2 |
| Installer/package lifecycle | PHASE-2-INSTALLATION-MATRIX and PHASE-2-PACKAGES |
| Checks and unattended recovery | PHASE-2-VALIDATION and PHASE-2-NIGHT-EXECUTION |

Do not require reading all supplementary reviews every slice. Do not introduce new
architecture, artwork variants, dependency surveys or reviews without a concrete
unresolved acceptance need. Existing selected strategy is ready for target proof;
new discoveries belong to a narrow decision/correction, not a whole-plan restart.
Guest implementation still requires explicit recorded owner continuation.

## Performance assessment and proof boundary

The strategy avoids known repeated work: accepted foundation reuse, qualified
staging/isolation, affected-check selection, lazy optional runtime, bounded IPC and
one guest writer. Major potential costs remain graphics/browser/Qt compilation,
runner scans and source acquisition, with measurements scheduled before costly
integration. Early UI interaction checks reduce late layout/integration rework.

No benchmark currently proves this is the fastest schedule or guarantees an
overnight completed release. B01/B02 measure build stages, B06 native rendering,
and B12 actual installation. Keep full verification for unqualified root writes;
never trade away integrity to improve a speculative timing estimate. Quality is
established by actual scoped acceptance, not by the number of planning reviews.
