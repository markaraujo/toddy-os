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
control, owned bytes and legal/source hashes. Original foundation/configuration packages with no upstream archive must match
the exact committed H11/B02 record hash. New original assistant/branding/installer
payloads require the declared original source kind, internally hash-bound recipe
and packager closure, and an owned source manifest with nonempty source hashes.
A foreign package with missing upstream sources is rejected.
Versioned dependency alternatives
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

## Native candidate archive assembly command

The fixed outer entry `image_native.sh base` (or `live`) runs the assembler
inside the guarded target, using source-built Dpkg rather than the Ubuntu
builder's Dpkg. It takes the actual native build lock, refuses active native
recipes/input sync, verifies existing target API visibility and enters a private
mount namespace. It binds the committed builder `/opt/toddy-build` read-only at
the same path inside the chroot with `nosuid,nodev,noexec`, verifies source inode
identity and mount flags, and invokes target Python with `-I` and a closed
environment. It never copies source/caches/credentials into an image.

```sh
bash /opt/toddy-build/scripts/build/phase2/image_native.sh base
```

The wrapper uses `/usr/sbin/chroot` on the Ubuntu builder; subsequent binaries
are target-native. Existing `/mnt/lfs/opt/toddy-build` trees or binds are refused.
Only the wrapper's newly created empty bind directory is removed on exit, after
unmount and inode verification. Mount changes remain in the private namespace.
After interruption, reconcile a retained empty directory instead of automatically
reusing it. No target API mounts are created or replaced by this entry.

The inner guard independently requires root device `/dev/vdb4`, disk serial
`TODDY-LFS-TARGET` and label `TODDY_LFS`; running this directly on the builder or
workstation root fails. It additionally takes a private native assembly lock.
Prepared signed bundles are fixed at
`/sources/stage/toddy-installer-native-inputs/payload` for base and
`/sources/stage/toddy-live-native-inputs/payload` for live. Live preparation uses
its complete live projection and `required_additions=()` through the existing
Python prepare API; both mandatory assistant/branding roots remain included.

The command creates only the corresponding new
`/sources/stage/toddy-offline-image-1/root` or `toddy-live-image-1/root`.
It checks capacity before creating that generation: 16 GiB + three times the
selected payload's installed bytes + 512 MiB. It pins stage/root inodes and
filesystem, refuses existing generations and verifies actual native tool bytes
against the selected source-owned closure. Dpkg's explicit private log is outside
the candidate image. Every archive is unpacked/configured once, and the exact
native configured database and signed input custody are rechecked. A failure
retains the intent/log/root; there is no retry/resume/install mode.

`unpacked.json` means only “native archives unpacked, needs resource
qualification”. It is deliberately not an assembly-success journal consumed by
H10 compression. Accounts, generated resources, fresh live session and complete
image attribution must still be qualified and reviewed. It never invokes the
production installer factory or substitutes candidate output for a finalizer or
boot receipt. The low-level `unpack_native` function exposes this precise phase
to the separate fixed generated-resource qualification recipe.

After complete unpack, the fixed `qualify-base`/`qualify-live` actions adopt only
the pinned successful generation and call the separate `resource_recipe.qualify`
source component. Adoption compares both receipts, manifest hash, work/root inode
pin, exact configured database and unchanged native unpack log. It never calls
unpack again. Missing/partial receipts or changed custody stop before resource
commands. These actions require that reviewed recipe source to be present; their
output remains a candidate for owner/coordinator source review. Do not run the
production finalizer over a candidate already modified by resource qualification;
reviewed expected outputs must drive a separate fresh generation.

## Fixed native media phases

The new `image_media.py` coordinator consumes a real completed B12 final assembly
journal at `/mnt/lfs/sources/stage/toddy-live-image-2/evidence/assembly.json`.
That journal must bind the current `image_assemble.py` producer, actual complete
snapshot and its exact image root. The current candidate-unpack command does not
produce it: generation-2 finalizer/live-session integration is still required.
Missing evidence fails before a media generation is created.

After that prerequisite, run these fixed commands sequentially in the builder:

```sh
bash /opt/toddy-build/scripts/build/phase2/image_native.sh media-compress
bash /opt/toddy-build/scripts/build/phase2/image_native.sh media-initramfs
bash /opt/toddy-build/scripts/build/phase2/image_native.sh media-iso
```

