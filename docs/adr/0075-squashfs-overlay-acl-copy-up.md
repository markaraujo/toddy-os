# ADR-0075: Copy ACL paths up before restoring live permissions

- Date: 2026-11-07
- Status: Private native Squashfs/overlay checks passed; native-kernel boot pending
- Refines: ADR-0047 and ADR-0048

## Problem and decision

The earlier ext4-lower experiment did not prove Squashfs ACL restoration. An
actual Squashfs image under the indexed overlay reproduced setfacl exit 1,
Operation not supported, on both hardlinked filenames. Preserve this failure;
successful compression/extraction cannot establish live boot permissions.

Frozen Linux 7.1.8 fs/overlayfs/inode.c ovl_set_acl checks the current real
inode's set_acl operation before ovl_set_or_remove_acl copies a lower inode up.
Squashfs lacks that operation. Copy only paths named in the verified ACL sidecar
to the tmpfs upper first, using native chmod --reference=PATH -- PATH to retain
the mode without rewriting content. Then restore the original numeric stream.
Keep index=on so the multiple filenames retain hardlink identity.

The initramfs includes restore_live_acls.sh. /init runs it with the new root's
native Bash/Coreutils/ACL tools before Systemd. The helper decodes only the
frozen ACL filename escapes and validates all entries before copy-up. Absolute,
traversing, duplicate, missing or redirected paths fail. Spaces, newlines and
literal backslashes work; an empty sidecar is valid. Errors still enter early
recovery before services start. No kernel patch or global security change occurs.

## Actual native evidence

Built frozen Squashfs-tools 4.7.5 with accepted native compiler/libraries in
protected disposable source directories. The exact recipe profile passes real
gzip/xz/zstd roundtrips covering data, numeric owners/modes, symlinks, hardlink
identity, sparse allocation, user xattrs and separate ACL restore. The durable
driver keeps inputs, logs, exit files and result. Bounded stages use private
process groups for timeout cleanup. No package is installed; native Dpkg status
is unchanged. A repeated build after improving timeout capture also passes.

```sh
python3 scripts/host/probe_native_squashfs.py start
python3 scripts/host/probe_native_squashfs.py collect /mnt/lfs/sources/recovery/squashfs-native-PRINTED_GENERATION
python3 scripts/host/probe_overlay_acl.py on --squashfs-probe /mnt/lfs/sources/recovery/squashfs-native-PRINTED_GENERATION --copy-up-acls
python3 scripts/host/probe_overlay_acl.py off --squashfs-probe /mnt/lfs/sources/recovery/squashfs-native-PRINTED_GENERATION --copy-up-acls
python3 scripts/host/probe_initramfs_archive.py
```

Use the exact printed generation. Collect the same live PID rather than starting
duplicates. This private experiment never creates H10 package-success markers.

Builder-kernel 6.8.0-147-generic tests use an xz Squashfs image with NFS export
metadata, a read-only loop mount and nosuid,nodev tmpfs upper:

- index=on and targeted copy-up preserve ACLs, numeric owners/special modes,
  hardlink identity and actual write propagation. Lower data remains unchanged.
- Directory access/default ACLs restore; a new child's inherited ACL allows UID
  101 access. security.capability bytes survive compression/copy-up/ACL restore.
- A harmless setuid helper runs as real UID 101/effective UID 0 through the
  overlay before and after copy-up, versus UID 101/101 directly on the nosuid upper.
- Seven helper refusal cases pass: absolute/traversing paths, redirected file,
  redirected parent, unknown escape, missing entry and duplicates. Outside data/
  mode remain unchanged; empty and repeated restores pass.
- index=off restores ACLs but breaks hardlink identity/write propagation, proving
  the index requirement still matters. The ext4-lower regression also passes.
- All private mounts are unmounted; successful overlay fixtures are removed.

Updated initramfs: 45 entries, twenty native runtime files, gzip size 14,272,302
bytes. Two fresh stages produce identical archives in this experiment. Native
extraction and existing byte/mode/owner/device/link/corruption/refusal checks
pass. This is not cross-build reproducibility or actual PID 1/native-kernel boot.

## Sources and retained evidence

Reviewed frozen Squashfs 4.7.5 Makefile; archive SHA-256:
547b7b7f4d2e44bf91b6fc554664850c69563701deab9fd9cd7e21f694c88ea6.
Linux 7.1.8 archive SHA-256:
ff01dcb449279d5b4cfccdb01fee639cf5ff1803f1749a77844dd33915422c49;
its fs/overlayfs/inode.c SHA-256:
6d0e2e57670184c533a03e0da47fad064ca1034b0a8aa30013e763727a069434.
Filename handling retains the frozen ACL 2.4.0 quoting policy in ADR-0048.

Immutable raw reports under .local/logs:

| Evidence | SHA-256 |
| --- | --- |
| Final build/version/three-compressor collection | 90c95b37b55b06fb4afae8bc4150bbc29b52bab4e9d9dd51799b109cbb1069a5 |
| Direct Squashfs ACL failure with stderr | 632c32dfa8cdb5b782b4373c390af4d6a816ad35d1e3f996cc285e4617f94dca |
| Corrected Squashfs index=on | 603289d92cad41f3ccec5403d2b25e3cd9de9dd1b983997df13851d8bd6b2d00 |
| Squashfs index=off negative control | 96293228d7faf596d1b0e83e24b6f91d0de680d43922d94dbbf3a8e1e226fc43 |
| Ext4-lower regression | dfbde528b0a0edfca1f91b6f75e85bc6f751065f647ea08ea4464449f8ecdb5f |
| Updated native initramfs archive | 94f37a7beb43082c7ecccff7ffbec62b1343977c0c8d381bf0c17d23eb348969 |

Helper SHA-256: 527eacc074c38e41324737df924b6ccc95f586cd6469ae7873485509251cd578.
Final private driver SHA-256: c9e71ba263dd25fbe06f5ab8f31bdc76fbb8cc28d12a91b125e58a258540b77b.
Compiled mksquashfs SHA-256: b2c67b7efc3c65ec8a57202599cc2cb22ffdca4068f534e0565055e1713fe6b4.
Compiled unsquashfs SHA-256: a60d305ee407fc10f0ae2729b4586c3502707d5024ec1db5fc750007c88183ce.

## Alternatives and consequences

Discarding ACLs loses permissions; changing the frozen kernel/root format adds
unnecessary maintenance; copying the complete root to tmpfs wastes RAM. Targeted
unchanged-mode copy-up passes the real filesystem experiment and retains the
selected design. Its RAM cost follows files with extended ACLs. Measure that
cost on the final image and repeat with Linux 7.1.8 in the required boot matrix.
No complete foundation image exists yet; H07-H13 acceptance gates are unchanged.
