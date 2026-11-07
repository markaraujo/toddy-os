# ADR-0112: Shared software catalog and deferred acquisition

- Date: 2026-11-07 America/Sao_Paulo
- Status: Accepted preparation; native qualification/implementation pending
- Preserves: ADR-0063, offline base, story graph and proportional validation

Owner approved Git in base, Docker/OpenCode optional, no mise, and mixed native/
Flatpak delivery. Final installer selection saves intent only; acquisition happens
in the installed user's session after review. Recommendations are on request only.
Adopt PHASE-2-SOFTWARE-CATALOG.md and the non-executable candidate manifest.

Reuse the existing pending-choice IDs/state and shared native transaction route.
The setup/catalog controller must work without the agent. Flatpak GUI extras are
per-user; their runtime is optional. Native core/CLI tooling and essential hardware
setup keep existing ownership/policy. No new shop, arbitrary model-generated
install commands, automatic remote installer scripts or background recommendations.

First qualification targets Docker/OpenCode/VS Code and LocalSend; remaining
candidates stay unavailable until proven. No requirement to ship the whole catalog
for G2. Preserve required scoped app acceptance and source/license/permission review.
No downloaded binaries, live installers, guest approval or runtime acceptance are
created by this documentation/catalog preparation.