Each acquires the existing build lock and target guards. Compression binds the
new actual assembly journal to H10 native compression/extraction/ACL evidence.
The initramfs phase uses unchanged reviewed early-live scripts and H10 native
newc/gzip verification. ISO construction uses the same verified root generation,
minimal initramfs and source-owned kernel; native tool versions and archive/record
hashes come from the current live projection, including the actual kernel package
revision rather than H11's historical version constant. BIOS/UEFI GRUB/FAT/ISO
readback reuse the unchanged H11 component, and `SHA256SUMS` is written only after
all native inputs are rechecked.

Fixed new generations are `toddy-live-compression-1`, `toddy-live-initramfs-1`
and `toddy-release-media-1`; existing/failed generations are preserved. The ISO
phase reserves 16 GiB plus three copies of its input bytes plus 2 GiB. These
commands do not partition disks, invoke QEMU or qualify kernel execution. Their
result explicitly retains pending actual BIOS/UEFI live and blank-disk installer
qualification, final source/license/privacy audit and physical owner testing.

## Reviewed generation 2 and actual media journal

After independent review of the generation-1 resource candidate, place the real
reviewed `generated-entries.json`, `expected-image-manifest.json`, policy and boot
profile in the fixed native input directory. The new `finalize-base` and
`finalize-live` actions create separate fresh generation-2 roots. They invoke
real `PreparedPayload.install_payload` and `NativeFinalizer`, then write
`finalized.json` only after all nine measured reports, signed input recheck and
independent complete image attribution succeed. Candidate directories are never
promoted or rerun. Root names are `offline-root-2` and `live-root-2`, avoiding
collisions in the native finalizer's private report directory. Each source root
contains an explicitly empty root-owned 0700 `lost+found` matching the production
ext4 namespace; this is staged metadata, not filesystem-format proof.

Use the same fixed `image_native.sh` outer entry shown above, replacing its
last argument sequentially with `finalize-base`, `finalize-live`, then
`stage-live`. These require the matching committed generated-resource/live-profile
source modules; absent qualification inputs or modules fail closed.

`stage-live` first requires the actual generation-2 finalization receipt. The
separate `live_profile.stage` verifies its report/source/input pins and complete
pre-transform image attribution, then applies only its source-attributed fresh
live account/session policy. The caller captures the unchanged H10 numeric ACL
sidecar with native owned tools and verifies its exact sole-file delta. Only
then does it record the complete metadata/hardlink snapshot and publish a real
H10-compatible `evidence/assembly.json` last. The journal explicitly maps the
native chroot image path to the coordinator's `/mnt/lfs` view of the same guarded
filesystem; it retains actual finalizer/live-profile/ACL receipt hashes. It does
not assert boot, root GUI or release acceptance. A partially completed phase is
retained for reconciliation, never silently replayed.

The live media ID is computed **before** compression by
`live_profile.media_identity`: a canonical hash of the selected payload manifest,
reviewed policy and live-profile producer source. The source-attributed
`/usr/share/toddy/live-image.json` binds that ID to the fixed live user, producer
and root-owned producer unit. `image_media` independently verifies that class,
source/unit bytes and policy identity and reuses its ID in initramfs/ISO. SquashFS
hash remains a separate actual measured field. The media ID does not depend on
final image bytes, avoiding a recursive identity requirement.


## Policy byte identity at the source boundary

The reviewed source `policy.json` must use `offline_payload.encoded(policy)`
(canonical sorted UTF-8 JSON plus newline). Native finalizer custody binds the
raw file SHA, while resource/live contracts bind canonical policy JSON. The
source assembler now requires these bytes to agree before qualification or
generation-2 creation; a pretty-printed equivalent file is rejected early, not
after native finalization. This check does not rewrite a reviewed file, invent
policy or relax the production composition's custody requirements.

## Preserve first-install evidence before shutdown

The developer install harness writes its operation journal under
`/var/lib/toddy/installer-qualification`, while `NativeFinalizer` writes the nine
measured reports under `/run/toddy-installer/finalization-target-<operation-id>`.
The latter is volatile. A completed installer reply alone neither preserves
these reports nor proves a successful boot. Save the actual review envelope as
a root-owned, non-writable-by-others JSON file outside the signed payload. It
contains the plan and no password; retain the original sealed descriptors for
execution as described in the installer package protocol.

