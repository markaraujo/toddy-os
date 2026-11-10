# ADR-0182: Owned minimal GNOME Shell and probe-only recovery

Status: native package/CLI/GI/private settings accepted; real graphical session pending.

Use frozen GNOME Shell50.4 source SHA256
`c531939539db316a41aef23670370abd1330d3254f84bcb0f9f4dae5d6e362cf`.
Read actual source/options and frozen BLFS13.1-systemd
`gnome/gnome-shell.html`. All central native SDK dependencies and actual Mutter18
font support were measured before preparation; Mutter's selected profile has no
XWayland. Apply exactly the book's GCC16 const callback correction, with before/
after hashes retained. Never upgrade the accepted foundation to bypass a build.

Select full Shell Wayland/Systemd/NetworkManager/PipeWire camera integration.
Keep the book-supported optional extensions tool disabled (no autoar dependency),
and optional Extensions management app disabled for the minimal app set. Omit its
otherwise unconditionally installed launcher during package preparation, with exact
hash receipt. Core Shell/extension APIs remain; no unbuilt app advertised. Omit the
optional WebKit captive portal helper; actual upstream network.js fallback opens
the default browser. The browser itself and this flow remain unqualified until
native graphical application/network checks. Bluetooth/provider capabilities without
qualified runtime dependencies are not advertised. Bundled libshew/GVC are already
in the authenticated archive, no dependency download or new framework.

The frozen book uses tests=false for bootstrap. Upstream original display tests
require native Wayland/Mutter test infrastructure; this profile registers zero,
NOT a passing original suite. They and real native interaction remain pending.
Actual read-only-input/unprivileged/no-route compilation and staging completed:
128ELFs and149regular stage files. CLI reports GNOME Shell50.4. Actual Shell/St GI
type/weekday, unchanged source Params through native GJS, and private schema/memory
roundtrip/reset checks qualify only those bounded scopes.

Initial own probe failed because Gio.SettingsSchemaKey.range_check is not a
variant type validator for unrestricted values. Correct the probe to check the
actual declared type through Variant.is_of_type; no expected range is loosened.
The wrong type is detected before any setting write; this is NOT a recorded failed
GSettings.set_value call. Probe2 passed with all128ELF and149stage hashes unchanged;
retain the initial failure/probe and exact corrected script/job bindings. No
compiler/stage/original suite replay. Two Params override/unknown-parameter refusal/
explicit-extra/recovery cycles and two private favorite-app reset cycles passed.
The private schema count94 covers fixed-path schemas only, not relocatable totals.
Stock cache/real desktop acceptance is not inferred.

Native installation/post0/0 changed343paths, owns547entries; archive
`24ba0f62ee26176c866649ff36b0c1ff91fd090bb82ee8c39811763bfd316bd9`.
Actual installed CLI and UID101 GI/source-JS/private schema checks passed; source
fixture copied with accepted hash. Package audits0, no service manually started,
no owner preferences modified. Retain exact root/bundled named licenses and
leading C/header/JS notices; per-file conditions prevail.
[Source, unchanged artifacts, recovery, native transaction and raw evidence](../evidence/B02-gnome-shell-install.json).

Next: controlled GTK-owned stock schema union for NMA/GDM/GSD/Shell preserving
all prior82schemas/623keys, then actual GDM/userdb/PAM/keyring/permission/login,
GNOME basic applications, keyboard/focus/accessibility/network/audio/offline and
resource gates. No B02 acceptance criterion is completed by this package alone.
