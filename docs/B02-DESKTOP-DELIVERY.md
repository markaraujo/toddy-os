# B02 — Reference desktop delivery

B02 is accepted for the tested native reference guest. This is a desktop-stage
delivery, not the Phase 2 installable ISO, assistant release or G2 acceptance.
B01/B02/B03 total **23% of the weighted Phase 2 plan**. The owner requested that
execution stop after all B02; no subsequent story is started by this delivery.
Physical foundation testing remains unperformed.

## Delivered behavior

The source-built minimal GNOME 50/Wayland desktop boots to normal GDM/PAM login.
Actual virtual keyboard/tablet input, Firefox 153.7.0esr, Files/Trash restoration,
GNOME Terminal, Text Editor and Settings were exercised in native sessions.
NetworkManager wired controls, DHCP/DNS/HTTPS, active-user policy, fallback and
restoration were checked. PipeWire/Pulse/WirePlumber played a non-silent virtual
HDA sample; mute/unmute changed actual state. Navy defaults preserve user edits.
The original approved logo/mascot masters are unchanged; B11 branding remains a
separate runtime story.

The installed FUSE kernel/helper mounted a real user filesystem, refused another
user's access/unmount and default allow_other, and cleaned up on owner unmount and
SIGTERM. Native portal appearance followed dark/light/dark; the real GNOME file
chooser returned the selected URI, cancelled without a URI and removed a closed
request. These checks do not qualify every portal or a Flatpak deployment.

Offline Text Editor refused a protected save after administrative authentication
was cancelled. An actual autosaved draft survived a deliberate sole-process crash,
was shown as restored and was saved with exact observed bytes. Later cold boot
preserved that file, the protected original, custom teal/dark preferences and
restored NetworkManager DHCP/DNS. The owned GRUB foundation recovery entry booted
the different preserved kernel configuration and retained data/network operation.

Git 2.55.0 is installed in the base. Its original full test command passed; the shell
aggregate records 31,993 successes, zero failures, 388 upstream known breakages and
454 skipped/prerequisite cases across 1,046 scripts. Actual installed native tests
covered commit/branch/fast-forward/clone/fsck, refusal to overwrite dirty work and
missing-credential prompt refusal. Git also ran in ordinary navy Terminal after a
native boot. No owner Git configuration was changed. Remote SSH/accounts and
generated Git man/HTML documentation are not qualified here; offline plain-text
reference/tutorial files accompany the package.

Tecla 50 displayed the actual US keyboard layout, switched lower/upper symbol
levels and closed normally. Its upstream fixed 800×400 dialog remained fully
visible at 1280×800; Super+Left did not resize it. This is not a 640px resizing claim.
Earlier browser and Terminal narrow-window evidence remains applicable.

## Measurements and inventory

The desktop sample uses QEMU/KVM, 4 vCPU, 4 GiB, virtual graphics/HDA and no GPU
passthrough. The separate B01 local-model reference uses 8 GiB. The observed login
screen was available within **28.6 seconds** of container/QEMU start, below the
45 second target; this is a conservative first-frame upper bound, not an instrument
for earliest appearance. Guest boot was fresh; host filesystem caches were not
flushed. Systemd's 4.457 second kernel/userspace accounting is not login latency.

A 15 second, three-sample offline idle observation with Editor closed and no active
agent/inference measured at most **408.273 MiB** using MemTotal minus MemAvailable,
below the 2 GiB desktop budget. Aggregate four-CPU non-idle time was 0.0333%. This is
not a physical benchmark or the future B06 service's 60 second budget.

[Observed runtime manifest](evidence/B02-desktop-runtime-manifest.json) records
360 installed integration packages and a foundation/desktop dependency
projection of 308 packages. The 134 package accepted foundation is retained. Required icons, fonts,
GVFS and portals are explicit roots. Exact versions, native archive/recipe/source
hashes and verified owned legal documents are included. Another 52 integration
packages are listed for B12 composition review, **not approved for blind removal**.
No composed image size or installable Phase 2 artifact is asserted. Source caches
and B01 prototype tools are development material, not mandatory desktop AI/model
installation. The runtime projection excludes agent/inference/Node/Qt/Rust roots.

[Optional packaging definitions](../config/phase2/optional-app-packaging.json)
reference the existing OpenCode/VS Code catalog IDs and retain unavailable status.
Origins, candidate owned paths, distinct source/product/marketplace terms and
update/remove qualification requirements are recorded. Mutable download endpoints
are not pinned releases; no remote installer was run, legal acceptance invented,
brand silently substituted or optional software advertised as working. Other
unqualified catalog candidates also remain unavailable; mise is excluded.

## Evidence, use and continuation

- [Criterion audit and evidence index](evidence/B02-acceptance.json)
- [Native final keyboard/Git session and real scanouts](evidence/B02-final-native-desktop.json)
- [Native FUSE/portal behavior](evidence/B02-fuse-portal-native.json)
- [Offline Editor, cold-boot persistence and recovery](evidence/B02-editor-persistence-native.json)
- [Measurements and methods](evidence/B02-desktop-measurements.json)
- [Git original/native tests and qualified cache custody](evidence/B02-git-native.json)

The retained native disks contain disposable fixture accounts. They are evidence
and recovery inputs, not a personal installation image. Existing controllers
reject context replay: inspect the checkpoint and actual postconditions before
resuming; do not remove their guards to rerun writes. `make check` validates the
repository, not physical hardware or a new installed release.

The [continuation card](PHASE-2-CHECKPOINT.md) preserves cold disk identities,
qualified cache custody and the exact next action. B04 has retained headless proofs
and remains unfinished; B02 now supplies its native prerequisites. Resume only on
owner instruction. B04–B13/G2, final composition/installer/ISO/checksums and release
handoff remain part of the full Phase 2 objective.
