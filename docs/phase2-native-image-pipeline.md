# Current native image pipeline

This pipeline preserves accepted foundation artifacts and consumes the current
source-built native package archives. The integration root is not a release
image. Copying it would include build accounts, caches and unrelated optional
packages. Current source preparation does not assert a booted installer or ISO.

## First executable step: current archive projection

After the coordinator has reconciled all native package transactions, sync the
committed source into the designated builder and run there as root:

```sh
python3 /opt/toddy-build/scripts/build/phase2/image_projection.py
```

This fixed command checks the existing target serial/root/mount guards, takes the
native build lock, refuses active dispatchers, reads fully configured native
Dpkg versions and validates every selected archive against its installed record,
control, owned bytes and legal/source hashes. Versioned dependency alternatives
use the existing offline-payload comparator. It rechecks the native inventory
before publishing a new private generation at
`/mnt/lfs/sources/stage/toddy-image-projection-1`. Existing output is retained;
there is no overwrite, install, unpack, signing or cleanup mode.

The generation contains:

- `profile.json`: unchanged frozen B02 roots/profile bytes.
- `projection.json`: current offline closure, excluding the two explicit base
  additions from its component array as required by `offline_payload.prepare`.
- `additional-components.json`: exact assistant and branding archive rows.
- `live-profile.json` and `live-projection.json`: the live union including
  Calamares, its approved branding and the native Toddy installer module.
- `split.json`: explicit offline/live-only/unselected package names.
- `complete.json`: producer and output hashes, published last after durable writes.

Both closures reject acquired agent/executor/voice/integration packages, Node and
local inference. The offline closure also rejects Qt and installer roots; live
may include their actual dependency closure. No source package is silently
filtered out to make a broken dependency graph appear valid. The output consists
of metadata; archive and composed-root privacy checks remain mandatory.

## Prepare the signed offline bundle

Reuse `scripts/build/phase2/offline_payload.py prepare`, with the new
`profile.json` and `projection.json`, native records in
`/var/log/toddy/packages`, archives in `/var/cache/toddy/packages`, the frozen
software catalog and the exact two additional records identified above. Supply
actual public keyring/Release/detached signature/Packages inputs and the reviewed
public-key SHA, plus measured generated-cache bindings. This command already
validates repository signatures, exact archive closure, source/legal custody,
control scripts/triggers, native dependencies and generated input namespaces.
It produces archive inputs, not an installed root. Do not embed private signing
keys or credentials into this generation or the live image.

No actual current signed repository or cache-binding receipt is supplied by the
exporter. Missing inputs are a real composition blocker, not permission to reuse
stale B02 cache bytes or create a successful signature/finalization receipt.

## First disposable installer qualification

Use the existing developer-only
`scripts/build/phase2/installer_qualification.py` against the fixed native inputs
at `/sources/stage/toddy-installer-native-inputs` inside the trusted live target.
Its real archive/finalizer/installed-initramfs callbacks do not depend on a
production boot seal. Its source-only `review`/`execute` commands require sealed
plan/options descriptors, explicit `TODDY-INSTALL-…` disk serial and exact plan
hash; password input is a separate private descriptor. Read its command help
and `scripts/build/phase2/installer-package.md` for the descriptor protocol.
Never replace that source harness with a production bypass flag. It shares the
same account namespace preflight and fixed callbacks as production.

The prerequisites remain actual signed payload, reviewed service-account/PAM
policy, generated-entry attribution, exact kernel/module boot profile and the
expected clean-image manifest. A native run must generate all nine independent
finalizer reports. Only real detached BIOS/UEFI boots can supply boot receipts.
`seal_installer_composition.py` subsequently verifies those reports and image
bytes and publishes `composition.json` last for the production factory.

## Reuse native compression, initramfs and hybrid components

The existing component boundaries are suitable for a new B12 coordinator:

1. `h10/compress_root.compress`: exact source snapshot, native SquashFS creation,
   extraction, ACL restore and sparse/metadata/hardlink readback. Requires the
   actual fresh image manifest and ACL sidecar. Its own minimum is two times
   uncompressed logical bytes plus 2 GiB; retain the Phase 2 16 GiB floor as well.
2. `h10/initramfs_archive.assemble`: existing source-owned live runtime, actual
   owned kernel/storage dependencies, fixed live scripts, UUID-independent
   media identity/rootfs hash, native newc/gzip and readback. Installed ext4
   boot remains the separate `runtime/installer/installed_boot.py` callback.
3. `h10/initramfs_input.verify(..., assembler=<new B12 assembler>)`: binds the
   new assembler's real journal and final manifest to native compression.
4. `h11/hybrid_media.compose`: fixed native BIOS/UEFI GRUB images, FAT and ISO
   readback, bound media marker, no kernel-execution acceptance claim.

Do not run the historical H10/H11 milestone CLIs for a Phase 2 image, alter their
accepted evidence, or pretend a new assembler has the old assembler hash.
`h11/assemble_iso.archive_input` hardcodes the historical assembler; a new B12
caller must use the generic verifier and the equivalent real archive checks.
Approved artwork is supplied by the separately owned branding packages; no new
art or live-only installer files belong in the offline base.

## Concrete remaining native blockers

The projection is an executable input step, not the complete image assembler.
Remaining work is a fresh archive-only root assembly driver with complete
source-attributed generated entries and live GNOME owner/session policy, followed
by the component calls above and disposable QEMU blank-disk BIOS/UEFI checks.
Actual signed repository/cache/policy/image receipts are required inputs. The
current builder's free-space figure alone cannot qualify the larger assembly:
account for fresh root, compressed archive, full extraction readback and ISO
input/readback copies above the 16 GiB reserve. Reuse accepted evidence through
verified custody; this tool neither retires caches nor authorizes deletion.