After `execute` returns `completed`, while the same trusted VM is still running,
use this source-only collector there:

```sh
/usr/bin/python3 -I /opt/toddy-build/scripts/build/phase2/installer_collect.py \
  --review /sources/stage/actual-installer-review-bios.json
```

The review filename identifies operator evidence, not a new install attempt.
The collector reads the exact completed operation through a read-only database
connection under the existing writer lock. It independently checks the now
nonblank disk's serial, size, device identity and unmounted state; rechecks the
signed inputs/source closure; validates all nine report schemas and input
bindings; and admits the measured copy only above the unchanged 16 GiB reserve.
It copies their **original bytes** into the sealer's fixed
`/sources/stage/toddy-installer-native-inputs/qualification` directory, then
writes `installed-handoff-<operation-id>.json` beside it. Existing identical
files may be read again; differing evidence, partial files, redirected paths,
active installer locks or incomplete operations fail closed. It never invokes
installation, mounts the disk, changes a journal or retries an unknown outcome.
Preserve these outputs and the completed journal in durable coordinator custody
before shutdown. Repeat the review/install/collection procedure on a separate
fresh disposable disk for the other firmware; never reuse a failed operation
or overwrite an earlier qualification report to force agreement.

The handoff records actual UUIDs, expected owner identity, kernel/initramfs/GRUB
hashes, source/input/report bindings and measured payload storage. Its boot,
fresh-owner-login, recovery and production-ready fields remain explicitly
unverified. For each advertised BIOS/UEFI path, detach the installer media and
all build disks, boot only the installed disposable disk, authenticate as its
fresh owner, and measure its root UUID/kernel/initramfs and persistent marker.
A second cold boot must have a distinct actual boot ID and retain that same
marker and root identity. Test the source-owned recovery entry separately;
`foundation-recovery.json` verifies attributed recovery files, not execution of
the rescue system. The old foundation milestone/root-autologin test CLIs do not
validate the new GNOME owner-login path unchanged.

Only observed results may populate `qualification/boot-bios.json` and
`qualification/boot-uefi.json` using the strict
`native-detached-installed-boot-v1` schema. The collector deliberately provides
no command that fills those assertions automatically. The existing composition
sealer continues to require both actual detached boot pairs, all measured
finalizer reports and exact source/image inputs. Public release handoff still
requires the actual ISO/checksums, installer/boot/recovery evidence, license and
privacy review, and explicit pending physical-machine validation; collected
source evidence alone is never an accepted ISO or production seal.

## Private protected stage ancestry

The actual historical LFS `/sources` cache belongs to UID1000 and is mode1777.
A protected stage child alone cannot satisfy `composition.secured()`'s complete
ancestor checks. The fixed `image_native.sh` now provides a private protected
view while retaining the original image paths and underlying data. It never
changes the legacy cache's owner/mode or weakens that generic validator.

Under the existing global build lease and designated target/source/active-job
checks, the wrapper enters a private mount namespace with a closed environment.
It first anchors the actual root-protected, same-target-filesystem stage into a
fresh protected `/run/toddy-image-stage-anchor.*` bind outside the target root.
Only then does it overmount the target's `/sources` directory with a tiny
root-owned0755 tmpfs. It binds the anchored actual stage back as `/sources/stage`
with `rw,exec,nosuid,nodev`, verifying the original device/inode/owner/mode and
actual mount options. Real NativeFinalizer ELF/cache commands may execute there;
setuid/device effects remain disabled. The original raw source cache is hidden
only in this job's view. Prepared archives, maps and public trust inputs already
live under stage; the project source remains its separate read-only/noexec bind.

All old native image actions still enter the actual native chroot with the same
fixed argv. Stage files/directories are created on the original filesystem and
persist at the original `/mnt/lfs/sources/stage` after cleanup. Only underlying
stage/work/root pins enter operation receipts; temporary parent tmpfs/anchor
inodes are local namespace cleanup guards, not persistent image identity.
Cleanup unmounts project source, stage child, parent tmpfs and anchor in that
order. The placeholder inside the tiny parent is removed only while that parent
is still mounted and its temporary device/inode matches. The real persisted
stage is never removed. No lazy/forced unmount or recursive stage deletion is
used; a cleanup failure is retained as a failed operation for reconciliation.

The only added actions are these exact cache-custody selectors:

