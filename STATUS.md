# Toddy OS — Current status

Updated: 2026-11-07

Bootstrap: ready_for_development

H01-H07 completed: 126 native packages, final metadata/audits and cold checkpoint verified. H08 is in progress for identity/services/network configuration. Full Berkeley standard coverage is explicitly reduced by owner approval (ADR-0092). No foundation ISO or G1 yet. Deliver H13/G1 for owner testing and await approval before B01-B13.

Foundation: **62%** · Agentic desktop: **0%**

G1: pending · G2: pending · Next: **H08**

No milestone earns credit without completed acceptance evidence.

## Active story: H08 — Configure identity, services and basic networking

The 62% phase total counts completed stories only. H08 is still in progress; its 6 points are not yet counted. Passing this story would raise the phase total to 68%.

Last verified: 2026-11-07 11:50 UTC

Verified:

- H07 accepted with 126 native packages, eight audits and verified cold pair h07-final-base.
- Frozen LFS 13.1-systemd chapter 9 and 10.2 reviewed; prepared H08 configuration and offline service policy have private-root tests (ADR-0042/0060).

Running: Applying the guarded native configuration next; actual identity/service/locale/ownership postchecks are pending.

Remaining:

- Install and verify owned base configuration with preserved bootstrap files.
- Verify offline service policy, locale/account/filesystem settings and ownership.
- Retain actual boot/DHCP/service behavior for H12 verification.

[Acceptance evidence](docs/evidence/H07.md)

| Story | Phase | Weight | Status |
| --- | --- | ---: | --- |
| [H01 — Inspect host and select isolated build environment](stories/H01.md) | foundation | 4 | completed |
| [H02 — Freeze books, sources and integrity manifest](stories/H02.md) | foundation | 4 | completed |
| [H03 — Prepare target, build user and package ownership](stories/H03.md) | foundation | 4 | completed |
| [H04 — Build the cross-toolchain](stories/H04.md) | foundation | 10 | completed |
| [H05 — Build temporary tools](stories/H05.md) | foundation | 8 | completed |
| [H06 — Enter chroot and create recoverable checkpoint](stories/H06.md) | foundation | 8 | completed |
| [H07 — Build and test the final base system](stories/H07.md) | foundation | 24 | completed |
| [H08 — Configure identity, services and basic networking](stories/H08.md) | foundation | 6 | in_progress |
| [H09 — Build kernel and boot configuration](stories/H09.md) | foundation | 8 | not_started |
| [H10 — Assemble the live system](stories/H10.md) | foundation | 8 | not_started |
| [H11 — Produce hybrid ISO and artifact manifest](stories/H11.md) | foundation | 6 | not_started |
| [H12 — Verify foundation boot matrix and recovery](stories/H12.md) | foundation | 6 | not_started |
| [H13 — Deliver and accept foundation gate G1](stories/H13.md) | foundation | 4 | not_started |
| [B01 — Evaluate desktop, harness, licensing and resource budgets](stories/B01.md) | agentic | 5 | not_started |
| [B02 — Build the graphical desktop and essential applications](stories/B02.md) | agentic | 10 | not_started |
| [B03 — Integrate provider adapters and local inference](stories/B03.md) | agentic | 8 | not_started |
| [B04 — Implement native tools and privileged execution](stories/B04.md) | agentic | 8 | not_started |
| [B05 — Implement durable agent tasks and configuration reconciliation](stories/B05.md) | agentic | 10 | not_started |
| [B06 — Provide terminal, desktop and first-run experience](stories/B06.md) | agentic | 10 | not_started |
| [B07 — Implement memory, retrieval and portable backup](stories/B07.md) | agentic | 8 | not_started |
| [B08 — Implement proactive health monitoring and automation](stories/B08.md) | agentic | 8 | not_started |
| [B09 — Add text-to-speech and speech-to-text](stories/B09.md) | agentic | 5 | not_started |
| [B10 — Add versioned plugin and MCP interfaces](stories/B10.md) | agentic | 6 | not_started |
| [B11 — Integrate approved branding and production asset variants](stories/B11.md) | agentic | 8 | not_started |
| [B12 — Build and test the graphical installer](stories/B12.md) | agentic | 9 | not_started |
| [B13 — Verify installed daily-use release and gate G2](stories/B13.md) | agentic | 5 | not_started |
