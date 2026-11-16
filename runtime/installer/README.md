# Native installation backend source

The selected frontend remains Calamares3.4.3. Its frozen B01 synthetic no-write
fixture is unchanged. The new source modules supply a deterministic backend for
a real guided installation; no LLM chooses partitions or executes the recipe.
No disk formatting, mount, account creation or GRUB operation was executed while
preparing these files. Host checks use a fake native runner and private fixtures.

`LinuxDisk.probe` reads a canonical whole block device, kernel identity, serial,
size/sector geometry, mount/use state, signatures and virtual-hardware identity.
It refuses partitions, held/mounted/read-only devices and nonblank targets for
this initial blank-disk slice. A read-only exclusive open checks kernel use across
mount namespaces. `make_plan` fixes explicit aligned GPT BIOS-boot/ESP and ext4
root extents, measured selected-payload space/headroom, firmware, owner/locale/
timezone, catalog/payload identities and deferred optional intent. Its digest
binds every field; changed identity or intent requires a different review.

Default `Installer.execute(plan)` returns review data and cannot write a disk.
Actual execution requires the exact digest, an independent current destructive
owner-authorization callback, root, native-tool preflight, a private journal and
one writer lock. Immediately before `sfdisk`, the engine re-probes the exact disk
and checks identity, policy, authorization and cancellation again. There is no
permanent virtual-only product restriction: `ProductionPolicy` supports an
explicitly confirmed physical blank disk. `QualificationPolicy` separately limits
development qualification to the designated `TODDY-INSTALL-*` QEMU disk. Physical
installation is untested; nonblank whole-disk replacement, dual boot, encryption
and Secure Boot remain unavailable in this slice.

The native argv backend writes GPT, checks observed extents, creates ext4/FAT,
observes UUIDs and verifies target mounts before payload installation. It installs
GRUB for selected BIOS or UEFI, writes persistent UUID-based fstab and an installed
kernel/initramfs boot menu with a normal text-login recovery entry. It uses no
live overlay initramfs, fake previous OS rollback, force-format flag or storage
pre-zeroing assumption. No unrelated physical device is exposed in the temporary
target `/dev`; exact target devices and minimal harmless character devices are
bound for the trusted native tools, with private proc and read-only sys views.

The following trusted integration callbacks are deliberately mandatory; a marker
or a dirty development-root copy does not qualify the offline installation:

- `verify_payload(plan)` verifies actual composed media/closure/catalog before
  the first write, and returns verified payload/catalog digest bindings.
- `install_payload(root, plan)` installs that exact source-built own-archive
  offline closure, including native ownership/dependency/source/license and
  private-key/image-closure audits. Build/probe packages are not automatically
  selected. It returns the same measured payload/catalog digest bindings.
- `build_boot(root, plan, observed_root_uuid)` builds and verifies an installed
  initramfs using the accepted kernel/module closure. It returns `verified`,
  `kernel`, `initramfs`, `kernel_sha256` and `initramfs_sha256`. The backend checks
  actual installed artifact bytes before GRUB. Boot/device/storage dependencies
  and initramfs contents need actual native qualification.
- `save_pending(root, plan)` invokes shared `runtime/setup/pending.py` as the fresh
  installed user. Do not duplicate its schema or write it as root. Use an
  installation ID such as `install-<operation_id>` and preserve unavailable
  wishes as deferred; no acquisition or reusable grants. Return `verified`,
  `uid`, `mode`, `path`, `catalog_sha256`, `manifest_sha256`. The engine independently
  verifies the observed file's UID0600, private0700 parent and actual bytes.

Login passwords enter only through a bounded dedicated private pipe passed by
the account UI, never JSON/argv/environment/journal. Native groupadd/useradd and
chpasswd create a fresh owner/home and normal login; this creates no assistant
grant. Canonical identity writes reject inherited machine IDs and emit an empty
machine-id for first boot. Hygiene rejects known live/builder accounts, autologin,
other personal homes, SSH identities, keyrings, network secrets and random seeds.
The composed-payload audit remains responsible for complete private signing-key
and image-source closure; this known-path check is not a blanket secret scanner.

