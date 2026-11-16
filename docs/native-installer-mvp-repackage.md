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

## Fixed installer5 cache-recipe revision

The aggregate cache correction changes packaged `offline_payload.py` and
`native_finalizer.py`. Preserve actual installer4/version2, its source/work,
archive/record and0/0 receipts. Use only the new fixed generation5 actions:

```sh
bash /opt/toddy-build/scripts/build/phase2/installer_mvp_prepare5.sh
python3 /opt/toddy-build/scripts/build/phase2/installer_mvp_native.py qualify5
python3 /opt/toddy-build/scripts/build/run_step.py b12-toddy-installer-5 \
  /opt/toddy-build/scripts/build/phase2/installer_mvp_install5.sh \
  /opt/toddy-build/scripts/build/phase2/installer_mvp_check5.sh --user root
```

The internal selector accepts only4 or5; no arbitrary version, path, job or
namespace is accepted. Generation5 is `0.2.0-1+toddy3`, with source/work/stage,
prepared/native receipt and offscreen HOME names ending5. It reuses the same
actual compile3 only after unchanged C++/native ABI proof, without Qt/Calamares
rebuild. It additionally requires actual installer4 success0/0, its exact
native receipt/prepared source snapshot, retained version2 archive/record and
unchanged installed version2 payload before preparation. Those immutable
historical hashes are included in the generation5 provenance and rechecked
through postcheck without pretending version2 remains installed after upgrade.
No native receipt or success is synthesized from the source selector.

After actual install/check5 succeeds, use a fresh measured MVP projection2 and
signed export4. Earlier projection1/export3/signatures remain immutable. Existing
prepared4 cannot be reinterpreted as current Python source; do not run old
qualify/install actions to refresh it. Native GUI, installer/boot and source
publication still require their actual distinct evidence.