```text
custody-offline-inspect  custody-offline-export  custody-offline-receipt
custody-offline-metadata custody-offline-retire
custody-live-inspect     custody-live-export     custody-live-receipt
custody-live-metadata    custody-live-retire
```

They call the fixed builder-side candidate-root helper inside this same private
view, preserving its explicit offline/live boundaries. They cannot choose a
command/path or select another root. Host custody entries use this wrapper
rather than traversing the raw legacy ancestry. The helper validates the
canonical global lock, exact FD9 device/inode and kernel-reported exclusive FLOCK
write lease, then reuses that inherited open description without opening or
reacquiring another lock. It never closes/unlocks its caller's lease.

The shell preserves original protocol stdin as FD8 **before** its namespace
heredoc replaces stdin. Only the fixed custody helper receives that original
channel, closing the extra FD8 copy; normal image actions close it. Thus bounded
host retirement-proof JSON stays data and export stdout stays raw tar/protocol,
never shell source or an arbitrary argv hook. The source namespace driver itself
is captured/rechecked in custody provenance alongside the helper/verifier.
Source tests exercise real inherited FLOCK ownership/refusal and binary stdin
preservation, shell/action/cleanup contracts and unprivileged entry denial; they
do not mount a namespace, execute a VM, qualify a native image or reclaim space.

Media phases run builder-side through the same fixed private protected-stage
view as assembly. The wrapper retains the canonical exclusive global lease on
FD9 through native calls and namespace cleanup. `image_media.py` independently
verifies its actual lock inode and kernel exclusive FLOCK; it never reopens or
relocks the lease. Direct invocation without that inherited lease fails closed.
The root-owned temporary `/sources` view preserves underlying stage identity and
outputs while hiding legacy writable source-cache ancestry only inside the job.
Neither original cache permissions nor generated source evidence are changed.

## Fixed current signed-input coordinator

After returning the actual detached signature to the flat
`/mnt/lfs/sources/stage/toddy-package-export-2`, use these builder-side commands
through the protected-stage/global-lease wrapper:

```sh
bash /opt/toddy-build/scripts/build/phase2/image_native.sh inputs-base-requirements
bash /opt/toddy-build/scripts/build/phase2/image_native.sh inputs-live-requirements
bash /opt/toddy-build/scripts/build/phase2/image_native.sh inputs-base-prepare
bash /opt/toddy-build/scripts/build/phase2/image_native.sh inputs-live-prepare
```

`image_inputs.py` consumes the actual projection2 generation, current native
records/archives and the independently pinned public archive certificate. It
verifies real `Release.gpg`, `Release` and `Packages` before creating input output.
It uses the existing signed offline-payload preparation and measured capacity
checks; it changes no packaged installer source. Base merges the two exact
additional-component rows. Live already includes them and passes
`required_additions=()` to the existing Python API, avoiding duplicate roots or
the base-only CLI's additional-root check. Standard profiles continue to exclude
all acquired backend/model/voice/integration packages.

Outputs are fixed at `toddy-installer-native-inputs` and
`toddy-live-native-inputs` beneath the protected stage. Each contains `payload/`,
canonical `policy.json`, `boot-profile.json`, `generated-bindings.json`, actual
archived-cache provenance and a durable intent/completion record. Existing or
interrupted output is preserved and never reused automatically. The policy
projects only locked system service accounts from the guarded target, omits
human/build/live users, clears all supplementary memberships and synthesizes
locked shadow/machine identity through the existing source policy. It never
copies passwords, keys, owner membership or user preferences. Review its actual
service account IDs before generation1 resource qualification. The boot profile
binds the selected archived kernel/module namespace and the fixed virtual-disk
storage set; it is no hardware or installed-boot qualification claim.

Cache binding evidence is explicitly **archived native output provenance**. It
hashes actual installed native component records, owned output/tool bytes and
the complete selected input namespace including assistant/branding additions.
It does not claim a successful selected-union regeneration. The unchanged
`resource_recipe` must execute native tools after fresh unpack and report all
changed owned outputs as blockers. Never replace those blockers with a fabricated
native-evidence hash or promote a candidate tree. Review the actual candidate
map/expected image, place their exact bytes in the matching fixed input directory,
and only then run fresh `finalize-base`/`finalize-live`.

The remaining executable order is:

