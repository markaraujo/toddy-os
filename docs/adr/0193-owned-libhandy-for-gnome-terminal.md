# ADR-0193 — Owned libhandy for GNOME Terminal

Date: 2026-11-10
Status: Accepted dependency implementation; original graphical execution pending

Frozen BLFS13.1-systemd `x/libhandy1.html` selects1.8.3, required by selected
GNOME Terminal3.60.0. Source SHA256
`05b497229073ff557f10b326e074c5066f8743a302d4820ab97bcb5cd2dab087`,
book page SHA256
`ada20fdf1b5083d19e6e7064017ab058cfde27b7a0017f51cafa5624effa08ce`.
Official HTTPS archive matched frozen MD5 before SHA256 freeze/extraction.
Use owned GTK3/FriBidi/GLib with introspection/Vala, release/usr/lib and no network
fallback. Optional examples/demo, Glade catalog, docs/profiling omitted. Retain
exact LGPL2.1-or-later legal text and leading runtime C/header conditions.

Build compiled122ELFs and78staged regular files, including all30upstream
registered test programs. Both frozen book and actual tests require a graphical
session. They remain explicitly deferred, **zero original test passes here**.
Their exact names/binaries are retained for real native display validation;
this package's headless qualification cannot satisfy the B02 GUI criterion.

The own C consumer initially failed134 because it did not initialize the GValue
copy destination. Actual upstream documentation requires the correct destination
type. Probe-only2 initialized G_TYPE_STRING and passed real UTF8/value-copy
independence, take/dup ownership, navigation enum and two reset cycles. Its next
GI step failed because `new_string` is marked introspectable0 in actual Handy1
GIR. GI-only3 uses the supported `new(GObject.Value)` constructor and checks copied
Unicode data survives source mutation. No library source patch, recompile,
restage or original-test replay. Both own failures retained; complete122ELF/
78stagefile hashes unchanged across corrections. Future recipe contains fixes.

Native package install/post0/0 changed120paths/184owned entries; actual installed
UID101 C/GI consumers passed in private no-route namespaces, actual
libhandy-1.so.0 resolution/pkg-config1.8.3/APT audits0. Full-root transaction
verification retained; no existing user preferences modified. Runtime source has
no new privileged service; widget/text/URI behavior still requires affected real
GNOME/Terminal checks. Do not infer complete ABI/security/UI coverage from data APIs.

[Source, failures, pending originals and native proof](../evidence/B02-libhandy-install.json).
Native archive SHA256
`768593bc0a8e3305668c081781f7f6c941bcc01975eb79071aff85c1b99c68a5`;
raw evidence SHA256
`5d6334231569273cc6bf67aeba6b65e386b87360d90e330bcd1c1f978472dca9`.
Next selected app is GNOME Terminal3.60.0; actual launch/window/focus/PTYShell/
settings persistence/Stop/recovery and private-schema/stock-cache integration
remain separate work. Preserve parked headless-focus attempt budget.
