# ADR-0181: Owned SettingsDaemon and scoped private power tests

Status: selected native package/CLI/private schema checks accepted; real session pending.

Use frozen GNOME SettingsDaemon50.1, SHA256
`dd2c9730914f0ececa0229dd8a8c2940a57ddeb0802434558d4b164d79cfe05c`.
Actual required owned dependencies were measured before preparation: GNOME Desktop4,
GLib, GSettings Desktop50.1, Geocode API2, GWeather4, GeoClue2, Canberra, Notify,
Pulse mainloop, Polkit, UPower, Systemd, GUdev, Gck2/Gcr4, Colord, NM and ALSA.
Keep mandatory Linux Systemd/ALSA/GUdev/NM/rfkill plus selected smartcard/Colord/USB
protection. Omit supported optional CUPS/WWAN/XWayland paths; no baseline upgrade,
new desktop framework or hardware availability claim. Bundled GVC source is already
in the authenticated archive; no compiler network download or duplicate build tool.

Read-only-input/unprivileged/no-route compilation passed263tasks and134ELFs;
156regular files staged. All11registered original programs passed with no observed
nested skips: two C color/timezone drivers and nine private power programs containing
26Python unittest cases. Power tests run real GSD and a real dummy GNOME SessionManager
with private DBus mock Mutter/logind/UPower/screensaver/provider services. They are
fixture evidence, NOT physical suspend/battery/brightness/audio, a greeter or desktop.
The longest original Unidle program completed144.16s within its150s source budget;
it was progressing and was neither interrupted nor restarted to meet a diagnosis cap.

Own actual private compiled-schema consumer checks24schemas, boolean/uint color
settings, invalid power enum refusal and two memory-only reset/recovery cycles.
Three staged CLI help commands passed. This is not the installed stock schema cache
or a display/power operation. Keep the pending controlled GTK-owned schema union
explicit before native graphical session acceptance.

Initial package50.1toddy1 was unpacked but unconfigured: the own exact dependencies
mistakenly requested Canberra0.30/Pulse17 native revisions toddy1, while the already
qualified libraries used by the compiler were both toddy2. Do not downgrade them or
force dependencies. Verify all458unpacked payload entries/old archive, extract a NEW
identical stage and produce50.1toddy2 with only corrected dependency revisions.
All458payload entries stayed identical. Controlled metadata2 recipe/post0/0 changed
only3root paths; native package is configured. Original failure/archive retained,
no compiler/original/stage replay. Future recipe declares exact qualified audio
revisions and native GSDtoddy2. [Source, originals, metadata recovery and native proof](../evidence/B02-gnome-settings-daemon-install.json).

Actual installed color/power/media-keys CLI/private libgsd resolution, SDK version,
UID101 private24schema/memory enum refusal/reset and package audits passed. These
checks manually activate no service and change no user's preferences. Existing
source schema XML is owned, but no stock cache acceptance is inferred. USB/smartcard
code without qualified providers is not advertised as actual protection/hardware.
Retain exact source GPL/LGPL and bundled GVC notices/leading headers; per-file
conditions prevail. External device/network/provider data is never a privilege
source; source Polkit/systemd/user-unit boundaries remain intact.

Next Shell50.4, a controlled stock NMA/GDM/GSD/Shell schema union preserving prior
82schemas/623keys/preferences, and actual native GDM/userdb/PAM/keyring/permission/
GNOME/login/apps/offline/focus/audio/network/resource gates. B02/G2 remain incomplete.
