# Fixed production installer composition

This is source integration for B12, not an installable ISO, native finalization
qualification or a blank-disk boot result. The factory has genuine callbacks and
still refuses the currently absent signed composition. There is no flag, JSON
command, environment variable, arbitrary factory path or marker that enables it.
The canonical existing disk-plan, password-pipe, journal, safe-boundary Stop,
identity and GRUB implementation remains unchanged.

## Fixed runtime contract

`live_bindings.create()` reads only
`/usr/share/toddy/installer/composition`. Files and every ancestor must be physical,
root-owned and not writable by other users; links, hardlinked files and changed
source/payload bytes are refused. The production constructor accepts no path.
Readiness independently reloads the prepared signed native archive bundle,
public-key pin, Release/Packages verification, catalog/profile/projection and
archive/record hashes using unchanged `offline_payload.PreparedPayload`.

The required tree is:

```text
composition.json
payload/                         exact offline_payload.prepare output
policy.json                      fresh account template and owned PAM/service paths
boot-profile.json                measured kernel/module namespace and archive epoch
generated-entries.json          exact complete native-generated attribution map
qualification.json               hash-bound summary of actual reports below
qualification/
  native-dpkg-database.json
  fresh-system-accounts.json
  pam-service-policy.json
  generated-caches.json
  ownership-xattrs.json
  private-state-and-keys.json
  runtime-linkage.json
  whole-image-attribution.json
  foundation-recovery.json
  boot-bios.json                  only when actually qualified
  boot-uefi.json                  only when actually qualified
```

No generated file or report above exists merely because this source was committed.

`composition.json` has schema_version1 and SHA256 bindings for payload manifest,
catalog, policy, generated entries, whole composed image, boot profile, qualification
summary and the exact source closure enumerated by `composition.SOURCES`. This
includes disk/identity/adapter/CLI code, shared PendingStore/parser and unchanged
H10 runtime/newc/ELF helpers. The installed assistant handoff/parser source hashes
must also match actual signed offline package ownership. Unknown or omitted
source bindings fail closed. Editing a helper invalidates previous qualification.

`policy.json` has exactly `accounts` and `required_policy_paths`. Accounts has
only literal `passwd` and `group` templates, derived from the reviewed foundation
baseline plus explicitly sourced/qualified desktop service identities. The foundation wheel group must be the empty GID97 baseline until the existing
fresh-owner step adds only the reviewed OS administrator. Root and service
passwords are generated locked; inherited password hashes, builder/live
users, normal personal UIDs and additional UID0 identities are refused. Preserve
LFS and extension source/license references in the native composition evidence
and live package legal inventory. PAM/service policy paths must be actual selected
source-owned files. The exact generated graphical.target and gdm.service links
must already appear in the attributed projection; there is no arbitrary service
enablement or plugin/hook list. A proposed owner username/UID/GID colliding with
system identities is rejected before disk mutation.

The generated attribution map uses the existing PreparedPayload row schema and
nine origin names. It must include all fresh account files, fresh directories,
Dpkg metadata, native loader/cache outputs, fixed service links and `/lost+found`
with actual metadata. Every real file/link/directory is independently compared;
unknown devices, xattrs, cross-device entries and unattributed outputs fail. This
projection is the native base before variable fresh-owner/UUID/GRUB/pending state;
those later changes remain bound to the existing installer operations/receipts
and require the installed-system hygiene/boot qualification. A successful base
projection is not final installed-machine acceptance.

## Actual callbacks

`NativeFinalizer` verifies the native configured Dpkg set/audit, creates literal
fresh accounts/directories, verifies owned PAM/service files and fixed GDM links,
regenerates known caches using a closed native argv vocabulary and selected tool
hashes, runs native ldconfig, refuses inherited private state, checks target ELF
runtime dependencies and independently audits complete image ownership and
foundation recovery. It writes each measured result outside the image under a
new private `/run/toddy-installer/finalization-target-OPERATION` directory. It never
reuses a prior directory after an uncertain result. Each report binds the actual
input manifest and check-specific postconditions; bare passed/verified markers
are rejected by the readiness reader. Unknown cache/tool families fail closed.

`InstalledBoot` uses accepted kernel `7.1.8-toddy`, exact source-owned module tree,
explicit storage/ext4 profile, native module-dependency readback and unchanged H10
ELF/runtime staging, native bsdcpio/gzip and full newc-entry validation. It checks
kernel/module/archive-tool hashes, preserves existing boot output, verifies gzip
roundtrip and returns hashes of actual installed artifacts. The original H10 live
ISO overlay init is unchanged. The new installed init contains only the observed
root UUID; it mounts dev/proc/sys/run, loads selected qualified modules, waits at
most60 seconds for the matching block UUID, mounts ext4 read-only and switches to
actual installed systemd. Failure displays the external rescue-medium route and
keeps PID1 alive; it does not run owner command-line hooks, repair/format a disk or
fall back to another root. Normal/text-recovery entries and canonical foundation
GRUB conffile/reference/link handoff remain the backend's responsibility.

