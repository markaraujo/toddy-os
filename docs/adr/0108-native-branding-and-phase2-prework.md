# ADR-0108: Native branding package and reusable Phase 2 inputs

- Date: 2026-11-07 America/Sao_Paulo
- Status: Accepted design/preparation; native integration pending B11
- Preserves: ADR-0063 approval boundary, approved artwork, B-story runtime gates

The owner requested GNOME branding and parallel preparation that genuinely reduces
later work. Deliver supported distribution inputs through `toddy-branding`, rather
than making a large Shell extension responsible for appearance. Keep Adwaita-based
native behavior, user-controlled defaults and app-scoped styling. Do not patch GDM
resources, apply global GTK CSS, lock decorative settings or reapply them at login.
A minimal version-pinned extension requires an actual shortcut/presentation gap
and a usable ordinary-launcher fallback; it contains no privileged/agent logic.

Select `io.github.markaraujo.Toddy` as the stable application/icon namespace;
profile changes do not alter it. Use distinct broker/executor service names from
ui/phase2/identity.json. The future assistant owns its launcher, while the branding
package owns shared art/catalog/identity exports. Avoid overlapping file ownership
and launchers for absent executables. Exact service contracts remain B01 work.

Prepare existing-asset mappings, wallpaper XML, inactive GSettings defaults,
semantic icon roles, bilingual copy and side-effect-free scenarios. Audit accepted
dependencies before scheduling new builds. These source inputs are individually
reviewable; they do not satisfy guest acceptance or authorize implementation.
See [prework and validation](../PHASE-2-PREWORK.md).

Primary references reviewed 2026-11-07: GNOME application-ID guidance, GNOME system
administrator background/default documentation, GSettings API 2.0 documentation,
GNOME native styling guidance and GJS extension anatomy, linked from the native
branding README. Current upstream documentation is not a guest-version lock.

Rejected: copying web visuals wholesale into GTK; a Shell theme fork; login-time
preference resets; duplicate SQLite/vector infrastructure for basic search; new
model downloads or extensive art variants before a demonstrated consumer need.
These increase maintenance or critical-path uncertainty without runtime evidence.
