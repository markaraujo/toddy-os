# Native installer revision4, reusing the actual compile3 module

Revision `0.2.0-1+toddy2` carries the current Python offline-payload typed MVP
policy. It preserves the retained installed revision1 archive/record, source3,
work3, module/probe, compile and native installation receipts. The frozen
`installer_native.py`, generator and all earlier receipts remain unmodified.
No Qt or Calamares build/install is requested.

After verified source sync, the sole coordinator runs in the guarded builder:

```sh
bash /opt/toddy-build/scripts/build/phase2/installer_mvp_prepare.sh
python3 /opt/toddy-build/scripts/build/phase2/installer_mvp_native.py qualify
python3 /opt/toddy-build/scripts/build/run_step.py b12-toddy-installer-4 \
  /opt/toddy-build/scripts/build/phase2/installer_mvp_install.sh \
  /opt/toddy-build/scripts/build/phase2/installer_mvp_check.sh --user root
```

There is no new compiler job4 and no manufactured build success. Preparation
revalidates the actual compile3 UID101 harness/job/exit, all frozen source3
inputs, actual native install3 recipe/postcheck0/0, original staged source plan,
retained revision1 archive/control/record/module and exact current native ABI
packages. Its module receipt independently requires all four current C++ source
hashes to match. A C++/ABI difference refuses reuse before stage creation and
requires an explicitly prepared fresh compiler attempt, never an automatic
upstream rebuild or changed frozen source. The current module is also rechecked
with native `readelf`/symbol metadata and direct declared providers.

The fresh names are:

- source: `/mnt/lfs/sources/phase2/inputs/toddy-installer-0.2.0-4`
- work: `/mnt/lfs/sources/phase2/work/toddy-installer-4`
- promotion: `/mnt/lfs/sources/stage/phase2-toddy-installer-4`
- prepared receipt: `/var/log/toddy/phase2/toddy-installer-prepared-4.json`
- native receipt: `/var/log/toddy/phase2/toddy-installer-install-4.json`
- full-root transaction: `b12-toddy-installer-4`
- unique offscreen probe HOME: `/mnt/lfs/tmp/toddy-installer-offscreen-postcheck-4`

Preparation creates the current deterministic source/package plan with a private
version2 generator instance, leaving the original version1 source/module globals
unchanged. Its source manifest includes the external revision4 producer/recipes
and `native-module-reuse-4.json`, binding all actual old compile/transaction and
archive hashes. All current packaged Python/legal/config bytes come from the
verified repository, never the dirty installed root. Prepared source files are
readonly and hash-pinned; stage bytes are independently inventoried before native
promotion. The packager child explicitly uses umask022 for public Dpkg control
permissions while evidence remains private.

Native installation is only under the new full-root dispatcher transaction,
with actual dependency preflight and16GiB capacity floor. Postcheck verifies the
new archive/control/record and every installed owned path's bytes, mode, UID/GID
and symlink, executes the original actual offscreen plugin probe against the new
installed module, requires empty Dpkg audit and successful APT dependency check,
then publishes its own verified receipt. Offscreen ABI proof is no root Wayland
GUI, blank-disk installation or boot proof. Missing/existing preparation,
promotion, package archive, record or receipt preserves the state and refuses
replay; reconcile outcome before another namespace is authorized.
