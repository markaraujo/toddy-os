# ADR-0042: Native base configuration and mutable runtime state

- Date: 2026-11-06
- Status: Source-derived preparation; H08 target execution pending H07 acceptance

Prepare H08 while H07's unchanged Berkeley DB suite runs; do not apply target
configuration early. Execution requires committed/synchronized H07 completed,
H08 in_progress and a successful actual native-metadata-closure recipe/postcheck.
Transfer public status.json with build metadata so the guest enforces the story
gate. A current-state probe correctly refuses H08 while H07 remains active.

Defaults follow frozen LFS 13.1-systemd chapter 9 and section 10.2: independent
Toddy identity, hostname toddy, English UTF-8 with existing Portuguese UTF-8,
US console/Lat2-Terminus16 font and UTC RTC/timezone. Actual native font/keymap
files and static DBus/network/resolve/timesync account IDs were inspected.
Systemd-networkd matches en*/eth* names and obtains IPv4 DHCP; resolved provides
its runtime stub. Keep predictable naming, no embedded MAC/private network or
workstation timezone. Actual boot/DHCP/service behavior remains H12 evidence.

The build-target fstab uses actual TODDY_LFS/TODDY_SWAP labels. The inspected
ESP is TODDY_ESP; mount it explicitly during bootloader work, as permitted by
LFS 10.2's note, instead of requiring a persistent FAT mount/checker here.
Live assembly must replace the build-target filesystem profile; the installer
writes selected disk UUIDs and user locale/timezone. Do not ship a build-disk
fstab as a generic live/installed configuration.

Package regular configuration as toddy-base-config 0.1 with /etc conffiles and
frozen book/recipe provenance. Four unowned bootstrap files have measured exact
hashes in config/h08-bootstrap-config.json. Before installation, refuse any
changed, missing, symlink-redirected or package-owned input; prevalidate every
replacement, preserve all original bytes and a manifest in a private same-target
recovery directory, fsync files/directories, then remove only the exact four
files. This avoids native Dpkg's correct confold preservation retaining stale
unowned bootstrap identity/DNS. Preserve unexpected owner work for diagnosis.
A safety regression initially exposed group-writable mkdir defaults under the
host umask; new recovery directories now request mode 0700 explicitly. All
five backup/refusal tests pass; no target files were replaced during preparation.

Timezone and resolver links are mutable generated state, not immutable package
payload. The package retains only their default policy; initial configuration
creates absent links. Systemd/timedated and owner choices may later change them
without a package update overwriting preferences. Audit accepts only root-owned
resolved's exact runtime link or timezone links to actual tzdata-owned zone files.
Service-enable links must resolve to real package-owned Systemd unit files; DBus
units are owned by DBus rather than Systemd. Never whitelist arbitrary files or
unresolved targets merely because they are in /etc/systemd/system.

Supply /run/dbus through native tmpfiles, enable DBus socket/networkd/resolved/
timesyncd offline and select multi-user.target. Disable networkd-wait-online per
LFS to preserve offline boot. These are file operations under chroot with
--root=/, not restarts of builder/workstation services. The postcheck must verify
actual installed config, package integrity, root locking, static identities,
locale/font/keymap/timezone data, fstab and offline enablement. No password,
provider key or signing private key is configuration-package payload. Keep build
tester until source tests finish; live/installer account profiles are separate.
H10 supplies the documented live local-console login strategy; B12 must remove
live-only login settings and create the installed owner, never a reusable password.

LFS 9.2.2.1 explicitly distinguishes chroot DNS from boot-time resolved. Use a
build-only copy of the builder resolver on the target's separate /run tmpfs,
recreated on chroot re-entry. Packaged /etc/resolv.conf remains a runtime link;
no static QEMU DNS data enters its payload. Image assembly excludes /run data and
must verify that exclusion. Native DHCP/DNS tests at boot still required.

Prepared staging/INI/shell checks and 82 local tests pass. Read-only re-audit of
the unchanged native root still has the prior 1968 unowned cleanup/API paths,
54 generated entries and four pending bootstrap configs: no target acceptance
was invented. All H08 acceptance boxes and status remain pending. LFS computer
instructions retain MIT terms; original project licensing remains D10, not an
assumed grant or a declaration that release licensing is complete.

Read-only pre-change audit: .local/logs/h08-generated-state-audit-before.json,
SHA-256 77a1c357cec44107e25cea8f550be713f7e594613200f96fcec3c3aff1b9d49d. This is the existing 101-package root,
not evidence of an H08 installation.

Native offline-policy experiments subsequently found that DBus's socket is
static and already activated by its owned vendor wants link, and that native
preset-all re-enables wait-online through networkd's Also= despite a disable
preset. ADR-0060 amends the prepared recipe: verify the actual static/vendor
activation, enable the three network/time services, and explicitly mask only
wait-online after disabling it. Private native configuration, repeat, preset
and refusal checks pass. H08 execution still requires H07 acceptance; none of
these experiments changed installed configuration or established real networking.
