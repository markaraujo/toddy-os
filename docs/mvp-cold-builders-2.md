# Second fixed inactive-builder custody pair

The second profile is limited to two historical builder duplicates in
`.local/vm/checkpoints`: `h07-final-base-builder.qcow2` and
`h09-boot-ready-builder.qcow2`. It preserves their original checkpoint JSON,
corresponding target disks, accepted/current images, source archives and every
existing first-pair receipt. No path argument or arbitrary selection is accepted.

Read-only current facts: both images are below 6.5GB logical size, with combined
allocated bytes 12957429760. Their original manifests bind raw SHA256 values
`a19c5c75dda427a45fffdb33bfbd66f7f5c753ba18abd3dd37a0adf8bf7fb154`
and `8ca06a77eafbd0d7def51bce9a35c470bb8ad1bc4bb66f506ce8fda097f4f316`.
An independent current 74-header absolute graph found no incoming backing edge,
active QEMU attachment or open QEMU consumer. Runtime identity and graph checks
are repeated before actual custody and before unlink; this observation is not a
future deletion authorization after any changed state.

The sole coordinator may inspect, then execute separately:

```sh
python3 scripts/host/phase2_mvp_cold_builders_2.py inspect
python3 scripts/host/phase2_mvp_cold_builders_2.py compress
```

The fixed new context is `.local/phase2/cold-checkpoint-compression-mvp-builders-2`.
A private instance of the exact SHA-pinned original graph/identity guard supplies
the second pair; it cannot rebind the original pair's module or context. The shared
compression protocol retains the existing native-boot/transaction locks, source
OFD lock, exact manifest/inode/mode/owner/nlink metadata, read-only QEMU structure
check, full raw SHA during compression, complete gzip restoration SHA/size check,
compressed SHA recheck, parent fsync and graph recheck before source unlink.

The 100GiB+512MiB host floor remains absolute. The fixed admission target for this
batch is that floor plus 32GiB, not a promise of gain or permission to choose more
files. The two selected images may yield only 7–8GB net; actual gain is unknown
until gzip size and free-space measurements exist. Keep remaining capacity gaps
explicit. Existing archives/partials and uncertain state fail closed. Use the
retained exact restoration instructions; compressed images are not directly
bootable. No compression, deletion, image mutation or native acceptance was
performed by this source preparation.

The nested H06 before-restore builder has no own checkpoint manifest in that
folder and is excluded. Historical targets and current/accepted disk chains are
also excluded; do not widen this source profile to reach a desired capacity number.
