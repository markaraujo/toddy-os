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
