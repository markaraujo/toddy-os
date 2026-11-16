# Restore the prepared cold installer-capacity checkpoint

The coordinator completed the explicit installer-capacity custody operation on
2026-11-16. All61,737,336,832 original bytes were reconstructed and SHA256 verified
from1840 retained archives before completion. The original target path is absent;
source.custody is hole-only and NOT bootable. Actual host capacity recovered
36,847,177,728bytes (34.3GiB). [Completion receipt](evidence/B12-installer-capacity-custody.json).
The superseded historical H07 services recovery pair remains byte-preserved;
current H13/B02/h07-final/H09 direct recovery/backing images are unchanged.

Candidate: `.local/vm/checkpoints/h07-native-services-target.qcow2`.
Future private context: `.local/phase2/cold-installer-chunk-custody-1`.
The original builder counterpart remains unchanged. Preserve all old custody
receipts/archives and this context until restoration is verified.

The sole coordinator must inspect real operation state, controller identity,
chunks, source path and backing graph before selecting a next action. A complete
receipt cannot be resumed. An interrupted operation requires the exact original
producer script digest; changing code is not authority to replay it. Do not launch
a native boot or second custody controller while the shared locks are held.

## Restoration procedure

1. Stop/verify absence of any QEMU user of the destination and acquire the same
   native-boot/cold-compression locks. Inspect the actual receipt, archive hashes,
   offsets, expected length/digest and metadata. Ensure the original destination
   and its new `.part` name are both absent; never overwrite an existing image.
2. Provision enough measured capacity for the complete original file plus the
   unchanged 100 GiB reserve and 512 MiB margin. Current original length is
   61,737,336,832 bytes. Reconstruction into a regular file may need that entire
   allocation in addition to retained chunks; do not infer fit from its former
   compressed/sparse representation. Do not delete chunks to make it fit.
3. Open the new private `.part` with exclusive creation and mode 0600. Iterate
   receipt chunks in ascending exact contiguous offset order. For every archive,
   check compressed SHA-256 first, then decompressed length and raw SHA-256 against
   its row. Reject gaps, overlaps, duplicate rows, unsupported state or trailing
   bytes. Append those verified raw bytes only. Never read retired ranges from
   the hole-only `source.custody`. Retain all inputs on any failure.
4. Flush/fsync the reconstructed file. Verify its full length and SHA-256 against
   the operation's `bytes` and `source_sha256` and the historical H07 checkpoint
   receipt. This preparation records expected SHA-256
   `536109a5db3f6f2c44620c33f954fc2ce96570636c9a6b33bbc1b708e57785fd`.
   A missing receipt, failed hash or unexpected destination requires investigation;
   no partial image becomes usable.
5. Restore recorded UID/GID and mode from `identity`, recorded `atime_ns` and
   `identity.mtime_ns`, and recorded xattrs (the fixed selection requires an empty
   xattr set). A nonprivileged restorer must already own the correct UID/GID;
   unavailable metadata permissions require the coordinator's authorized action.
   Fsync the file again. Publish without replacement within the same filesystem
   under the held locks: link the verified `.part` to the absent final name
   (atomic failure if it exists), fsync the directory, unlink only this new
   `.part` alias, and fsync the directory again. Keep every custody input. Recheck
   ownership/mode/timestamps and complete length/hash. Retain the chunks.
6. Run read-only `qemu-img check` with the original backing namespace available,
   then verify the original paired checkpoint receipt. This target has no backing;
   its unchanged builder counterpart needs `/vm/builder-base.img` resolution.
   Only after actual checks may the restored original path be exposed for a
   separately authorized restore/boot. Do not replay guest jobs or package
   transactions as part of representation restoration.
7. Record a new restoration receipt with command exits/postconditions and actual
   identities/digests. Preserve the original custody receipt, chunks and sparse
   placeholder. Any later archival cleanup is separate authorization/work.

The focused temporary-file test demonstrates exact ordered archive reconstruction,
mode/mtime retention, absent-destination protection and unchanged archives. It does
not replace the real destination's full SHA/QEMU/paired-checkpoint checks. No restore
command is automatically invoked by repository checks.
