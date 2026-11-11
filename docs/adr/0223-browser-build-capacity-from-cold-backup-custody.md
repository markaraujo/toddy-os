# ADR-0223: Browser build capacity from an unused cold backup

Status: accepted
Date: 2026-11-11
Scope: B02 development storage prerequisite; no browser acceptance

The frozen BLFS13.1-systemd Firefox153.2.0esr page estimates8.9GB for a build
without tests. The host currently has approximately110GB free and must retain
100GiB. The target also retains its16GiB reserve. No browser build fits the
remaining margin; reserve thresholds and the frozen foundation remain unchanged.

The actual43-image graph has no consumer of the explicitly selected old
`checkpoints/h07-gcc-tested-target.qcow2`. It is a cold intermediate checkpoint,
not an active target, backing image or foundation release master. Its current
inode11832380, size34,298,068,992bytes, mtime_ns1793940369084300644, one link and
empty extended-attribute set are fixed preconditions. Allocated space is
25,530,310,656bytes. The original bytes and recovery evidence must remain retained.

Extend the qualified ADR0219 chunk-custody tool with only this explicit
`firefox-capacity` profile and a new custody directory. Preserve the old math
profile and completed receipts. Revalidate the actual image graph, ownership,
identity, structural QEMU check and exclusive file lock before touching this
backup. Record the exact original whole-file digest, producer identity and PID.

Use the existing32MiB archive/fsync/decompression/hash/manifest-before-retirement
protocol unchanged. Rename the source into private custody and retire only
already durably verified ranges. An interrupted operation must reconstruct and
verify its whole original digest before continuing. The original path is not a
bootable image during custody; retain chunks and the sparse source placeholder.
Completion still requires full original-length/digest reconstruction. Never
replay a complete operation or change its inputs after compaction.

Measure the actual recovered capacity before selecting browser scratch size.
Do not preallocate an oversized volume, modify physical disks, change active
backing chains or silently upgrade dependencies. Reuse the existing pinned
Firefox archive and qualified compiler/runtime packages. Browser compilation,
security review, native installation and graphical validation remain separate.
