# ADR-0184: First native Shell failure and actual runtime prerequisites

Status: first native Shell interaction attempt failed; dependency work continues.

Committed probe inputc295dc5e0a2d85598d510248f298275e0c0ce582 boots a fresh disposable
no-NIC overlay with actual7.1.8-toddy/Systemd and installed Shell/Mutter50.4/GTKtoddy8.
Before boot, verify3016native package files and actual current versions. Use
UID101, a private user bus, actual headless Wayland1280x720/software rendering and
source-supported automation/perf helper; no unsafe-mode or simulated screenshot.
This is a first compositor/Shell interaction gate, not authenticated GDM/session
or required basic-app acceptance. Never boot an older overlay after parent changes.

Actual Wayland surfaceless renderer/virtual monitor/a11y registry initialized.
The automation was never reached by150s; no actions/PNG were produced. The owned
process group was terminated and waited for; timeout is NOT success. Native report
SHA256 `71d9c11c82ad568277593678e89484e969d7577049f844b7cac7baaec3fa6647`
records failure. Actual child exited0/OOMfalse after poweroff; backing identity
unchanged verified BEFORE builder restart. Child runtime success does not turn the
failed Shell test into a pass.

Observed diagnostics: Gst1.0 typelib missing causes actual Screencast service
exception; UID101 lacks a registered logind user, preventing a login-user-backed
state machine; required Settings application absent. Colord daemon was deliberately
unselected by the prior bounded client profile, so no colord.service exists. Audio
connection and camera monitor are unavailable. No GDM registration exists in this
standalone probe. These are real incomplete runtime integrations. The precise
startup wait preventing automation has NOT yet been isolated; do not claim one
warning alone proves its cause or repeat unchanged inputs.
[Actual report, logs, terminal state and recovery](../evidence/B02-shell-first-native-failed.json).

Restart verified builder, restore only the six existing scratch filesystems and
same authenticated Systemd source bind; no trim/format/recreation. New builder
bootb4a89c17-0d00-43c2-ad3a-a90982468c85, source7193files verified. One temporary
restore command's string quoting failed Python parsing before execution; corrected
with a raw literal and compile preflight before the actual restoration. Its log
is retained. No uncertain state mutation was repeated.

Next actual prerequisite: frozen BLFS13.1-systemd multimedia/gstreamer10.html
GStreamer1.28.6. Official HTTPS archive matches the frozen MD5 and is pinned before
guest extraction to SHA256
`62b6b9f0ad3147a6dd6420ac64a91180b14e990695bddd353b96041611d052ca`.
Select core/Check/original tests/CLI/GI, book gst_debug=false, preserve API checks;
omit optional privileged PTP helper, examples/benchmarks/docs/backtrace extras.
Original network-clock tests use an isolated loopback-only namespace with no
external route. Own typed caps/buffer, missing element refusal and two fakesrc/
fakesink EOS→NULL cycles test synthetic pipelines only. No codec/hardware/audio/
PipeWire screencast claim until those consumers are actually supplied/verified.

Continue other required basic-app/runtime dependencies and actual PAM/logind
session integration before a new native attempt with new inputs. Preserve the
failure ledger across compaction; do not repeat accepted PAM/GJS/Mutter suites,
reduce GUI requirements or mark B02/G2 complete. Complete all B02, then stop.

## Actual core prerequisite result

GStreamer core build/stage completed406ELFs/213regular files with original107OK
programs. One original validate.simplest is SKIP because optional gst-validate is
absent; not a pass, raw stdout retained. Actual GI caps/buffer/missing element
refusal and two synthetic fakesrc/fakesink EOS→NULL cycles passed. No original
replay. Native install/post0/0 changed565paths, owns670entries, archive
`e51ed504763515f4f607255d2f77d588bcf8820e8608f1590153418d4fcef9e0`.
Installed UID101 GI/synthetic pipelines/private no-route namespace/SDK/APT0;
private registry removed. The Gst typelib dependency is supplied. This does not
prove real multimedia devices/codecs/GNOME screencast or resolve the unisolated
startup wait. [Actual owned core proof](../evidence/B02-gstreamer-install.json).
Base1.28.6 source frozen/cached, not built. Continue prerequisites before native retry.
