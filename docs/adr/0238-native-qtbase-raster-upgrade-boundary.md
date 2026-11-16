# ADR-0238: Native QtBase raster upgrade boundary

Status: accepted source preparation; native build/upgrade/Wayland launch pending
Date: 2026-11-16

## Context

The coordinator's real native inventory in the recovery2 context found the
installed QtBase 6.11.2 Gui feature header hash
`515af16e49f4760f5cecd7acb0407fe007241cea97dd0f9c60f12ae1a7a8e8ae`,
with Wayland/scanner features both -1 and no WaylandClient/platform plugin. The
conditional rebuild is therefore needed. Frozen QtBase 6.11.2 already owns
raster Wayland QPA; no additional QtWayland compositor or version upgrade is needed.

Accepted B02 cold backings and historical foundation masters remain immutable.
The coordinator prepares new phase2-candidate overlays and a separately identified
ext4 scratch device before running any new source wrapper. Reclaimed host capacity
does not create target free space: target reserve remains 16 GiB and closed cache
retirement must be independently qualified from actual retained package records.

## Decision

Use the fixed source-controlled prepare/isolated-build/qualification/install/
postcheck sequence in the [native execution guide](../qt-native-raster-upgrade.md).
Keep the qualified job.py/isolated.sh harness, UID 101, immutable source/native
library mounts, private PID/network/IPC namespaces and no owner credentials.
Source/build/stage/promotion live on the separately identified scratch filesystem;
only the intended native package transaction writes installed candidate paths.

Package as **qtbase 6.11.2-1+toddy2**, the same package name and upstream version.
The existing native stage packager accepts same-owner upgrade paths while refusing
foreign ownership, retains exact source/legal records, and uses accepted native
Dpkg. Do not split qwayland into an unowned duplicate Qt package or copy individual
binaries over the accepted package. Preserve old QtBase/Svg/Linguist archives and
records; existing Svg/Linguist packages remain unchanged and are actual consumers
of the new staged/installed Qt libraries in focused native postchecks.

Force raster Wayland/client/scanner/xdg-shell/keyboard and Fontconfig; retain no
OpenGL/XCB and bundled Freetype/HarfBuzz choices. Disable unrelated newly
autodetected GTK3/Xlib/ICU/proxy/GSSAPI/Brotli/direct-input integrations for a bounded
client. Declare the fixed accepted native image/font/keyboard providers; reject
any actual direct ELF provider outside that reviewed set, ambiguous ownership,
missing provider or runtime search path before package mutation. An unexpected
provider is a review failure, never an automatic dependency upgrade.

Native target free space must cover 16 GiB plus three times the actual staged
allocation bound and 64 MiB metadata, independently of compression/replaced-file
reclaim. Insufficient capacity stops before package/archive writes; no reserve
reduction or speculative source/result deletion is permitted. Existing closed
stage/cache retirement requires separate retained-record verification by the
coordinator. Source wrapper preparation requires a new scratch mount with at
least 12 GiB free and target floor plus 64 MiB for its small aliases/receipts.

## Verification and limits

The stage must have an exact manifest and successful private native widget/TLS/
D-Bus/concurrent, existing Svg, Linguist and Wayland-plugin metadata consumers.
These run offscreen, not as Wayland graphical acceptance. The fixed root postcheck
verifies native package/Depends, installed Wayland features and old archives/
consumer packages. Actual Wayland rendering/input and authenticated root Calamares
plugin launch remain separate coordinator gates. No display permission weakening,
provider credential inheritance or installer/finalizer completion is implied.

Focused source tests qualify the metadata/version contract, declared single-owner
ELF provider enforcement, rejected build RPATH and conservative payload capacity
bound. Native compilation, package transaction, rollback and GUI behavior remain
pending. No guest writes were performed by this source slice.
