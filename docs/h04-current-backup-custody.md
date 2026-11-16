# Exact current-byte custody of the inactive H04 target backup

Only `.local/vm/checkpoints/h04-target.qcow2` is eligible for this fixed profile.
A read-only audit found it self-contained, project-owned, single-link, inactive,
not referenced by any of72 current image headers, and outside current/accepted
master/backing/ISO roles. Its current fixed metadata is:

- device66306, inode11810807, mode0644, owner/project UID/GID1000, nlink1
- logical8,805,875,712 bytes; allocated8,784,470,016 bytes
- mtime_ns=ctime_ns=1793929443958529671
- QCOW2 with no backing file

No original whole-image manifest SHA is available for this backup. The profile
therefore makes **no historical integrity claim**. Lossless custody of all actual
current bytes is established independently by a NEW full read-only source SHA,
exact metadata pin, actual read-only QEMU structural check, compression and full
independent decompression byte-count/SHA verification. It does not invent an old
success, old SHA, filesystem test or boot acceptance.

After the other cold-custody operation finishes, the sole coordinator runs:

```sh
python3 scripts/host/phase2_h04_current_cold_backup.py inspect
python3 scripts/host/phase2_h04_current_cold_backup.py compress
```

`inspect` only checks current fixed metadata, accepted foundation/B02 identity,
absolute backing graph, owned candidate and absence of active/open QEMU
consumers. It creates no custody context and does not hash/compress/delete the
real image. `compress` uses the existing serial opaque backup protocol, native
boot/cold-custody locks and exclusive whole-image Linux OFD lock. Actual
`qemu-img check` runs without repair in the existing networkless read-only
utility container; no VM is booted or restored.

Before opening any compressed output, the controller hashes every current source
byte through its pinned FD, records its current metadata/hash with
`historical_integrity_claimed:false`, then rewinds the same FD. The subsequent
compression stream must match that new complete baseline and unchanged identity.
An independent full gzip decompression must reproduce every byte and SHA before
archive rename/fsync, new graph/source/xattr rechecks, durable retiring intent and
only then unlink of the exact original backup. Archive-directory fsync occurs
before source removal. There is no root filesystem extraction on the host.

Fresh artifacts are:

- `.local/phase2/cold-checkpoint-h04-current-1/result.json`
- `.local/vm/checkpoints/h04-target.qcow2.gz` (0600, exact opaque recovery stream)

The100GiB+512MiB host reserve and additional streaming margins remain mandatory.
The8.78GB allocation is only an upper bound: net gain is lower by compressed
archive allocation and measured concurrent filesystem activity. The receipt
reports actual free-space change, never an assumed8GB. If the bounded stream
cannot fit or does not save space, originals/partial outputs remain for inspection.
No second path, generic cleanup, automatic retry or overwrite is accepted.

Existing project logs/metadata/manifests, accepted/current disks and backings,
source/package archives, ISOs and unrelated host data remain untouched. The new
compressed representation is not directly bootable. To recover, verify its stored
archive SHA, stream-decompress to a NEW `.part` at the exact absent original path,
verify the recorded current full image SHA/size, restore stored mode/UID/GID/raw
xattrs/atime/mtime, fsync, rename and run read-only QEMU check before use. Preserve
the archive until verified recovery; it remains a current-byte backup with no
retroactive historical acceptance.