```sh
bash /opt/toddy-build/scripts/build/phase2/image_native.sh base
bash /opt/toddy-build/scripts/build/phase2/image_native.sh qualify-base
# Independently review actual candidate maps, then install their exact input bytes.
bash /opt/toddy-build/scripts/build/phase2/image_native.sh finalize-base
bash /opt/toddy-build/scripts/build/phase2/image_native.sh live
bash /opt/toddy-build/scripts/build/phase2/image_native.sh qualify-live
# Independently review actual live candidate maps, then install their exact bytes.
bash /opt/toddy-build/scripts/build/phase2/image_native.sh finalize-live
bash /opt/toddy-build/scripts/build/phase2/image_native.sh stage-live
bash /opt/toddy-build/scripts/build/phase2/image_native.sh media-compress
bash /opt/toddy-build/scripts/build/phase2/image_native.sh media-initramfs
bash /opt/toddy-build/scripts/build/phase2/image_native.sh media-iso
```

Apply measured capacity/custody admission between these phases. Missing signed
inputs, native cache drift, source attribution, reviewed maps or finalizer reports
remain concrete blockers. First QEMU BIOS/UEFI boots and blank-disk installer
qualification follow actual ISO creation; none is inferred by this preparation.

## Separate MVP preinstalled delivery slots

The explicitly selected `phase2-mvp-preinstalled-v1` profile uses a separate
projection and fixed inputs/roots/media. It is always `g2_eligible:false` and
must not be relabeled as the standard optional-acquisition release. It carries
only the selected already-built signed backend/tool packages; no Qwen weights,
owner credentials or automatic service/model activation are added by this driver.
After the typed MVP projection has actually been produced, the corresponding
commands are:

```sh
bash /opt/toddy-build/scripts/build/phase2/image_native.sh inputs-mvp-base-requirements
bash /opt/toddy-build/scripts/build/phase2/image_native.sh inputs-mvp-live-requirements
bash /opt/toddy-build/scripts/build/phase2/image_native.sh inputs-mvp-base-prepare
bash /opt/toddy-build/scripts/build/phase2/image_native.sh inputs-mvp-live-prepare
bash /opt/toddy-build/scripts/build/phase2/image_native.sh mvp-base
bash /opt/toddy-build/scripts/build/phase2/image_native.sh qualify-mvp-base
# Review actual base resource outputs and place exact maps in MVP base inputs.
bash /opt/toddy-build/scripts/build/phase2/image_native.sh finalize-mvp-base
bash /opt/toddy-build/scripts/build/phase2/image_native.sh mvp-live
bash /opt/toddy-build/scripts/build/phase2/image_native.sh qualify-mvp-live
# Review actual live resource outputs and place exact maps in MVP live inputs.
bash /opt/toddy-build/scripts/build/phase2/image_native.sh finalize-mvp-live
bash /opt/toddy-build/scripts/build/phase2/image_native.sh stage-mvp-live
bash /opt/toddy-build/scripts/build/phase2/image_native.sh media-mvp-compress
bash /opt/toddy-build/scripts/build/phase2/image_native.sh media-mvp-initramfs
bash /opt/toddy-build/scripts/build/phase2/image_native.sh media-mvp-iso
```

The current projection is `toddy-mvp-image-projection-2`; input directories are
`toddy-mvp-installer-native-inputs` and `toddy-mvp-live-native-inputs`. Candidate
and fresh reviewed directories are `toddy-mvp-offline-image-{1,2}` and
`toddy-mvp-live-image-{1,2}`. Reviewed root names `mvp-offline-root-2` and
`mvp-live-root-2` also isolate finalizer report directories from standard runs.
Compression/initramfs/ISO generations are `toddy-mvp-live-compression-1`,
`toddy-mvp-live-initramfs-1` and `toddy-mvp-release-media-1`. Existing generations
are never overwritten. Standard actions/paths continue to require standard
manifests; an MVP manifest cannot cross into a standard image slot or journal.

This path preserves the same signed-archive, resource, protected source,
capacity, finalizer, ownership and first-boot prerequisites. Its distinct media
and journal labels record a limited MVP scope, not passed installation or G2.

## First real MVP install, then installable MVP media

The first staged MVP live image deliberately has `installer_ready:false`:
production `Composition()` cannot run without real installed-boot evidence.
Do not publish that first desktop/qualification ISO as an installable release.
The trusted coordinator uses the existing sealed plan/password/cancel FD
protocol through this separate source-only entry for the first blank VM:

