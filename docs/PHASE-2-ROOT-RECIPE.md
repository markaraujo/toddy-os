# Phase 2 installed-root recipe contract

B01 freeze, 2026-11-07. Implements the already selected GPT/ext4 and GRUB BIOS/UEFI
direction (D16), not a new installer architecture. This is the exact sequence for
B12 to implement and prove; it is **not an executed installation**. B01's actual
no-write evidence is [separate](evidence/B01-calamares-native-probe.json).

Inputs: accepted kernel7.1.8-toddy/modules and foundation native package records,
authenticated source-built own archives, explicit root allowlists from
[architecture.lock.json](../config/phase2/architecture.lock.json), versioned
Calamares configuration and a schema-validated reviewed target plan. The plan
binds operation ID, firmware mode, resolved virtual disk identity/size, partition
intent, payload/catalog hashes, locale/timezone and target owner identity.
No API key, imported root grant or live/builder account is a plan input.

1. Verify live media identity/root hash and package/catalog identities before
   preparing the target. Resolve block device, serial/size, mount ownership and
   physical ancestry again at the write boundary; refuse the running live/source
   media and unexpected devices. Calculate space from actual selected payload,
   filesystem/boot needs and recovery headroom, rather than the development-root
   size. B12 tests blank disposable virtual disks only. Physical installation,
   dual boot, encryption and Secure Boot are outside this initial supported scope.
2. Present exact GPT changes. Use ext4 for the installed root. UEFI gets a FAT ESP
   mounted at /boot/efi; BIOS on GPT gets its BIOS boot partition. The selected
   profile fixes explicit aligned extents in the reviewed plan before writing.
   Obtain the actual filesystem UUIDs after creation; do not substitute /dev/vdX
   names for persistent boot/fstab identity. A changed plan/device requires review.
3. Assemble a private target root from verified own native archives with the
   explicit offline-base closure. Preserve accepted required foundation tools,
   ownership/conffiles and baseline source/security qualifications. Use existing
   native backend and image payload/runtime/ownership audits. Reconcile each
   transaction before the next. A dirty builder-root copy followed by deletion
   of secrets is not sufficient image closure. Native Qt/installer libraries are
   live-only unless an actual installed consumer requires them. Exclude new
   compiler SDKs, scanners, source caches and test credentials as declared.
4. Write fstab with the **observed** root/ESP UUIDs and selected mounts. Create an
   installed-root initramfs that mounts the persistent ext4 root by UUID and loads
   only qualified storage/filesystem modules. Reuse the accepted kernel/module
   artifacts; do not boot the installed system through the live ISO overlay init.
   Verify the initramfs contents, kernel/module release and required dynamic
   consumers. No blanket foundation rebuild or silent ABI upgrade.
5. Install GRUB for the selected firmware into the reviewed target only: BIOS
   boot code to that GPT disk, or the target ESP for UEFI. Record the actual
   generated entries and root/kernel/initramfs hashes. Include a usable text/rescue
   entry; updates preserve the prior verified kernel/initramfs/entry until the new
   boot succeeds. The first installation has no fictitious previous OS rollback.
   Retain the accepted rescue-medium route for failed first installation.
6. Create the fresh owner UID/group/home, locale/timezone and normal login
   authentication through the dedicated account flow. Verify ownership and home
   contents. Do not copy /home, SSH keys, builder passwords, keyrings, machine ID,
   live autologin or temporary installation accounts. Initialize machine identity
   for the installed machine and disable inherited live-only units. Provider
   credentials remain deferred to the installed user's protected store. Creating
   Linux login credentials does not grant the assistant administrative policy.
7. Install only the repository **public** trust material at
   /usr/share/keyrings/toddy-archive-keyring.gpg. Native APT source metadata uses
   an explicit Signed-By binding to that key and the actual qualified project
   release origin. Verify signed Release/InRelease metadata, package hashes and
   version/dependency closure. The key must match the reviewed release manifest;
   no fixture/test trust key, private signing material, blanket trust bypass or
   Ubuntu/Debian repository is allowed. If the real acquisition repository is not
   qualified, optional acquisition is unavailable with a concrete reason.
8. Remove live-only installer payload/state according to owned package manifests,
   not arbitrary recursive paths. At the end, atomically hand off only selected
   non-secret optional intent to the actual installed user's 0600
   XDG_STATE_HOME/toddy/setup/pending.json. The installed setup rechecks catalog,
   compatibility, consent and transaction state before acquisition. Do not install
   Node/Pi/executor/model/voice merely because they were build/probe inputs.

The versioned JSON-string Calamares boundary preserves actual Boolean types
([ADR-0116](adr/0116-native-installer-feasibility-and-json-plan-boundary.md)). B12
must implement strict parsing, schema/semantic bounds, atomic ownership/handoff
and cancellation/restart reconciliation. A synthetic plan is neither permission
to write a device nor proof that any of these postconditions hold.

B12 exit proof: boot the installed disk with installer media detached, log into
the fresh owner, verify persistent files/reboot, firmware/root identity, no inherited
live/builder credentials, offline desktop/setup and independent later acquisition.
Inject one required-base failure and interrupted/uncertain operation, reconcile
postconditions and demonstrate the documented rescue/recovery route. B13 assembles
the complete accepted component/catalog set and verifies the integrated release.