Every mutation step is durably marked before dispatch. Cancel before writing
returns canceled-without-disk-writes; later Stop waits for a native command's safe
boundary and reports rescue/reconciliation. A native error or lost outcome never
automatically retries a write. On restart, an existing unfinished operation
requires observed postcondition reconciliation from the rescue environment.
Do not invoke the engine under a new ID to bypass that check. Busy mounts are
reported rather than lazily/forcibly unmounted. The first failed installation
uses the accepted rescue-medium route, not a fictitious prior installation.

Focused host checks:
`python3 -m unittest discover -s tests -p test_installer_backend.py -v`.
These prove source guards and command plans only. Calamares job wiring, composed
offline closure, actual virtual-disk install, detached ISO boot twice, installed
credentials/identity, native update rollback and physical testing remain pending.

## Verified offline input bundle

[`scripts/build/phase2/offline_payload.py`](../../scripts/build/phase2/offline_payload.py)
prepares an exact native own-package input bundle. It reads the committed B02
runtime projection and its bound profile, exact versioned component JSON records
and `.deb` cache. It independently inspects archive control/payload metadata and
hashes, versioned dependency alternatives, unique ownership and copyright/source
provenance. It reuses H10 `root_inventory.package_inventory` unchanged; it does
not copy any current builder-root files, account database, home, cache or logs.

Keep the retained foundation and full declared desktop/Git closure. The required
offline additions are the separately qualified `toddy-branding` and lightweight
`toddy-assistant` packages. Agent/executor/voice/integration/Node/model closures
are separate acquired products. The accepted kernel, pre-FUSE recovery kernel and
owned foundation GRUB configuration are mandatory source artifacts; G1 evidence
and recovery recipes are unchanged. A complete desktop projection is still an
input selection, not a composed image or blank-disk installation.

The preparer verifies an offline detached Release signature using an explicitly
pinned binary public keyring, Origin, SHA256-bound Packages index and exact
package identity/hash/size. It retains only those public verification materials;
secret OpenPGP packets are rejected before copying. No release signing key,
credential, new network repository, hosted service or trust bypass is created.
The focused tests generate an isolated ephemeral fixture signing key in a private
temporary directory, then remove it; that is not the project release key.

Owned generated caches require exact output/tool digests, complete selected
producer input namespaces (including link/directory identities), regular input
hashes and an actual retained native qualification-report digest. Known schema,
icon, MIME, hwdb, dconf, loader and module-index families have explicit scopes.
Unknown/incomplete families fail closed. Unowned generated paths, fresh service
accounts, PAM/service policy and image state still require native finalization.
`bytes` is the observed uncompressed package file size, conservatively including
hardlink aliases, rather than compressed archive length; installer headroom remains
separate. Failed/incomplete preparation is retained and cannot become install-ready.

The coordinator can collect the exact missing inputs with this read-only command
in the designated builder, after checking the current operation/package locks:

```sh
python3 /opt/toddy-build/scripts/build/phase2/offline_payload.py requirements \
  --projection /opt/toddy-build/docs/evidence/B02-desktop-runtime-manifest.json \
  --records /var/log/toddy/packages \
  > /var/log/toddy/phase2/offline-required-inputs-NEW.json
```

This reports exact archive/record names and hashes, missing assistant/branding
inputs, generated-cache binding templates and the required recovery artifacts.
Null tool/evidence fields are missing proof, never approval. Supply the actual
new qualified assistant/branding record paths and actual frozen public release
metadata when preparing a new output generation:

```sh
python3 /opt/toddy-build/scripts/build/phase2/offline_payload.py prepare \
  --profile /opt/toddy-build/config/phase2/desktop-runtime-roots.json \
  --projection /opt/toddy-build/docs/evidence/B02-desktop-runtime-manifest.json \
  --records /var/log/toddy/packages --cache /var/cache/toddy/packages \
  --catalog /opt/toddy-build/config/phase2/software-catalog.json \
  --additional-record /var/log/toddy/packages/toddy-assistant_ACTUAL-VERSION_all.json \
  --additional-record /var/log/toddy/packages/toddy-branding_ACTUAL-VERSION_all.json \
  --keyring /ACTUAL-PUBLIC-REPOSITORY/toddy-archive-keyring.gpg \
  --key-sha256 ACTUAL-REVIEWED-PUBLIC-KEY-SHA256 \
  --release /ACTUAL-PUBLIC-REPOSITORY/Release \
  --signature /ACTUAL-PUBLIC-REPOSITORY/Release.gpg \
  --packages /ACTUAL-PUBLIC-REPOSITORY/Packages \
  --index-path ACTUAL-SIGNED-RELATIVE-PACKAGES-PATH \
  --generated-bindings /var/log/toddy/phase2/ACTUAL-qualified-cache-bindings.json \
  --output /mnt/lfs/sources/stage/phase2-offline-inputs-NEW
```

The `ACTUAL`/`NEW` names above are required substitutions, not observed artifacts
or commands to replay. Preparation writes only a fresh private output bundle,
with immutable copied archives/records/catalog/policy and public signature data.
It never installs. The output reports `configured_installed_root: false`.

`PreparedPayload` supplies the installer's `verify_payload`/`install_payload`
callbacks. Bind its expected manifest SHA256 and set plan payload/catalog/bytes to
the returned observed values. The default target guard requires the designated
mounted root partition2, exact reviewed parent device identity and root metadata;
an unmounted host tree or arbitrary root is refused before Dpkg. Native root
unpack/configure is available only through the explicit trusted runner, after
rejecting all maintainer scripts/triggers and unqualified Pre-Depends ordering.
Each target must be fresh; uncertain partial unpack is not replayed.

The mandatory native finalizer must run and retain these independent checks:
native Dpkg database; fresh system service accounts; PAM/service policy; generated
caches; ownership/xattrs; private state/keys; runtime linkage; whole-image
attribution; foundation recovery. Each result has passed=true, integer exit0,
an actual report path outside the image and its verified SHA256. The report binds
check name/input manifest and includes measured postconditions. Bare markers are
rejected. The finalizer also declares every fresh/generated entry and a complete
image-manifest SHA256. The adapter independently reads every actual file/link/
directory, rejects unknown devices/xattrs/unattributed state, verifies all owned
bytes/metadata and recovery files, and rechecks bundle/signature custody afterward.
Unpack success alone cannot return the installed-payload receipt.

No actual finalizer, composed root, signed Phase2 repository, blank-disk install
or boot is claimed by this source slice. Native reports, extended system-user
policy and controlled cache/image audits remain concrete required inputs.

## Canonical foundation configuration handoff

The accepted foundation package owns `/etc/toddy/grub.cfg` as a conffile and
`/boot/grub/grub.cfg` as the exact relative link `../../etc/toddy/grub.cfg`.
The backend preserves that native layout. It retains the original configuration
bytes as the read-only, attributed reference
`/usr/share/toddy/recovery/foundation-grub.cfg`, writes selected installed UUID/
kernel/initramfs entries to the canonical conffile, runs native grub-script-check
before grub-install, and records verified configuration/reference hashes in the
operation journal. Unknown links or an unexpected regular `/boot` configuration
are refused. The retained reference is historical input, not an active entry
booting the builder disk or a fictitious prior installed-system rollback. Current
text recovery and the accepted external rescue-medium route remain distinct.

The known H10 `/etc/localtime -> ../usr/share/zoneinfo/UTC` leaf is also handled
explicitly: the selected timezone bytes atomically replace that exact generated
link, with byte/type/mode readback. Its zoneinfo source remains unchanged. Other
links are refused without following them. Canonical symlink transformations and
the new recovery reference must appear in final installed-image attribution;
source fixture checks do not replace native installation or detached-media boot.
