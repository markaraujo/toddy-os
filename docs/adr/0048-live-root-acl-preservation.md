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