`boot-profile.json` has exactly kernel_sha256, module_namespace_sha256, modules
and integer archive epoch. Compute the namespace with `installed_boot.module_namespace`
from actual signed ownership, not host modules. Allowed storage names are fixed
in source; ext4 plus at least one actual storage family are required. Every
selected module must resolve through the same native kernel release's actual
indices; missing/unknown dependencies, unavailable binaries or unqualified
compression/dlopen requirements remain blockers until native qualification.

`save_pending` runs `/usr/sbin/chroot --userspec=UID:GID --groups=GID` with a fixed
clean environment and `/usr/bin/python3 -I
/usr/lib/toddy/setup/installer_handoff.py`. Only bounded non-secret intent goes to
stdin. `close_fds` prevents inheriting the dedicated password/Stop descriptors;
password bytes never enter request JSON/argv/environment. The helper verifies its
actual nonroot UID/GID and owned home, then calls canonical Catalog/PendingStore
itself. It creates private parents/0700 setup and atomic0600 pending.json, preserves
unavailable wishes as deferred, grants no acquisition consent, and reads back the
actual manifest digest. The backend independently checks ownership/mode/bytes.
The root installer never writes this user manifest directly.

## Packaging custody

The lightweight assistant owns canonical
`runtime/setup/installer_handoff.py` as
`/usr/lib/toddy/setup/installer_handoff.py`; it requires no broker, Qt, Node or model.
The live-only installer owns its installer modules, exact copied
`scripts/build/phase2/offline_payload.py` as `installer/offline_payload.py`, unchanged
H10 initramfs_runtime.py/initramfs_archive.py under `installer/h10/`, and unchanged
`scripts/build/audit_native_elf.py` as `installer/audit_native_elf.py`. Preserve
original licenses/source hashes. Do not install the live Qt/Calamares tree into
the base merely to run the pending helper. Source checkout imports are explicit
fallbacks for development; installed production imports require the fixed module
layout, without runtime symlinks or environment search hooks.

## Native sealing and remaining required artifacts

`seal_installer_composition.py` only seals **existing measured** artifacts. In the
designated guest, after the actual native callbacks/installation probes, supply a
fresh private input tree containing the prepared signed payload, reviewed policy,
measured boot profile, generated attribution and nine native reports. BIOS/UEFI
reports must record two distinct actual boot IDs with installer media detached,
fresh-owner login, same root UUID, initramfs hash and persistent marker hash.
Each firmware report binds this exact base image, kernel, manifest and installed
init source. Only firmware modes with these proofs can be advertised. Source/unit
fixtures cannot supply production qualification.

The native coordinator uses low-level source callbacks under the existing
single-writer qualification harness to collect the first evidence; the production
factory remains unavailable until all retained evidence is sealed and installed.
There is no production qualification override or alternate permissive factory.
Do not replay uncertain writes or use a new operation ID to evade reconciliation.

After these inputs actually exist, the source tool's command shape is:

```sh
python3 /opt/toddy-build/scripts/build/phase2/seal_installer_composition.py \
  --image /sources/stage/ACTUAL-NATIVE-COMPOSED-ROOT \
  --inputs /sources/stage/ACTUAL-NATIVE-COMPOSITION-INPUTS \
  --output /sources/stage/NEW-SEALED-COMPOSITION
```

These uppercase names are required actual substitutions, not observed artifacts
or commands to replay. The tool requires designated guest root and a new output
under `/sources/stage`; it independently audits the image, verifies all signed
archive inputs and reports, rechecks copied custody/source/image bytes and writes
the descriptor last. It does not format/install, sign, download or produce a boot
result. An incomplete output is retained and is not a factory input.

Still required: actual Phase2 signed public repository/key metadata; complete
frozen native offline closure including current assistant handoff and branding;
exact generated-cache union/tool/output/evidence bindings; fresh desktop service
account/PAM policy and all generated metadata; kernel/storage/module/ELF closure;
actual native finalizer reports and image projection; installed initramfs native
probe; BIOS/UEFI blank-disk installation, safe Stop/reconciliation, fresh account
login, two detached-media persistent boots, installed hygiene/update recovery and
live-media/package/source/legal composition. No physical hardware result is
claimed. The current absent artifacts keep production create() fail-closed.

## Deterministic loader resource generation

The installer uses `generated_resources.generate_loader_cache`, a narrow reuse of
frozen H10's Glibc2.44 recipe. Native ldconfig runs with `-X -i`; it must preserve
the complete selected owned library/SONAME namespace and emit the expected native
2.44 cache format. Every readback library resolves to actual selected owned bytes.
Only the freshly generated0600 auxiliary inode cache is removed after exact
metadata/namespace checks; its hash is retained in the operation result. Existing
cache/auxiliary output is an uncertain prior generation and is preserved/refused.
No builder cache, new search directory/tunables or unrelated output is accepted.
The new shared helper is part of the installed composition source hash closure
and live-only installer package manifest. This source correction is not native
regeneration qualification; reviewed independent image hashes still require actual
first-candidate generation and a second fresh finalizer run.