```text
/opt/toddy-build/scripts/build/phase2/mvp_installer_qualification.py review ...
/opt/toddy-build/scripts/build/phase2/mvp_installer_qualification.py execute ...
/opt/toddy-build/scripts/build/phase2/mvp_installer_qualification.py collect --review ACTUAL_REVIEW_FILE
```

Run with native root Python in the guarded trusted qualification environment,
with source and fixed MVP inputs available. The wrapper accepts only
`/sources/stage/toddy-mvp-installer-native-inputs` and checks the typed non-G2
manifest on every recheck. All actual disk identity, fresh owner/password FD,
plan confirmation, cancellation, native finalizer and boot callbacks remain the
original source implementation. There is no production factory path override,
`--test` flag or live Polkit exemption. `collect` preserves real reports and the
actual disk/identity handoff in the MVP input directory. Never put password bytes
in a command, environment, log or review file.

After an actual blank-VM install and detached UEFI installed-owner boot, retain
the real `qualification/boot-uefi.json` and its source-bound
`qualification/owner-settings-uefi.json` alongside the actual nine finalizer
reports. The existing sealer already supports one qualified firmware; BIOS is
not silently asserted. Then run:

```sh
bash /opt/toddy-build/scripts/build/phase2/image_native.sh seal-mvp-installer
bash /opt/toddy-build/scripts/build/phase2/image_native.sh embed-mvp-installer
bash /opt/toddy-build/scripts/build/phase2/image_native.sh media-mvp-installer-compress
bash /opt/toddy-build/scripts/build/phase2/image_native.sh media-mvp-installer-initramfs
bash /opt/toddy-build/scripts/build/phase2/image_native.sh media-mvp-installer-iso
```

The sealer consumes the fixed MVP offline-root-2, its actual input/report set and
current source closure, publishing only a fresh
`/sources/stage/toddy-mvp-installer-composition-1`. It validates real signed
packages and firmware evidence; no missing receipt is synthesized. Embedding
requires the existing complete first live snapshot and independently calls the
production `Composition.readiness()` over both source and copied staging trees.
It adds only the exact sealed composition tree under
`/usr/share/toddy/installer/composition`; complete before/after bytes, metadata,
xattrs and hardlinks reject any other change except the immediate parent's
mtime. Existing ACLs and their sidecar remain unchanged; new source files must
have no xattrs/ACLs. Copy bounds preserve the16GiB reserve, and every copied file
and output directory is fsynced before the final journal.

`evidence-installer/assembly.json` is published separately with
`installer_ready:true`, the exact composition/copy receipt hashes and actual
supported firmware list. First desktop evidence and ISO are retained. New final
media generations are `toddy-mvp-live-installer-compression-1`,
`toddy-mvp-live-installer-initramfs-1` and
`toddy-mvp-installer-release-media-1`. Their result remains non-G2 and exposes
installer readiness truthfully. Existing/partial seals or embedding intents are
preserved and refuse replay; source changes after the first snapshot require a
new measured source generation rather than overriding the receipt.

MVP installer revision2 must use a fresh measured signed export generation:
`/mnt/lfs/sources/stage/toddy-package-export-3`. The fixed MVP input commands read
`Release`, `Release.gpg` and `Packages` only from that new flat directory after
actual installer4 installation, MVP projection and public-signature return.
They do not fall back to export2. Export2 remains immutable and is still the
fixed standard-profile source; its older installer archive must never be replaced
inside an existing export or signed index. No signature or successful export3
receipt is created by this source-path change.

## Current installer5 MVP inputs: projection2 and signed export4

After the actual aggregate-cache installer5 revision3 package passes, the fixed
`image_projection.py --mvp` command creates only the fresh
`toddy-mvp-image-projection-2`. The MVP input coordinator and media dependency
reader now require that generation and signed `toddy-package-export-4`.
Standard projection2/export2 paths are unchanged. Preserve the prior actual
MVP projection1/export3 and their signature/verification receipts as historical
revision2 evidence; do not overwrite or reinterpret them after a package upgrade.
Export/sign/verify the actual new closure before invoking MVP prepare actions.
The earlier export3 staging commands in this guide describe the preserved prior
checkpoint, not authorization to place export4 signatures in export3.
