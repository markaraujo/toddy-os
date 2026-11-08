# Toddy OS — Current status

Updated: 2026-11-07

Bootstrap: ready_for_development

Owner-authorized isolated Phase2 implementation active. B01 verified native engine/GIO and Calamares no-write feasibility, including typed JSON and real JobResult. Final source/root/budget/interface freeze remains before B01 acceptance. Native GNOME, B02–B13/G2, installable Phase2 ISO and physical validation remain pending.

Foundation: **100%** · Agentic desktop: **0%**

G1: passed · G2: pending · Next: **B01**

No milestone earns credit without completed acceptance evidence.

## Active story: B01 — Freeze the minimal Toddy architecture and delivery slices

The 0% phase total counts completed stories only. B01 is still in progress; its 5 points are not yet counted. Passing this story would raise the phase total to 5%.

Last verified: 2026-11-07T23:59:15.867467+00:00

Verified:

- Read-only-backed KVM clone, native GLib package and 14 focused GObject/GDBus cases passed.
- Native Node installed and corrected postcheck passed without replay; original failed context record preserved.
- 11 native Pi tool/cancel/disconnect/protocol cases passed; descriptor-safe compiler and parent-lock proof passed.
- Native GI/GLib core metadata/PyGObject installed; installed GIO async/actual peer/signal/FD fixture passed with no namespace children.
- Calamares3.4.3 bundled Pybind11 2.11.1 compiled/linked/embedded native Python3.14.10 unchanged.
- Native QtBase6.11.2 source/stage/package and offscreen Widgets/TLS/DBus/Concurrent consumer passed; visual/display/font integration pending.
- Calamares3.4.3 source/stage/startup and actual PythonJob/JobResult synthetic plan with nine negative cases passed; typed JSON Boolean boundary verified.

Running: Final B01 architecture/root/license/budget freeze using verified probes and exact source identities; no guest writer active.

Remaining:

- Final source/license/root/ABI and resource contracts; assess all B01 criteria before completion.

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
