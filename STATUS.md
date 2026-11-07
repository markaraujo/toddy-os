# Toddy OS — Current status

Updated: 2026-11-07

Bootstrap: ready_for_development

H01-H11 completed with a revised ISO after reproduced USB discovery correction. The unchanged 134-package root and revised media integrity passed. H12 repeats final-media tests and corrects native retest infrastructure; G1 remains pending. Owner review after H13 precedes Phase 2.

Foundation: **90%** · Agentic desktop: **0%**

G1: pending · G2: pending · Next: **H12**

No milestone earns credit without completed acceptance evidence.

## Active story: H12 — Verify foundation boot matrix and recovery

The 90% phase total counts completed stories only. H12 is still in progress; its 6 points are not yet counted. Passing this story would raise the phase total to 96%.

Last verified: 2026-11-07 13:38 UTC

Verified:

- 4/4 final ISO boots passed: BIOS/UEFI on CD and virtual USB; USB tests offline.
- 3/3 actual recovery cases passed: GRUB rescue, absent media and corrupted Squashfs; original ISO unchanged.
- Original ISO booted successfully again after failure injection; final live DBus XML bounds passed.
- Final image has nine measured dynamic Expat consumers across 2,626 ELF files. Systemd native namespace retry passed; Glibc retry remains open.

Running: Corrected 50-case native regression profile: verify cold backing, execute preserved upstream tests, retain complete dedicated-UART evidence.

Remaining:

- Complete and classify native Glibc/Systemd follow-up results.
- H13 G1 audit, reproducible instructions and owner-testing handoff.

[Acceptance evidence](docs/evidence/H12-final-media.json)

| Story | Phase | Weight | Status |
| --- | --- | ---: | --- |
| [H01 — Inspect host and select isolated build environment](stories/H01.md) | foundation | 4 | completed |
| [H02 — Freeze books, sources and integrity manifest](stories/H02.md) | foundation | 4 | completed |
| [H03 — Prepare target, build user and package ownership](stories/H03.md) | foundation | 4 | completed |
| [H04 — Build the cross-toolchain](stories/H04.md) | foundation | 10 | completed |
| [H05 — Build temporary tools](stories/H05.md) | foundation | 8 | completed |
| [H06 — Enter chroot and create recoverable checkpoint](stories/H06.md) | foundation | 8 | completed |
| [H07 — Build and test the final base system](stories/H07.md) | foundation | 24 | completed |
| [H08 — Configure identity, services and basic networking](stories/H08.md) | foundation | 6 | completed |
| [H09 — Build kernel and boot configuration](stories/H09.md) | foundation | 8 | completed |
| [H10 — Assemble the live system](stories/H10.md) | foundation | 8 | completed |
| [H11 — Produce hybrid ISO and artifact manifest](stories/H11.md) | foundation | 6 | completed |
| [H12 — Verify foundation boot matrix and recovery](stories/H12.md) | foundation | 6 | in_progress |
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
