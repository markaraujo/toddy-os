# Fixed opaque custody of two historical H07 builder backups

A read-only host audit inspected76 project QCOW/img headers with no errors and
resolved their actual absolute backing references. The active candidate uses
only its current builder/target/Qt scratch and retained seed. Neither selected
historical builder is an incoming backing or active attachment. Those facts are
rechecked by the executable helper; the audit is not retirement or space proof.

Only these two inactive project checkpoints are eligible:

| Source | Logical bytes | Allocated bytes | Original checkpoint manifest |
| --- | ---: | ---: | --- |
| h07-native-crypto-builder.qcow2 | 6,102,843,392 | 6,071,943,168 | h07-native-crypto.json |
| h07-native-services-builder.qcow2 | 6,299,451,392 | 6,273,445,888 | h07-native-services.json |

Exact source device/inode/nlink1/mode/UID/GID/ns times, original manifest SHA and
original full image SHA are pinned in `phase2_mvp_cold_builders.py`. The combined
source allocation is12,345,389,056 bytes; actual gain is that allocation minus
verified compressed archive allocation and other measured filesystem activity.
No8GiB or larger reclamation is asserted in advance.

The sole coordinator first runs this fixed read-only inspection:

```sh
python3 scripts/host/phase2_mvp_cold_builders.py inspect
```

It verifies accepted foundation/B02 identities, actual owned candidate, direct
active attachments and open QEMU file consumers. Every project QCOW/img header
is read without repair. `/vm` and `/evidence` backing paths are mapped to their
canonical existing project files; other virtual aliases require the actual
retained container mount binding. Unresolved paths, symlinks, non-file backings
or incoming absolute references fail closed rather than inferring from names.

After current guest writes are checkpointed and before starting image-growth
work, run the narrow existing opaque-compression protocol:

```sh
python3 scripts/host/phase2_mvp_cold_builders.py compress
```

It acquires shared native-boot and cold-custody locks, then processes those two
sources sequentially, stopping early if actual free space already reaches the
admission target. No VM is started, stopped or restored. A disposable networkless
read-only utility container performs only `qemu-img check`, resolving the original
retained `/vm/builder-base.img`; its bytes/identity remain accepted and unchanged.
An exclusive Linux OFD whole-image lock excludes actual QEMU consumers. Each
source is compressed to a fresh0600 `.qcow2.gz.part` with actual free-space checks,
full source SHA comparison to its original manifest and independent complete
`gzip` decompression byte-count/SHA proof. There is no privileged filesystem
extraction or nested executable restoration on the host.

The archive file is fsynced, renamed, its directory fsynced **before** retirement,
then rehashed. A durable retiring intent precedes source unlink. Exact original
inode/metadata/xattrs, unchanged manifest, accepted backings and no incoming/open
consumers are rechecked before unlink. Only that exact selected builder file can
be removed. Checkpoint JSONs, target images/archives, active/current/accepted
backings, source archives, ISOs and all unrelated project/host files stay intact.

The new private context is
`.local/phase2/cold-checkpoint-compression-mvp-builders-1`. Its result preserves
raw xattrs, original mode/UID/GID/atime/mtime, source/archive identities and SHA,
full roundtrip proof, absolute graph and actual free-space delta. Archives remain
beside their original checkpoints under the existing private `.local/vm` tree.
The absolute100GiB+512MiB reserve is retained throughout output streaming; initial
and per-write margins are additional. The free-space goal is that floor plus20GiB
for upcoming bounded image growth, not a promised result or permission to retire
anything else. No generic path/profile or automatic retry is accepted.

Compressed representations are explicitly not directly bootable. Preserve the
original checkpoint manifests byte-for-byte; the receipt records unavailable
original builder names and recovery. To recover, first verify archive SHA, then
stream-decompress into a NEW `.part` at the exact absent original source path
with sufficient capacity. Verify original full image SHA/size, restore recorded
mode/UID/GID/xattrs/atime/mtime, fsync, rename and run read-only QEMU check in the
original `/vm` mapping before use. Retain the gzip until verified recovery.
Existing/partial custody contexts require actual outcome inspection; this helper
never restores a VM, overwrites an image or replays an interrupted retirement.
