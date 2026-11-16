# Frozen expanded foundation duplicate custody

Only the two explicit historical caches are eligible: `h10-live-root` and
`h11-release-root` beneath the designated target's protected stage. The source
pins the actual root device/inode/mtime from the coordinator's read-only facts,
plus the already frozen assembly and original image-manifest hashes. No arbitrary
path, alternate profile or replacement-root adoption is accepted.

Future consumer review: foundation CLI work is finished and no further foundation
assembly/compression/initramfs/ISO command may consume these expanded caches.
Restore a reviewed exact tree from retained custody before any newly authorized
consumer. Accepted backings, original ISOs, media trees and all evidence remain
retained. Retirement is capacity management, not new acceptance or a foundation
rebuild. Never delete a live/current MVP root through these profiles.

The sole coordinator runs each independently after syncing committed helpers:

```sh
python3 scripts/host/phase2_h10_expanded_root_custody.py
# Inspect actual completed host/guest receipts and free-space measurements first.
python3 scripts/host/phase2_h11_expanded_root_custody.py
```

Private host contexts are `.local/phase2/h10-expanded-root-custody-1` and
`h11-expanded-root-custody-1`; their opaque archives are `h10-expanded-root.tar.gz`
and `h11-expanded-root.tar.gz`. Do not extract/execute their privileged payload on
the host. Existing reserve-plus-full-stream upper-bound admission still applies;
compression estimates are not used to lower the host reserve.

The existing protected namespace/global FD9 lease and FD8 proof channel apply.
Before export and again before retirement, the complete expanded image must match
the original frozen manifest, including bytes, ownership, mode, mtime, xattrs and
hardlink classes. Raw ACL/xattr/symlink bytes and full identities are then covered
by the existing tree archive verifier, complete gzip decompression, durable host
receipt and second guest snapshot. External hardlinks, mount/open/mapped/loop
consumers, drift or incomplete prior intent fail closed. Evidence/media byte hashes
are retained and rechecked after exact root-only removal. There is no replay or
uncertain-write retry mode; preserve every partial export and journal.

Source fixture tests prove the bounded contracts, not actual custody success.
Record actual recovered guest bytes separately; no host trim gain is claimed.

Retained evidence/media may contain legitimate relative merged-/usr symlinks
(for example initramfs runtime `lib64 -> usr/lib` and `usr/bin/sh -> bash`).
They are recorded separately as typed `preserved_links`, including raw target
bytes/base64/SHA, own inode/device/mode/UID/GID/ns times/link count and raw xattrs.
Resolution walks each relative component and nested link within the same retained
evidence or media tree; absolute targets, escapes (including outside-and-return
chains), missing targets and cycles are refused. No link is silently ignored or
hashed as a regular file. Regular-file hashes and complete obsolete-root archive
proof remain unchanged. All recorded link metadata/raw targets are independently
rechecked after the obsolete root is removed, alongside existing regular hashes.
