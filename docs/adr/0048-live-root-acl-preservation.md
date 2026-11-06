# ADR-0048: Preserve POSIX ACLs outside Squashfs inode metadata

- Date: 2026-11-06
- Status: Native metadata-channel experiment passed; real image integration pending

Source inspection finds that Squashfs-tools 4.7.5 read_xattrs.c and Linux 7.1.8
fs/squashfs/xattr.c support user.*, trusted.* and security.* namespaces, not
system.posix_acl_access/default. Do not claim that basic Squashfs ownership/mode
or security-capability preservation also preserves POSIX ACLs. No native
Squashfs tool build or image roundtrip has run yet; H10 remains unstarted.

Retain extended ACLs as a separate numeric getfacl stream generated from the
sanitized root tree using physical traversal, relative escaped names and
--skip-base. Preserve ordinary numeric ownership/modes and supported xattrs in
the root image itself. Restore the ACL stream with native setfacl -P --restore
inside the new overlay root before starting init/services; the installer must
apply the same stream to its new filesystem before first boot. A failure must
stop for recovery instead of silently running with changed permissions. Do not
copy up all base files merely to restore empty/basic ACLs. Do not replace the
main root filesystem's service identities with all-root initramfs ownership.
Actual image/overlay metadata tests, including any required copy-up behavior,
are still mandatory before acceptance. This decision is not an assertion that
the integration already exists or all image metadata is correct.

A private actual-target experiment deliberately strips a file's ACL while
copying its data/basic mode, then restores the numeric stream. It retains UID
18/GID 18, mode 4750 including special flags, escaped spaces/newline filename
and exact content. Actual child processes running with UID/GID 101 cannot read
the stripped copy, can read after restoration, and cannot execute it. The
source contains only harmless fixture text; no account credential is used.
Temporary data is removed and no package is installed or modified.

The first successful probe emitted the native ACL tool's warning that --restore
without -P can traverse symbolic links. Its original result/stderr/exit remains
outside Git. The corrected physical restore repeats the whole experiment with
exit 0 and no warning. A new file image is still not tested. Raw prefix:
.local/logs/h10-native-acl-sidecar-probe; JSON SHA-256
83c41d0eb7cb7ca0dc4f03061ce0eaec8c057ecc97d26019bb33104c00abe0b7.

Alternatives: discard ACLs (unacceptable permission loss), rely on Squashfs
xattrs (contradicts the actual supported namespace tables), or change the root
format and introduce a new builder/kernel path solely for this metadata. The
small explicit metadata channel preserves required semantics while keeping the
selected compressed-root tools. No source test is removed or classified passed
from a private fixture. Main-root/installer source and format tests remain open.


## Overlay copy-up and hardlinks

A follow-up used the accepted native tools with the builder's Ubuntu
6.8.0-147-generic kernel in a new private mount namespace. A read-only bind
of a private ext4 lower fixture and a 64 MiB tmpfs upper/work pair exercised
actual overlay mounts, numeric ACL restore, UID 101 access, mode 4750/UID 18/
GID 18 preservation, unchanged lower bytes/ACL, and volatile upper disposal.
The source fixture has UTF-8/newline names and two hardlinks to one file.

The negative control, index=off, restored the ACLs but split the hardlinks:
writing one name no longer changed the other. The index=on run retained both
inode identity and actual write propagation. This is a real behavior difference,
not an assertion that matching content alone proves hardlink preservation.
Both profiles completed their expected assertions, and all private mounts and
fixtures were removed. Overlay was auto-loaded only in the disposable builder;
no host module, mount or security setting was changed.

Require index=on for the planned live overlay, and verify the effective mounted
option rather than trusting a successful mount exit. Never silently accept an
index-disabled fallback after restoring ACLs. Frozen Linux 7.1.8
Documentation/filesystems/overlayfs.rst, sections Non-directories, Permission
model and index, explains copy-up and the broken-link behavior without indexing.
Its fs/overlayfs/super.c ovl_lower_uuid_ok/ovl_get_fsid implementation also shows
that incompatible lower UUID arrangements may disable indexing. Inspect the
actual mounted profile and retain an end-to-end hardlink write test.

This experiment used ext4 as lower, not Squashfs. Actual Squashfs export/file
handles, its null UUID in a single lower filesystem, tmpfs upper, kernel 7.1.8
and live boot still require verification before H10 acceptance. The frozen
Squashfs source includes export.o and installs squashfs_export_ops; no obsolete
SQUASHFS_EXPORT Kconfig symbol is added. The final image must retain export
metadata. Do not extrapolate the builder-kernel experiment into a native boot
pass or assume every kernel/lower combination supports the selected profile.

Reproduce from the checkout with python3 scripts/host/probe_overlay_acl.py off
and then the same command with on. This deliberately tests private builder
fixtures only; it does not execute H10 or modify the installed root. Raw logs (SHA-suffixed immutable generations are retained alongside the
current unsuffixed report):

- .local/logs/h10-overlay-acl-index-off-probe.json, SHA-256
  `7943c3f5b292551d3998c67f03f35ea5abdec0463c3c5813570e32bde9ef6cae`.
- .local/logs/h10-overlay-acl-index-on-probe.json, SHA-256
  `04797b3788663e4ad3d4ab843eecfe30a32693e130a11c4c800cde26e697d320`.

The earlier default/off observations remain outside Git. Alternatives include
copying/relinking every hardlink into tmpfs before services or using a different
writable-root design; neither is needed if the intended single-layer indexed
profile passes the actual Squashfs/native-kernel test. Failure of that test must
reopen this choice, not discard hardlink semantics or weaken the acceptance.


## Administrative helper behavior through the live overlay

The prepared /init places upper/work under a nosuid,nodev tmpfs /run while
mounting the live root overlay with normal executable semantics. Verify that
this does not silently disable the final root's reviewed privileged helpers.
Frozen Linux 7.1.8 fs/exec.c checks mnt_may_suid(file->f_path.mnt) and process
no_new_privs before applying set-ID credentials; mode bits alone are not proof.

The private builder-kernel experiment now matches those tmpfs options. Native
GCC compiled a tiny C executable that only prints real/effective UID. It is
root-owned mode 4755 in the private lower tree. A child drops supplementary
groups, GID and real/effective UID to 101 before executing it. Actual results:

| Execution path | Real UID | Effective UID |
| --- | --- | --- |
| Overlay before copy-up | 101 | 0 |
| Overlay after copy-up and restored mode | 101 | 0 |
| Same bytes directly through the nosuid upper mount | 101 | 101 |

The read-only lower executable's bytes/mode stay unchanged. The existing ACL,
hardlink and volatile-write assertions still pass with indexing enabled; the
index-disabled control still demonstrates broken hardlink write propagation.
No installed helper, account or host security policy was changed. The inoffensive
probe executable and all mounts/fixtures were removed after verification.
This is not the future agent privileged executor or an installed-system test.

Updated native evidence generations use the same h10-overlay-acl-index-*-probe
prefix, preserving every earlier cited generation before replacing the current
report. Off SHA-256:
`1911babc83d41f0b6646b1b759c11a8d83b25ef149e7c32bbdca282893dd325b`.
On SHA-256:
`ec555a0fdb531b6b6201c9ead094aebd8e6be31264523cea2e6cb175c7cd578e`.
The actual Squashfs/7.1.8 live root must repeat the relevant checks. Keep normal
root-overlay helper behavior distinct from the nosuid staging path; do not
weaken the latter globally or claim broad security certification from this
small executable test.
