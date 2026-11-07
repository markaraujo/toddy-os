# Toddy OS — Current status

Updated: 2026-11-07

Bootstrap: ready_for_development

Owner-authorized isolated Phase 2 implementation is active (ADR-0113). B01 cloned/inventoried the accepted foundation, proved native build containment and installed source-built GLib with focused native checks. Native Node compilation is running for the Pi spike; worker protocol fixtures pass on the developer host only. B01 acceptance, B02–B13, G2 and physical hardware validation remain pending.

Foundation: **100%** · Agentic desktop: **0%**

G1: passed · G2: pending · Next: **B01**

No milestone earns credit without completed acceptance evidence.

## Active story: B01 — Freeze the minimal Toddy architecture and delivery slices

The 0% phase total counts completed stories only. B01 is still in progress; its 5 points are not yet counted. Passing this story would raise the phase total to 5%.

Last verified: 2026-11-07T22:24:18.077150+00:00

Verified:

- Read-only-backed disposable KVM clone and native package audit passed.
- Native isolated compiler/staging/write-denial proof and GLib bootstrap install/postcheck passed.
- 14 focused GLib/GObject/GDBus cases passed; host-only Pi protocol/tool/cancel fixture passed.

Running: Native Node 24.19.0 source build under isolated unprivileged staging; one guest writer.

Remaining:

- Native Pi and GIO bridge spikes, exact dependency/license/root inventory.
- Calamares no-write probe, CPU model contract and final B01 budgets/acceptance.

[Acceptance evidence](docs/evidence/B01.md)

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
| [H12 — Verify foundation boot matrix and recovery](stories/H12.md) | foundation | 6 | completed |
| [H13 — Deliver and accept foundation gate G1](stories/H13.md) | foundation | 4 | completed |
| [B01 — Freeze the minimal Toddy architecture and delivery slices](stories/B01.md) | agentic | 5 | in_progress |
| [B02 — Deliver the minimal branded GNOME desktop](stories/B02.md) | agentic | 10 | not_started |
| [B03 — Connect provider adapters and one optional local AI profile](stories/B03.md) | agentic | 8 | not_started |
| [B04 — Deliver native tools and the revocable privileged executor](stories/B04.md) | agentic | 8 | not_started |
| [B05 — Persist tasks and recover interrupted system changes](stories/B05.md) | agentic | 10 | not_started |
| [B06 — Deliver Toddy quick entry, native UI and first-run setup](stories/B06.md) | agentic | 10 | not_started |
| [B07 — Deliver inspectable local memory and portable backup](stories/B07.md) | agentic | 8 | not_started |
| [B08 — Deliver quiet health monitoring and one persistent automation](stories/B08.md) | agentic | 8 | not_started |
| [B09 — Deliver optional push-to-talk and spoken Toddy responses](stories/B09.md) | agentic | 5 | not_started |
| [B10 — Deliver a bounded plugin interface and one MCP integration](stories/B10.md) | agentic | 6 | not_started |
| [B11 — Integrate the navy brand and nerdy Toddy installer scenes](stories/B11.md) | agentic | 8 | not_started |
| [B12 — Deliver guided offline installation and optional software setup](stories/B12.md) | agentic | 9 | not_started |
| [B13 — Deliver the basic-tested experimental owner preview and G2](stories/B13.md) | agentic | 5 | not_started |
