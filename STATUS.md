# Toddy OS — Current status

Updated: 2026-11-11T14:47:01.279729+00:00

Bootstrap: ready_for_development

B01/B03 accepted13%; B02 actual native desktop/FUSE/portal/offline Editor refusal/crash recovery/idle/coldboot persistence/NM/recovery-entry evidence passed. Required Git2.55.0 missing from actual inventory; implement before final runtime manifest/catalog/B02 acceptance. Finish B02 then stop; no Phase2 ISO/G2 or physical acceptance.

Foundation: **100%** · Agentic desktop: **13%**

G1: passed · G2: pending · Next: **B02**

No milestone earns credit without completed acceptance evidence.

## Active story: B02 — Deliver the minimal branded GNOME desktop

The 13% phase total counts completed stories only. B02 is still in progress; its 10 points are not yet counted. Passing this story would raise the phase total to 23%.

Last verified: 2026-11-11T14:47:01.279729+00:00

Verified:

- Normal native GDM/PAM Wayland owner login, Files local navigation/Trash restore, Editor open/type/save/relaunch and Settings navigation have real retained scanouts.
- Native NetworkManager Settings wired on/off/reconnect, DHCP/DNS/HTTPS and active-client polkit checks passed; manager recovery passed in disposable guest. Restored-manager reboot persistence remains pending.
- Installed Firefox153.7.0esr native open/input/navigation/process exit-reopen/profile persistence/Stop/TLS/offline/640px readability and five content-process NNP/seccomp/caps checks passed; original collector failure retained and reconciled read-only.
- Owned navy desktop/launchers/Terminal defaults preserve user overrides across new D-Bus/reset. Actual native navy overview/Terminal commands/Portuguese text/tiled view and PipeWire/Pulse/WirePlumber HDA playback/mute/unmute passed with non-silent QEMU WAV capture.
- Actual candidate BIOS+UEFI no-disk boots passed FUSE module/UID101 device open/direct mount denial/unload plus Landlock9/seccomp/namespaces. First no-udev fixture permission failure preserved; correction uses exact owned Systemd FUSE0666 rule only in volatile diagnostic.
- Native linux-kernel7.1.8-1+toddy2 installed and full payload/Kmod lookup/APT checked. Coupled boot-config0.1-2+toddy2 retains exact menu/recovery bytes; original kernel0/post1 reverse-pin failure retained and resolved without kernel reinstall. Actual installed boot pending.
- Fuse3.18.2-1+toddy1 native install2 recipe/post0/0,40owned paths, exact reviewed root SUID helper/default owner-only policy and UID101/NNP CLI/library API pass. First unreviewed-privilege rejection0rootchanges retained; only declared helper added to central policy. Real mount/signals/denial/unmount recovery pending.
- Unmodified upstream hello/signals consumers compiled against installed libfuse3.so.4, no RPATH/SUID. Portal base1.22.1 and GNOME50.0/GTK1.15.3 backends now compiled/staged and owned-installed with recipe/post0/0. Base image/sound Bubblewrap validation enabled; GTK Settings/AppChooser/Lockdown enabled. Native desktop integration pending.
- GTK4.22.4-1+toddy14 owned schema/legal-only update recipe/post0/0; all runtime bytes preserved,132schemas/1113keys preserved and2portal schemas/1key added. Actual installed Gio default-source134schemas/1114keys checked; no user values changed.
- Combined native context3 passed: actual installed kernel config, normal GDM/PAM owner, real FUSE owner/helper mounts/other-UID denial/default allow_other refusal/unmount/SIGTERM8 cleanup/upstream signals0; portal dark-light-dark1/0/1 and real chooser allow0/cancel1/Close0+object removal. Context1/2 fixture failures preserved, passed helper results reused. Real scanouts retained.
- Native offline Editor refused protected save after polkit cancellation; original unchanged. Actual29B autosaved draft before sole-process SIGKILL, Document Restored/SaveAs exact29B SHA verified; idle15second sample without agent/inference. Later distinct coldboot preserves file/user teal+dark and restored NM DHCP+DNS. Owned GRUB recovery selected by actual keyboard; running original foundation config/data/network verified. Earlier fixture/collector failures retained and corrected without OS rebuild/replay.

Running: All native jobs stopped; builder remains stopped. Next install required pinned Git2.55.0 (missing in actual359package inventory), then minimal runtime manifest/optional app status and final B02 audit. No new Git job dispatched yet. Finish all B02 then stop.

Remaining:

- Build/own/qualify pinned Git2.55.0 in the offline base; actual native inventory currently lacks Git despite selected plan root.
- Publish exact minimal runtime manifest and optional catalog availability, bind real idle/resource measurements to reference guest.
- Audit all B02 desktop S01-B/S02/S03 criteria and evidence. Physical hardware, Phase2 ISO and G2 remain unaccepted.

[Acceptance evidence](docs/evidence/B02-editor-persistence-native.json)

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
