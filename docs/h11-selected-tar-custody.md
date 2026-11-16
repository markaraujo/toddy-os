# Second opaque-file custody profile: H11 copy Tar

This profile reuses the H10 opaque streaming/gzip/decompression mechanism and
permits only the equivalent historical H11 file:
`/mnt/lfs/sources/stage/h11-release-root-evidence/copy/selected-root.tar`.
It does not select an expanded root, either retained SquashFS copy, the ISO or
any manifest/log. The source table accepts only literal `h10` and `h11`; there
are no user-defined paths, receipt names or archive profiles.

The measured H11 file is device 64788, inode 1239398, mode 0644, root:root,
link count 1, mtime 1794056866601470587 ns and 3,731,630,080 bytes. Its allocated
potential is **3,731,636,224 bytes (about 3.48 GiB)**, not a claim of measured
reclamation. SHA-256:

```text
b914a7dc2c0678c4153c2e2f0cdb39d97764c937a3e5b5e139ed3914324a9efe
```

The evidence/copy directory inodes are 1239390/1239393, with 31 inventory rows
including the evidence root. The profile independently pins H11 assembly,
copy-report, selected input and `20-image-manifest.json` hashes. Full inventory,
private host archive durability, complete decompression, target/candidate and
consumer checks are unchanged. The proof also binds its literal profile and
profile source hash, so H10 proof cannot authorize H11 retirement.

## Deployment and one coordinator command

**Complete the already running H10 operation before syncing this shared-source
update.** The first H10 receipt pins the prior guest/host producer bytes; changing
those files during an active operation would correctly invalidate its custody.
Once H10 has a complete reconciled receipt, sync the shared guest helper plus
`opaque_tar_profiles.py`, and the shared host controller plus thin H11 entry.

Only the sole coordinator then runs:

```sh
python3 scripts/host/phase2_h11_selected_tar_custody.py
```

The thin entry selects the fixed H11 profile. The shared guest command becomes
`h10_selected_tar_custody.py h11 export|receipt|retire`; the historical helper
filename does not broaden its target. Unique guest receipt:
`/var/log/toddy/phase2/h11-selected-tar-custody-1.json`. Unique private host
context: `.local/phase2/h11-selected-tar-custody-1`. The H10 default names remain
unchanged. Both profiles share the same host/native locks and refuse any
existing or uncertain receipt/context.

All H11 manifests/logs, both retained SquashFS copies, ISO, current Phase 2
caches, package/source archives and accepted read-only backing images remain.
Actual guest `f_bavail` delta is recorded after the single fixed unlink. No
15–20 GiB or physical host/QCOW2 trim claim follows from this one profile.
Failure, lost reply and opaque-file recovery follow
[the H10 custody contract](h10-selected-tar-custody.md): reconcile first, keep
partial artifacts, never replay or extract Tar members.

Source fixtures cover distinct fixed identities/receipts, rejection of arbitrary
profiles, H11's current byte bound in the shared compressor and cross-profile
proof refusal. No actual H11 export or retirement is claimed by source tests.
