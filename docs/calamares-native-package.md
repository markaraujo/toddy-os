# First native Calamares package from the accepted B01 stage

The accepted B01 Calamares 3.4.3 build is staged, not yet a native installed
package. Reuse that exact stage; do not rerun CMake or compile to close this gap.
`calamares_native.py` requires stage hash
`439015aa8fd7c97674e0577862bfd8f21999a1fcb09a67976e848347334b2c03`,
373 entries and 5,468,441 regular-file bytes at
`/mnt/lfs/sources/phase2/work/calamares-probe-1/stage`, the retained B01 consumer-4
exit zero and the frozen source archive SHA from the source lock.

Before writes it checks the original CMake cache: all actual source module
directories are in `SKIP_MODULES`, `INSTALL_CONFIG=OFF`, `INSTALL_POLKIT=OFF`,
`WITH_QML=OFF`, Python/bundled Pybind11 on and `/src` home. Frozen upstream source
files are compared read-only with the retained archive; an unrecorded patch
stops rather than being silently packaged. B01 fixtures stay outside the package.

The seven measured direct external ELF owners are exact frozen runtime
providers: gcc-runtime 16.2.0-1+toddy1, glibc 2.44-1+toddy1, kcoreaddons
6.29.0-1+toddy1, python 3.14.10-1+toddy2, qtbase 6.11.2-1+toddy2, qtsvg
6.11.2-1+toddy1 and yaml-cpp 0.9.0-1+toddy1. Native versions/archive records,
actual provider bytes and unique ownership are checked; internal staged
Calamares libraries are allowed only within that exact stage. Unexpected
RPATH/RUNPATH or direct providers stop before promotion.

The sole coordinator runs in the guarded builder:

```sh
python3 /opt/toddy-build/scripts/build/phase2/calamares_native.py qualify
cd /opt/toddy-build/scripts/build
python3 run_step.py b12-calamares-native-1 \
  phase2/calamares_native_install.sh phase2/calamares_native_check.sh --user root
```

The install recipe first establishes native absence, reserves 16 GiB plus
three payload copies and 64 MiB, then runs the existing staged executable
`--version` against the actual updated Qt using a fixed private offscreen
environment. It creates only new promotion `phase2-calamares-native-1`, adds
retained exact source/license notices and invokes standard `stage_package.py`
for `calamares 3.4.3-1+toddy1`. It does not add upstream install modules, config
or Polkit policy. The custom Toddy module, its private config/branding and narrow
authenticated root launch remain separate packages/contracts.

The actual native install is under the existing full-root dispatcher. The
receipt `/var/log/toddy/phase2/calamares-native-install-1.json` records intent,
then installed/postcheck-pending, then measured native byte/metadata/dependency
and offscreen-consumer verification. The postcheck requires the dispatcher's
persisted recipe exit zero. Existing stage, probe or receipt paths stop; after
an uncertain outcome reconcile the native database/receipt before any action.
Never reinstall or rebuild merely because a postcheck failed. The original
accepted B01 stage and archive remain unchanged.

This source wrapper's fixture tests prove guards and command selection only.
Actual native execution belongs to the coordinator. Offscreen version checks
are not root Wayland GUI, custom module, disk-install, BIOS/UEFI boot or release
acceptance; those remain explicitly pending in the receipt.
