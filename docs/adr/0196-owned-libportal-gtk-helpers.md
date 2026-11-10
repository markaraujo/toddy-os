# ADR-0196 — Owned libportal GTK helpers with scoped portal evidence

Date: 2026-11-10
Status: Accepted library/userspace slice; real desktop portal services pending

Nautilus50.2.2 actual SDK preflight requires libportal/libportal-gtk4, alongside
missing gnome-autoar, tinysparql and Glycin's GTK4 helper. Use frozen
BLFS13.1-systemd `general/libportal.html`0.9.1, source SHA256
`de801ee349ed3c255a9af3c01b1a401fab5b3fc1c35eb2fd7dfb35d4b8194d7f`,
page SHA256
`78c367c0833edab73cd00e40f1a733f0d555fb0235b21f3bb21db238ddd6c02c`.
Official HTTPS archive matched frozen MD5 before SHA256 freeze/extraction.

Select shared base library, GTK3/GTK4 parent-window helpers and introspection.
Qt5/Qt6, Vala, docs and manual demo are omitted through supported options. The
book's Qt6.9 patch affects unselected Qt code; no Qt helper is built/qualified.
These GTK helper libraries do not implement the separate real
xdg-desktop-portal/GNOME/GTK services or supply permission grants.

Actual pytest9.1.1/dbusmock0.38.1 and owned GLib/GTK dependencies verified before
preparation. Preserve original selected Python driver and180s budget; assert it
is registered so missing test tools cannot silently remove all tests. Only pytest
cache output is disabled; JUnit/basetemp go to private work, source remains RO.
All61original cases passed/no skips, using private mock portal D-Bus fixtures.
They test client protocol behavior, not actual input/capture/screencast devices,
GNOME consent, desktop service or user authority. Private PID namespace teardown
terminates any leftover fixture daemons noted by the frozen book.

Build/stage0,33compiledELFs/42staged regular files. Own real private-session-bus C
constructor/init/context detection/two construct-release cycles passed. GTK3/GTK4
GI namespaces and actual shared helper symbol loaded in separate Python processes,
respecting incompatible GTK major versions in one process. No window parent
export/widget/display is claimed. No compiler network, source patch, policy/grant,
owner data or unrelated preference change.

Native install/post0/0 changed73paths/76owned entries. Actual installed UID101,
private device/mount/PID/network namespaces, C/bus and separate GTK3/GTK4 GI/helper
symbol/shared ABI/pkg-config/APT0 passed. Target userspace in builder VM, not a
native Toddy desktop boot. Full-root transaction verification retained. No original
suite/compiler replay. Runtime versions are owned/pinned; real desktop portal
service/error/permission/cancel/reconnect integration remains separate B02 work.
Retain exact authenticated LGPL3-only/root and leading runtime/base/GTK notices.

[Source, original cases and native proof](../evidence/B02-libportal-install.json).
Native archive SHA256
`bf6531b67001334177fcb9a18a115e5604d409d774bddab8d6eaf5adffad32cf`;
raw evidence SHA256
`7381ac4b9c3c403485e735cfe2a49415e4640ec37101444eae74ae20bc4328a3`.
Next required Nautilus leaves are gnome-autoar/archive dependencies, tinysparql and
Glycin GTK4. Preserve all accepted library evidence and parked headless-focus
budget; no unsupported backend/catalog item becomes available from this slice.
