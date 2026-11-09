# Toddy OS — Current status

Updated: 2026-11-07

Bootstrap: ready_for_development

B01 and B03 accepted (13% weighted Phase2). B02 native GNOME dependency implementation in progress; native graphical desktop/login/basic applications and B02 acceptance remain pending. B04 final runtime integration blocked; B05–B13/G2 and physical validation pending. Owner requests stopping after fully validated B02.

Foundation: **100%** · Agentic desktop: **13%**

G1: passed · G2: pending · Next: **B02**

No milestone earns credit without completed acceptance evidence.

## Active story: B02 — Deliver the minimal branded GNOME desktop

The 13% phase total counts completed stories only. B02 is still in progress; its 10 points are not yet counted. Passing this story would raise the phase total to 23%.

Last verified: 2026-11-09T06:59:41.325814+00:00

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
- Owned GdkPixbuf2.44.7 native23 tests and real image/GI/generated-cache0/0. Frozen cargo-c/librsvg dependency sources418+352 authenticated without host compilation; owned build-only cargo-c0.10.24 native25tests/11C-ABI checks0, installed recipe/post0/0. SVG/GTK acceptance pending.
- Owned SVG2.62.3 renderer/Gdk cache0/0, real C+GI SVG/PNG pixels/refusal; original1of1365Rust golden failure retained under source-backed Pango geometry exception ADR0134/144ELFs unchanged. Owned TIFF4.7.2 native156tests/image APIs0/0, no Gdk TIFF loader/window acceptance.
- Owned ISO Codes4.20.1 native data/Portuguese gettext0/0 and715actual source-file UTF8 checks; original bare-domain driver empty-glob caveat retained. Bounded3GiB regular-file GTK compiler volume verified in disposable builder; no target repartition/physical disk change.
- Owned GTK4.22.4 Wayland bootstrap native30headless cases/C-GI/schema0. Original install0/post1 GTK3-name assertion retained, corrected GTK4 namespace postcheck-only recovery0/0/full installed payload unchanged; no window/GNOME/media acceptance.
- Owned native Hicolor0.18/Adwaita icons50/GSettings schemas50.1 and controlled GTK2 schema/legal-only upgrade0/0. Actual52schemas/fonts/GI/icons/SVG/cursor data0; all other GTK runtime payload unchanged. Original plain-C enum probe failure retained/probe-only recovery0,938stagefiles unchanged.
- Owned native Doxygen XML role, optional libxml2 Python48cases, Itstool64cases and Libxmlb56cases qualified. Original failures and narrowly affected recovery results retained.
- Owned Libfyaml native535+286cases/private Check9CTest and AppStream8drivers/C+GI passed. Owned LibSass27C++cases and Sassc4CLIchecks passed; Libadwaita staged/version1.9.3, all67widgettests await native display.
- Controlled virtual target free-block trim and source-only archive custody complete, target/full pending cache identical. Original GI1.86 DBus declarative types compiled/owned0/0; no GUI acceptance.
- Owned full ATK/AT-SPI2.60.6 core/bridge0/0: nine original drivers qualified (seven reused, two real private-bus recovery), staged/installed C/GI states0 and163compiledELFs unchanged. No GNOME/session acceptance.
- Owned LCMS2.19.1 native testcms0/5.59s and ICC serialize/reopen/navy identity/refusal0. Original install0/post1 source-version assertion retained; verify-only0/0/full payload unchanged, no reinstall. Glycin307-crate closure source-verified only.
- Accepted foundation Libseccomp archive/full payload reused unchanged; actual installed child-only syscall refusal0, no reinstall. Additional source7928+11passes retained separately. Hwdata0.410 owned0/0, five byte-identical UTF8 tables/PnP2557 unique names; no device support claim.
- Actual native7.1.8/Systemd sandbox0 on4CPU/4GiB BIOS/noNIC; bwrap26portable+66native upstream passes/5explicit optional skips, native consumer0,11ELFs unchanged. Checksum-reconciled split serial marker without native replay; owned0755 byte-identical install/post0/0. Builder/same3scratch volumes restored, no formatting/trim.
- Owned display-info0.4.0 install/post0/0/all68registered EDID fixtures0, actual QEMU/PnP/malformed+truncated refusal0; both parser/hwdata source-license inventories retained. No physical monitor or graphical-session acceptance.
- Owned libei1.6.0 C6drivers237case executions/schema0 and libinput1.31.3 ten portable drivers0; both install/post0/0. No portal/device/physical/GNOME acceptance.
- Owned ALSA1.2.16.1 install/post0/0, original LSB config/MIDI2PASS and null PCM480frames@48000Hz API0; no audible-device claim.
- Owned Pipewire1.6.8 original50drivers/private IPC0; install0/post1 retained, full payload/archive verify-only plus actual installed UID101/caps0/NNP daemon-client0/daemon stopped0, changed_paths0. No audible/session routing acceptance.
- Owned Lua5.4.8 shared library/basic upstream suite/final OK/C API and interpreter UTF8 installed0/post0; original patch/probe/legal failures retained and narrowly reconciled, no suite/library replay.
- Owned Wireplumber0.5.15 install/post0/0,53original drivers/C/CLI0; minimal native profile, POT output-only correction preserves135ELFs. No audible/native session routing acceptance.
- Owned libnotify0.8.8 install/post0/0, native C/GI and empty private-bus ServiceUnknown refusal0; optional original mocks unavailable/not passes, no displayed notification.
- Owned GUdev238 install/post0/0, unchanged original environment tags1case/C/GI0, no sysfs/device exposure. Three umockdev suites unavailable/not passes; no actual device/event acceptance.
- Owned libwacom2.19.1 recipe/post0/0,8original data/CLI drivers and8725Ccases0; optional Python tool/suites omitted, Git SKIP77 not pass; no physical tablet/hwdb acceptance. GTK3.24.52 Wayland bootstrap source/stage4RGBA/C/GI/private schema0, not installed or display-qualified.
- Owned GTK3.24.52 and GTK4 schema/legal-only toddy3 upgrade recipe/post0/0:56fixed+6relocatable schemas/461defaults/11IM metadata0,624oldGTK4regular files unchanged. Owned GNOME Desktop44.5 source/bg/languages/C/GIR and install/post0/0; no actual graphical/session acceptance.
- Owned JSON-GLib1.10.8 install/post0/0,17original unit/conformance drivers/570TAPcases0/skips0 and C/GI/parser-refusal0; no UI/network/service acceptance.
- Owned Ogg1.3.6 recipe/post0/0, original bitpack/framing2PASS and packet/page/CRC-refusal C0; no audible output acceptance.
- Owned Vorbis1.3.7:528original codec roundtrips/C0,149stagefiles unchanged after documented callback macro correction; install0/post1 direct-link omission reconciled verify-only0/0 changed_paths0, no reinstall/audio claim.
- Owned libsndfile1.2.2 original old-Automake audio-file/header tests and exact WAV C0; summary-only recovery/no replay; unsupported external codecs explicitly not passes.
- Owned PulseAudio17 client-only libraries/tools0/0,12original drivers0; private staged indirect-library lookup recovery preserves105stagefiles. No Pulse daemon/autospawn/device audio claim.
- Owned Canberra0.30 ALSA/Pulse/null modules0/0; native null callback/cancel/state/refusal0, no original suite or audible output. Exact LGPL/header notices retained after bounded preinstall legal-stage recovery.
- Owned libusb1.0.30 options/init drivers/C no-discovery/refusal0/0; stress and umockdev omitted, no physical USB acceptance.
- Pulse17.0/Canberra0.30 legal metadata upgraded to toddy2 with complete LGPL/GPL;105Pulse/25Canberra nonlegal files unchanged, native C/refusal0/0; no compile/upstream replay.
- Owned GUsb0.4.9 original API map/2ID+JSON fixture cases/C/GI0/0,21stagefiles unchanged by final probe. Upstream optional polling getter bug explicitly unqualified; no physical USB claim.
- Same-version Systemd261.2-1+toddy2 owns qualified40-input hardware database;2119old nonlegal files unchanged. Native vendor/refusal/API/CLI0 and corrected launch-only original Colord EDID0; verify-only0/0 changed_paths0, no source rebuild or hardware claim.
- Owned Colord1.4.8 client/ICC bootstrap0/0,38distinct original cases across verified partitions/76ELFs unchanged; original failed monolithic run and generated-data SKIP retained. Native RGB ICC/refusal/GI0; no privileged color service/sensor acceptance.
- Owned Docutils0.23 install/post0/0,4original man writer cases/API/CLI/include-disabled consumer0; private source-required Flit3.12 backend leaves foundation4.0.2 unchanged. Build tooling only.
- Owned unchanged GI1.86 GL namespace declarations/compiler/typelib import0/0,13record definitions; no legacy GL invocation/provider/GPU claim/core rebuild.
- Mutter50.4 source bootstrap0: GVDB+four original Mtk programs15cases/CLI/GI/private schemas0;211previous compiled ELFs unchanged after exact GL declaration prerequisite, no actual compositor/display claim.
- Owned Mutter50.4-1+toddy1 and existing GTK4 schema/legal-only4.22.4-1+toddy4 upgrade0/0:624oldGTK4regular files unchanged, actual global61fixed+6relocatable schemas/39new defaults0, including pending Colord ColorHelper. No user preferences/GTK4 rebuild/GUI acceptance.
- Actual native7.1.8/Systemd headless Mutter50.4 Wayland GTK window/action/resize/render0;67original Libadwaita drivers408cases0/no skips,69artifacts89source files unchanged. Active compositor focus and full GNOME/login/basic apps remain pending.
- Owned Libadwaita1.9.3-1+toddy1 install/post0/0; native C/GI ABI/APT0. Original prewrite qualification selector failure retained, no rebuild or suite replay.

Running: No writer. Next GtkSourceView5.20 dependency for basic editor; full GNOME/login/apps/network/audio/offline/security/measurements pending. Complete ALL B02 then pause.

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
