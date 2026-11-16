# Execute the prepared native Qt raster upgrade

Run only in the new coordinator-owned **phase2-candidate** guest. Accepted B02
backing images and h07final/h09/foundation masters remain read-only and unchanged.
This guide is actionable source preparation; none of these native commands has
been executed by the source worker. Preserve status/current story acceptance.

## Prerequisites

- Complete/reconcile the selected host custody operation and measure free host
  capacity. Keep 100 GiB + 512 MiB host reserve plus actual new disk/build/ISO budgets.
- Attach a new disposable virtio scratch disk with serial `TODDY-QT-RASTER-1`
  (within virtio's 20-byte ID), format/mount it through the coordinator's guarded
  disk procedure at `/mnt/toddy-qt-raster-1`, ext4, rw/nosuid/nodev, root-owned
  without group/world write. The wrapper validates exact mount/source/serial,
  different device from `/mnt/lfs`, UUID/mount ID/boot identity and 12 GiB free.
  It never formats or mounts an arbitrary disk itself.
- Inspect actual candidate target free space. Existing margin near 16 GiB is
  insufficient for an upgrade. Reclaim only qualified redundant closed stages/
  caches with actual stage/package/source custody and no backing/mount consumers;
  retain old QtBase/Svg/Linguist packages and accepted source/results. No deletion
  or retirement is performed by the Qt wrapper. It requires 16 GiB + 64 MiB for source
  preparation and later 16 GiB + 3×staged payload allocation+64MiB before transaction.
- Sync the reviewed committed source into `/opt/toddy-build` and ensure the
  existing guarded target/native Dpkg records are available. Reuse the exact
  verified QtBase 6.11.2 archive already under `/mnt/lfs/sources`; no downloads,
  system dependency upgrades, owner keyrings or current-root copies are required.
  Existing QtBase must be 6.11.2-1+toddy1 and missing the required raster features;
  a complete existing backend requires no rebuild.

## Commands and durable evidence

With one coordinator/guest writer, in the guarded builder guest:

```sh
bash /opt/toddy-build/scripts/build/phase2/qtbase-wayland-prepare.sh
python3 /opt/toddy-build/scripts/build/phase2/job.py qtbase-wayland-2 \
  /mnt/lfs/sources/phase2/inputs/qtbase-wayland-6.11.2-2 \
  /mnt/lfs/sources/phase2/work/qtbase-wayland-2 bash /src/toddy-build.sh
python3 /opt/toddy-build/scripts/build/phase2/qtbase_wayland_native.py qualify
cd /opt/toddy-build/scripts/build
python3 run_step.py b12-qtbase-wayland-install-2 \
  phase2/qtbase-wayland-install.sh phase2/qtbase-wayland-check.sh --user root
```

The native prepare receipt is
`/var/log/toddy/phase2/qtbase-wayland-prepared-2.json`. It pins archive/member
custody, old package archives/records, exact helper/recipe/harness hashes and
scratch/alias identity; a root write to source must receive EROFS. Preparation
refuses all existing input/work/promotion/receipt paths, preserving uncertainty.
The qualified harness supplies native dependencies read-only, unprivileged UID 101,
new private namespaces and an empty network. It exposes no owner session bus,
credentials, package database or writable installed payload to source/compiler.

The build receipt/log/exit are `qtbase-wayland-2.{job.json,log,exit}` in that
log directory; work contains `qt-static-stage.json`, `qt-staged-consumer.log`,
`qt-existing-lrelease.log` and `qt-qualified.json`. Stage headers come first and
assert Wayland/scanner/keyboard features; staged libraries/plugin metadata and
existing Svg/Linguist consumers are checked under a private D-Bus/offscreen QPA.
No offscreen test proves actual Wayland display, input or root launch.

Qualification requires exact successful job command, unchanged original producer
helpers/harness/source inode and complete stage manifest. The install recipe
copies only verified worker output into a new scratch promotion tree, performs
actual direct ELF provider ownership/Depends/RPATH checks, binds it at the fixed
native staging alias and retains upstream legal notices. The existing packager
builds **qtbase 6.11.2-1+toddy2**, preserving same-owner path semantics and refusing
foreign package conflicts before Dpkg. There is no `--force-overwrite`, duplicate
Qt package, arbitrary command, framework switch or source version bump.

The normal full-root native run_step record remains authoritative. The separate
`qtbase-wayland-install-2.json` records intent before the native transaction;
postcheck verifies package status/Depends, installed raster features, existing
Svg/Linguist behavior and unchanged old package/record custody. If an installed
Calamares binary exists its offscreen `--version` is checked, but that is not
plugin/graphical qualification. Tests retain outputs in target
`/tmp/toddy-qtbase-wayland-postcheck-2`; do not copy owner runtime secrets there.

## Failure, rollback and remaining gates

Any existing partial preparation/job/stage/archive/receipt requires actual
postcondition inspection. Never rerun prepare/install to guess the outcome.
Source volume aliases and its identity must remain mounted for this boot; after
an unexpected reboot, preserve all files and create a separately reviewed exact
alias recovery receipt before qualification. No automatic new job or resume hook
is provided. Healthy compiler jobs are monitored, not restarted.

If an upgrade is interrupted or fails its postcheck, stop new tasks, inspect
native Dpkg and exact old/new archives/current payload. The old QtBase archive
and records remain retained for a separately guarded native downgrade/reconcile;
never copy individual shared libraries. The pre-upgrade candidate checkpoint is
the coordinator's complete rollback boundary; accepted B02 backings remain usable.
No rollback is automatically claimed or performed by this source slice.

After headless/package checks, qualify actual Wayland QWidget rendering/input,
exact Calamares 3.4.3 module build/load and authenticated root GUI launch with
minimum measured display transport. Do not weaken global X11/Wayland permissions
or inherit owner keyrings/provider/session credentials. Installer disk writes still
require its independent signed composed closure/finalizer, exact review and owner
confirmation; this Qt upgrade is not B12/G2/ISO acceptance.

## Configure correction and preserved attempt1

The coordinator observed qtbase-wayland-1 exit1 during configure, before
compilation. Frozen Qt6.11.2 src/gui/configure.cmake enables system_freetype for
INPUT_freetype=system and disables it for qt; fontconfig requires that feature
and Fontconfig_FOUND. The original combination fontconfig=ON/freetype=qt was
therefore inconsistent. Use the already installed frozen FreeType2.14.3 provider
with INPUT_freetype=system. Keep Fontconfig2.18.3, bundled HarfBuzz, the source
archive/version, raster Wayland profile and all other flags unchanged. The
coordinator's actual pkg-config inspection reports freetype2=26.6.20 (the
FreeType2.14.3 package's metadata version), not a requested dependency upgrade.

The corrected controller uses only attempt2 aliases, source-2/work-2/promotion-2
on the SAME /mnt/toddy-qt-raster-1 volume, prepared/job/install/postcheck2 names
and b12-qtbase-wayland-install-2 dispatcher identity. Original source/work aliases,
scratch source/work directories, job1 configure output and all first-attempt
receipts remain untouched and cannot satisfy attempt2 qualification. Existing
attempt2 paths still cause refusal; no cleanup/replay is performed. This source
correction has not compiled or installed Qt and grants no GUI/installer acceptance.
