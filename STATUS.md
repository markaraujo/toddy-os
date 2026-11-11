# Toddy OS — Current status

Updated: 2026-11-11T11:27:48.350438+00:00

Bootstrap: ready_for_development

B01/B03 accepted (13% weighted Phase2). B02 corrected Firefox153.7 built/staged/installed; owned payload/APT/UID101 version/desktop entry verified. GDM/default graphical boot configured with native links; actual default-boot/browser GUI/sandbox/TLS and integrated audio/theme/offline/reboot/resource gates remain pending. Stop after fully validated B02. No Phase2 ISO or physical acceptance.

Foundation: **100%** · Agentic desktop: **13%**

G1: passed · G2: pending · Next: **B02**

No milestone earns credit without completed acceptance evidence.

## Active story: B02 — Deliver the minimal branded GNOME desktop

The 13% phase total counts completed stories only. B02 is still in progress; its 10 points are not yet counted. Passing this story would raise the phase total to 23%.

Last verified: 2026-11-11T13:50:36.822472+00:00

Verified:

- Normal native GDM/PAM Wayland owner login, Files local navigation/Trash restore, Editor open/type/save/relaunch and Settings navigation have real retained scanouts.
- Native NetworkManager Settings wired on/off/reconnect, DHCP/DNS/HTTPS and active-client polkit checks passed; manager recovery passed in disposable guest. Restored-manager reboot persistence remains pending.
- Installed Firefox153.7.0esr native open/input/navigation/process exit-reopen/profile persistence/Stop/TLS/offline/640px readability and five content-process NNP/seccomp/caps checks passed; original collector failure retained and reconciled read-only.
- Owned navy desktop/launchers/Terminal defaults preserve user overrides across new D-Bus/reset. Actual native navy overview/Terminal commands/Portuguese text/tiled view and PipeWire/Pulse/WirePlumber HDA playback/mute/unmute passed with non-silent QEMU WAV capture.
- Actual candidate BIOS+UEFI no-disk boots passed FUSE module/UID101 device open/direct mount denial/unload plus Landlock9/seccomp/namespaces. First no-udev fixture permission failure preserved; correction uses exact owned Systemd FUSE0666 rule only in volatile diagnostic.
- Native linux-kernel7.1.8-1+toddy2 installed and full payload/Kmod lookup/APT checked. Coupled boot-config0.1-2+toddy2 retains exact menu/recovery bytes; original kernel0/post1 reverse-pin failure retained and resolved without kernel reinstall. Actual installed boot pending.
- Fuse3.18.2-1+toddy1 native install2 recipe/post0/0,40owned paths, exact reviewed root SUID helper/default owner-only policy and UID101/NNP CLI/library API pass. First unreviewed-privilege rejection0rootchanges retained; only declared helper added to central policy. Real mount/signals/denial/unmount recovery pending.
- Unmodified upstream hello/signals consumers compiled against installed libfuse3.so.4, no RPATH/SUID. Portal base1.22.1 compiled/staged/version0 with image+sound Bubblewrap validation enabled; native portal package/session acceptance pending.

Running: No guest writer remains. Portal base build1 is terminal0. Next install its verified stage, build/install GNOME50.0 and GTK1.15.3 backends, update only owned shared schema cache, then combine real FUSE mount/helper/signals and portal appearance/consent checks in one native VM session. Complete all B02, then stop.

Remaining:

- Boot the installed FUSE-enabled kernel in the reference guest; execute prepared real filesystem/signals/other-user/allow_other denial/unmount/recovery tests.
- Own the compiled portal base, build/own GNOME/GTK backends and shared schema cache, then verify actual dark/light and affected portal consent/cancel/denial.
- Finish restored NetworkManager and file/editor persistence across reboot, affected refusal/recovery and recovery-entry boot.
- Publish exact minimal runtime manifest/optional catalog availability and reference desktop idle/resource measurements; separate build target from deliverable roots.
- Complete applicable S01-B/S02/S03 desktop scope, including absent-agent/offline operation. Physical hardware, Phase2 ISO and G2 remain unaccepted.

[Acceptance evidence](docs/evidence/B02-portal-base-build.json)

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
