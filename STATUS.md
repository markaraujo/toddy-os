# Toddy OS — Current status

Updated: 2026-11-07

Bootstrap: ready_for_development

B01 accepted for architecture/native feasibility (5% Phase2). B03 optional CPU-local runtime implementation started with pinned sources and explicit CPU gates. Provider/model tasks, native GNOME, installed Phase2 ISO, B02/B04–B13/G2 and physical validation remain pending.

Foundation: **100%** · Agentic desktop: **13%**

G1: passed · G2: pending · Next: **B02**

No milestone earns credit without completed acceptance evidence.

## Active story: B02 — Deliver the minimal branded GNOME desktop

The 13% phase total counts completed stories only. B02 is still in progress; its 10 points are not yet counted. Passing this story would raise the phase total to 23%.

Last verified: 2026-11-08T13:29:09+00:00

Verified:

- B01 accepted graph and native GLib/GIO/introspection/PyGObject/Qt/Node packages reused; B03 accepted.
- B04 core/user tools/signed native package and Stop/revoke/recovery verified; final runtime integration blocked by absent native NM/polkit/running system bus.
- Native libxml2-2.15.3 compile7 programs/3904 regression cases/stage0; native package install/post0/0 and XML external-loader deny/positive control passed. Full-root scans19.328s of22.343s; optimization not enabled.
- Owned native Wayland1.26 after26 combined tests, unchanged-binary FD correction and postcheck-only EGL metadata reconciliation; actual client/server sync passed. Protocols1.49 native191 tests/install/post0/0.
- Native Pixman0.46.4 source35 tests/stage0, owned install/post0/0 with opaque/transparent pixel-composite consumer; kernel config already enables virtual DRM/user namespaces/seccomp (configuration only).
- Owned Rust1.97.1 SDK, proportional serif/fonts/Pango and12 independent Python test-tool backends qualified; original compiler/test evidence reused.
- Native keyboard data2.48/libxkbcommon1.13.2 with exact patch owned0/0;26 library+2 locale tests,5516 data PASS/3164 optional pycountry SKIP, actual US/BR/PT Shift/registry;411 ELFs unchanged. Headless xkbcomp1.5.0 SDK independently owned0/0; no X server/GUI acceptance.
- Owned PCI/DRM/PyYAML prerequisites0/0: DRM13PASS/2deviceSKIP77, native API/invalid-FD checks; PyYAML1283 pure-backend cases and safe-loader refusal. Duplicate GCC staging custody reclaimed3.82GB; native compiler/source/tests/recovery unchanged.
- Owned Mesa26.1.7 reference software/virtual Wayland EGL/GBM and Epoxy1.5.10 dispatch0/0; actual shaders/triangle/RGBA0,32,64,255 pixel staged/installed. Mesa48 upstream drivers qualified43+5 recovery,1266ELFs unchanged; Epoxy4portable tests. No native GNOME/window/physical GPU acceptance.

Running: No guest writer after owned Mesa/Epoxy install/post0/0; continuing GdkPixbuf2.44.7 image/GI and frozen librsvg/GTK prerequisites.

Remaining:

- Pinned incremental desktop dependencies and first working native GNOME session.
- Minimal apps/branding/offline usability, security/ABI review and reference guest measurements.

[Acceptance evidence](docs/evidence/B02.md)

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
| [B01 — Freeze the minimal Toddy architecture and delivery slices](stories/B01.md) | agentic | 5 | completed |
| [B02 — Deliver the minimal branded GNOME desktop](stories/B02.md) | agentic | 10 | in_progress |
| [B03 — Connect provider adapters and one optional local AI profile](stories/B03.md) | agentic | 8 | completed |
| [B04 — Deliver native tools and the revocable privileged executor](stories/B04.md) | agentic | 8 | blocked |
| [B05 — Persist tasks and recover interrupted system changes](stories/B05.md) | agentic | 10 | not_started |
| [B06 — Deliver Toddy quick entry, native UI and first-run setup](stories/B06.md) | agentic | 10 | not_started |
| [B07 — Deliver inspectable local memory and portable backup](stories/B07.md) | agentic | 8 | not_started |
| [B08 — Deliver quiet health monitoring and one persistent automation](stories/B08.md) | agentic | 8 | not_started |
| [B09 — Deliver optional push-to-talk and spoken Toddy responses](stories/B09.md) | agentic | 5 | not_started |
| [B10 — Deliver a bounded plugin interface and one MCP integration](stories/B10.md) | agentic | 6 | not_started |
| [B11 — Integrate the navy brand and nerdy Toddy installer scenes](stories/B11.md) | agentic | 8 | not_started |
| [B12 — Deliver guided offline installation and optional software setup](stories/B12.md) | agentic | 9 | not_started |
| [B13 — Deliver the basic-tested experimental owner preview and G2](stories/B13.md) | agentic | 5 | not_started |
