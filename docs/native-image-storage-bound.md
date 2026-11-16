# Native image storage measurements and reserve

`manifest.bytes` retains its existing meaning: expanded regular-file logical
bytes counted per pathname, including hardlink aliases. It is not compressed
archive size and must not be silently changed for installer/disk-plan consumers.
The existing verified archive pass now also records actual member sizes, target
names, local hardlink classes, control bytes and per-package list bytes. Equal
SHA-256 content does not establish an inode relationship.

The additive `storage` object merges selected namespaces with the actual target
filesystem block size. It reports logical path bytes, unique regular bytes,
regular inode/hardlink counts, rounded data, symlink and directory/index/inode
bounds, selected native database staging and largest owned-cache temporary
output. Repeated package directories merge; hardlink classes stay local to their
archive. Fresh runtime directories come from the existing reviewed inventory.
The bound is deliberately conservative allocation accounting, not measured `du`
and not a declaration that generated resources or an installed root are ready.

Before `prepare` creates its destination, it counts every archive, record,
public repository material, catalog/profile/projection, both preparation-state
forms, manifest and actual directory-entry namespace. It checks free bytes
against **16 GiB plus that complete copied-tree bound**. The manifest's bounded
self-description growth is included. An insufficient reserve fails before mkdir;
no copy or partially successful preparation is fabricated.

`image_projection.py` now emits `storage-report.json` during the same archive
verification pass, for offline and live selections. This read-only archive report
needs no invented signed repository or qualification. It explicitly leaves
reviewed generated policy and embedded inputs unresolved; the later actual
signed `prepare` output remains mandatory.

## Capacity evidence and deferred cleanup

The retained H11 custody receipt measured free target bytes at 25,580,957,696,
after both opaque Tar retirements. The mandatory reserve is 17,179,869,184,
leaving 8,401,088,512 bytes at that checkpoint. Other current writes must be
remeasured; this historical figure does not admit a new allocation by itself.
The previous 3-times-logical-plus-512-MiB preflight admitted at most
2,621,405,866 logical payload bytes at that checkpoint, before prepared bundle
copies. Actual selected archive/node measurements must drive the next decision.

No candidate root is retired by this change. Current candidate/finalizer content
snapshots omit mtime and hardlink classes. Matching their hashes cannot establish
an exact reconstructible duplicate. Any future duplicate decision must compare
full actual metadata/link snapshots before a live transform mutates finalized2,
and retain all journals/maps/archives. Expected fresh generated-file timestamp
differences are not permission to relax that equality or delete a candidate.

## Phase admission with measured additional allocations

The source assembler now requires additive measurements from the verified bundle;
it refuses an old/missing storage block or a different filesystem block size.
Its existing envelope remains **16 GiB + 3 times the measured root bound +
512 MiB**. The new root bound includes archive allocation/database/cache staging,
actual reviewed account-file bytes and, for live profiles, the actual signed
base bundle plus existing declared composition metadata, counted at the intended
embedded path. This reserves those real bytes without pretending to install them.
Future native qualification artifacts are explicitly unmeasured and must pass a
separate complete copy preflight when they exist; absent artifacts are never
invented or assigned a successful receipt.

For compression, the actual final full snapshot supplies per-file sizes,
hardlink classes, symlink target lengths and names; actual xattr lengths are
read from the same unchanged image. The two-copy compression/extracted-readback
allowance uses that allocation bound plus the existing 2 GiB margin, above the
16 GiB floor. The unchanged H10 component still independently verifies source,
SquashFS extraction, ACLs, sparse policy and hardlink classes.

Early runtime admission measures the fixed source-owned program/loader closure,
actual script bytes, parent/alias/device namespace and bounded newc headers,
body/padding and gzip overhead. Actual names/schema sizes bound its report
metadata too. The existing 1 GiB allowance is retained as a minimum. A runtime
that cannot fit the existing 256 MiB raw-newc protocol is rejected before staging,
not allowed to fail after copying a large runtime. No old H10 source is changed.

ISO admission still accounts for three new copies: staged input, ISO and full
payload readback. It now rounds actual file/name allocations before multiplying,
and keeps the 2 GiB margin plus 16 GiB reserve. Existing compressed artifacts and
all earlier roots/bundles already consume free space at each admission check;
those retained bytes are not treated as reclaimed.

`isolated.sh` already holds the global native build lock throughout compilation.
The outer image entry additionally recognizes only actual `job.py` harness
records for the dispatch/uncertain interval and refuses one without its terminal
`.exit`. Unrelated custom/historical JSON receipts are not treated as compiler
jobs. This does not restart or reconcile an uncertain compiler automatically.
