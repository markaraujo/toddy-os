# ADR-0227: Preserve a cold GCC builder backup to recover native-test margin

Status: accepted scoped operation; terminal custody evidence pending
Date: 2026-11-11
Scope: development-host project backup only; no guest/system installation

After preserving the corrected browser source, measured available host storage
is108,321,005,568bytes against the100GiB reserve. This margin cannot support the
next native test overlay or additional retained browser build artifacts safely.
The current browser compiler writes to its fully allocated private raw volume;
it remains healthy and its guest writer must remain undisturbed.

The actual42-image backing graph has no consumer of
`checkpoints/h07-gcc-tested-builder.qcow2`. Select only this unused intermediate
builder backup, not a foundation master/active disk/backing image. Fixed identity:
inode11832378, size5,949,423,616bytes, mtime_ns1793940344780548431, UID1000,
one link, no extended attributes. Its physical allocation is5,913,346,048bytes.
The original archive bytes and recovery evidence must remain available.

Add one exact `native-capacity` selection to the existing qualified32MiB
chunk-custody tool. Keep both old profiles, identities, contexts and completed
receipts unchanged. Before touching this source, recheck graph/identity,
exclusive file lock, structural QEMU check, actual host reserve and exact original
SHA. Each chunk must be archived/fsynced/decompressed/hash verified and durably
recorded before retiring its original range. Verify complete reconstruction
against original length/SHA before terminal success.

Hold the existing cold-compression/native-boot-test locks. No native boot test
may run concurrently, while the independent single-writer guest compiler may
continue. Capture the real producer/PID/start identity and monitor deterministically;
never restart a healthy job. A partial result requires actual archive/source/
process reconciliation and the same producer before any explicit resume.

The source moves into private custody and its old path becomes unavailable.
The hole-only placeholder is not bootable. Recovery reconstructs ordered verified
chunks with adequate free space, then validates the whole original SHA/length and
QEMU image before use. Never retire archives before verified recovery. No physical
disk, active target, foundation master, compiler result or installed payload changes.
Terminal host capacity must be measured, not inferred from expected compression.

Basis: ADR0219/0223 qualified custody protocol and exact current graph/metadata
preflight in the private operation evidence. Focused protocol tests and required
repository checks apply; unchanged compiler/native foundation suites are reused.
