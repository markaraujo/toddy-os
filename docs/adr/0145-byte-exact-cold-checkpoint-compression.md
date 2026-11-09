# ADR-0145 — Reversible byte-exact cold checkpoint compression

Status: accepted and executed; six images verified, capacity recovered.

## Concrete need

The Phase2 host has about1.5GiB above its100GiB reserve after the qualified
C/C++ tool prerequisites. The remaining Mozilla/GJS chain needs a larger working
budget. The project stores442GiB of historical checkpoint files. Read-only
metadata inspection of47virtual images found six explicit h01/h03/h04/h05/h06
backup candidates not referenced as backing files. Active overlays, foundation
backings, live ISOs, raw evidence and installed payloads remain separate.

## Decision and guards

Compress only the six explicit cold candidates using gzip, stopping when host
free space reaches112GiB. Preserve all raw image bytes and original file metadata
in an ignored custody receipt. No image conversion, content change, repair,
filesystem trim, guest deletion, foundation rebuild or host installation.

Require read-only qemu-img structural check0, regular owner-owned source with
one hard link, unchanged identity, whole-image OFD exclusive lock, and absence of
backing consumers before and immediately before retirement. Bound output by the
actual100GiB host reserve. Verify gzip decompression restores the full original
byte count and SHA256, record compressed SHA256 and fsync before retiring the
uncompressed representation. Preserve mode, uid/gid, xattrs, atime/mtime in the
receipt. Failures retain original or already-verified archive plus exact state;
never rerun a partially completed custody operation blindly.

Small real-file checks must reject damaged gzip/wrong digest and demonstrate an
independent process cannot obtain a conflicting source-image lock. Full-source
roundtrip verification on each actual image is still mandatory, not replaced by
these checks. A compressed checkpoint is unavailable to QEMU until restored.

## Recovery

Read `.local/phase2/cold-checkpoint-compression-1/result.json`. Verify the archive
SHA256, decompress to a NEW `.part` beside the exact original source path (which
must be absent), verify raw byte count and SHA256, restore recorded mode/uid/gid,
xattrs and atime/mtime, fsync, then rename and run qemu-img check before use.
Ensure enough real capacity above reserves first; sparse restoration may preserve
zero runs. Keep the gzip archive. Never pass gzip to QEMU, overwrite an existing
image, or silently rewrite historical checkpoint manifests. Raw content hashes
remain unchanged; historical restore tools require this explicit restoration step.

## Observed result

[Actual evidence](../evidence/B02-cold-checkpoint-compression.json) records six
full image SHA/byte-count gzip roundtrips, preserved metadata, structural checks0,
no backing consumers and exclusive source locks. Host availability increased from
108674478080 to123148398592bytes (14473920512bytes observed gain), above112GiB.
Second-file check first used a host context unable to resolve /vm; that file was
unchanged. Bounded read-only container correction verified already-retired source
postconditions and resumed remaining files without recompressing the first.
No guest filesystem, active/backing/master image, ISO, physical disk or accepted
foundation payload was modified. This is archive proof, not historical boot proof.
