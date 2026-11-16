# Qt 6.11.2 raster Wayland preparation

This source slice corrects the earlier assumption that a missing Wayland QPA
necessarily requires installing the separate QtWayland module. In the frozen
Qt **6.11.2** source, the basic Wayland client, scanner, platform plugin and
xdg-shell integration already live in **qtbase**. No version upgrade is proposed.
The separate official QtWayland archive has been verified and retained for source
custody; it is not selected for this minimal client or added to current package
metadata. It adds compositor and extra integrations (including Adwaita decoration),
which do not supply a missing QtBase client backend.

## Source-backed decision

The existing [source lock](../config/phase2/sources.lock.json) freezes QtBase
6.11.2 archive SHA-256
`5b2e00eccaf5a4d8c14134ffa0ea8dfd0a35ae1ffc7f8d87fa4305a1ed23cf22`.
The inspected paths in that exact archive are:

- `src/gui/configure.cmake`: `wayland` requires Wayland::Client, `waylandscanner`
  requires Wayland::Scanner, and `wayland-client` requires those two features.
  `wayland-client-xdg-shell` requires the client; no OpenGL requirement applies.
- `src/plugins/platforms/wayland/CMakeLists.txt`: creates WaylandClient and the
  `qwayland` platforms plugin; its plugins include xdg-shell.
- `src/plugins/platforms/wayland/qwaylandintegration.cpp`: creates a
  QWaylandShmBackingStore for QWidget backing stores independently of the guarded
  OpenGL context methods. CPU raster does not require rebuilding QtBase with GL.

The QtWayland 6.11.2 `src/client/CMakeLists.txt` only creates a header feature
module. Its client configure file states that the remaining Qt-specific shell and
Adwaita decoration features were not moved to QtBase. Its official archive and
upstream SHA-256 URL are recorded in the additive
[Qt preparation lock](../config/phase2/qt-wayland.lock.json).
The existing B02 dependencies are Wayland 1.26.0, wayland-protocols 1.49,
libxkbcommon 1.13.2 and xkeyboard-config 2.48. Their package revisions are retained
in that lock; no upgrades are needed for the proposed client.

The QtBase B01 recipe disables XCB/OpenGL but does **not** explicitly disable
Wayland. Autodetection may have missed Wayland/xkbcommon when it ran before B02.
B02's retained runtime manifest lists the exact same `qtbase 6.11.2-1+toddy1`
probe package as an unselected integration package. No different production Qt
recipe or qualified Wayland GUI was found. Offscreen/TLS/D-Bus success cannot
answer whether the existing package contains the required QPA. Inspect it first.

## Exact next actions for the sole native coordinator

1. Perform a read-only native inspection or inspect the verified retained package
   extracted into a new private stage. Run
   `python3 scripts/build/phase2/qt_wayland_inspect.py ROOT --require` (add
   `--stage` for an isolated complete stage). Retain the JSON and package custody.
   The helper reads only files/features and never loads plugins or contacts a
   display. Its status is not GUI acceptance. Required files are the exact-version
   Core/Gui/Widgets/WaylandClient libraries, `usr/plugins/platforms/libqwayland.so`
   and `usr/plugins/wayland-shell-integration/libxdg-shell.so`. Wayland/scanner/
   xkbcommon/client/xdg-shell feature headers must report enabled.
2. If all are present, reuse the existing package and move directly to actual
   raster platform load and input/rendering. Do not rebuild unchanged QtBase.
3. If files/features are missing, prepare the **existing verified QtBase 6.11.2**
   archive as an immutable source using the existing qualified unprivileged
   `isolated.sh` flow. Use the new
   [conditional recipe](../scripts/build/phase2/qtbase-wayland-raster-build.sh).
   It requires UID 101, new compile/empty stage, exact Wayland/xkbcommon versions,
   forces client/scanner/xdg-shell/keyboard, preserves existing no-GL/no-XCB flags,
   and installs only under `/stage`. It does not promote or enter native Dpkg.
4. Run the static stage helper `--stage --require`; retain the entire manifest,
   actual feature/configure summary, ELF dynamic dependencies and upstream source
   notices. Compare against the retained installed QtBase package: B02 now exposes
   more autodetected libraries, so inspect all actual differences and close native
   Depends before promotion. Do not cherry-pick only the plugin from a different
   QtBase build or overwrite the accepted package's custody. Package all rebuilt
   files under a new Toddy package revision of the same upstream 6.11.2, after the
   coordinator approves its exact metadata. This slice changes no active metadata.
5. Perform the controlled native package transaction with retained rollback;
   verify Dpkg/Depends, existing offscreen widget/TLS/D-Bus/concurrent checks,
   QtSvg consumers, exact Calamares 3.4.3 module compilation, actual Wayland QWidget
   raster display/input and plugin unload/exit. Use `QT_QPA_PLATFORM=wayland` for
   the explicit test; do not accept an offscreen fallback. The inspector alone
   checks neither relocations, ABI compatibility nor real compositor protocol use.
6. Qualify the actual authenticated **root** Calamares launch separately in GNOME.
   Root display access and scrubbed launch environment remain unmeasured. No
   `xhost +`, global socket permissions, copied owner keyring/session bus, broad
   Polkit changes or silent framework replacement is authorized by this recipe.
   Native disk writes still require the separately qualified signed composed
   closure/finalizer, exact plan and owner confirmation.

## Disk custody and validation scope

The official QtWayland archive is 905,288 bytes, SHA-256
`8eb7615e39332a10f506e8dd70f02d5954bb5949ff54f6dcbf8bd6168222f9df`.
It was downloaded through the official HTTPS release URL and matched the official
`.sha256` file before extraction/use. Inspection used Python tarfile reads; there
was no source extraction or build. Before downloading, free space was
109,586,087,936 bytes; afterward 109,585,174,528. The check reserved another worker's
148,000,000-byte planned model download in addition to the required
107,911,053,312-byte (100 GiB + 512 MiB) floor. No further Qt downloads are planned.
A native build needs a new measured reserve check and explicit peak budget.

Focused tests exercise read-only static inspection, missing keyboard/plugin
rebuild decisions, ELF/escaping-link rejection and recipe/version guards. Fixtures
are synthetic static ELF headers, never an actual plugin load. No guest, host
system package, current package metadata, installer composition or disk target was
modified. Native inspection/build/launch/installation remain pending.
