# ADR-0211 — Colord GTK and owned dependency preflight

Status: accepted for B02's scoped library/API qualification.

## Decision and actual implementation

Use frozen BLFS13.1-systemd colord-gtk0.3.1 with both GTK3 and GTK4 libraries,
GTK3 introspection, and original display tests compiled. The source generates no
GTK4 GIR. Optional documentation/man are disabled following the book. Optional
Vala is unavailable because the owned Colord SDK has no colord.vapi; Control
Center consumes the C ABI, so keep both GTK libraries/GI and omit that binding.
No parent rebuild, panel removal or source-library patch is needed.

[Build/stage](../evidence/B02-colord-gtk-stage.json):17ELFs/15regular stage files.
Initial build failed only at vapigen after C/tests/GIR compilation. Incremental
configure removed Vala while all original ELF bytes remained identical; staging
completed. Its own consumer then exposed the shared __CD_VERSION_H guard between
Colord and Colord GTK: including the umbrella header masks the GTK version macros.
Preserve that public-header limitation. Correct only the own probe to use local
GObject/profile-empty state, and verify version through authenticated source and
actual pkg-config. Consumer/collection-only3 passed with compiler/stage unchanged.
The normal fresh recipe uses these choices directly, without recovery fixtures.

Both original tests require real GTK windows and a display profile. They remain
unexecuted, not passing. Actual staged and installed C consumers separately load
GTK3 and GTK4, create local non-widget CdWindow objects, inspect empty profile
state and signals, and repeat two fresh lifecycles without service/device access.
GTK3 GI, shared-library resolution, exact payload/version and APT passed under
UID101/NoNewPrivs/private-device/no-route. This does not accept widgets, profile
mapping, calibration, a Settings panel, a real display or physical hardware.

## Native metadata correction and prevention

[Native receipt](../evidence/B02-colord-gtk-install.json) retains the first
incorrect exact GTK3 dependency: revision1 was declared while actual owned GTK3
is revision2. Dpkg safely left Colord GTK unpacked. A guarded metadata-only
Colord GTK revision2 upgrade corrected the dependency, preserving original
source/compiler/stage/archive and installed payload. Recipe/post0/0, three paths
changed. No compiler/source/stage replay or global security changes.

This repeats a known class of hand-written dependency-revision errors. Add a
read-only dependency preflight to the Phase2 generic promoter before promotion,
archive or unpack writes. Require actual installed state and native dpkg version
comparison, support explicit alternatives, and reject unsupported syntax.
Four focused safety tests cover stale exact revisions, unpacked state, owned
alternatives and unsupported syntax. [Actual native proof](../evidence/B02-dependency-preflight.json)
accepts the owned GTK3/Colord versions and refuses stale GTK3 revision1 with the
dpkg status bytes unchanged. Foundation recipes and full-root checks are retained.

## Next Settings dependencies

Recursive source Meson/native pkg-config preflight still requires libgtop,
UDisks, MIT Kerberos, CUPS and Samba libraries. Keep core panels and qualify the
selected frozen leaves incrementally. Embedded libgxdp is already in the
authenticated Control Center archive; optional gmobile/malcontent and GTK-X11
are not prerequisites of the selected reference Wayland profile. This is not
complete Control Center or full desktop acceptance.
