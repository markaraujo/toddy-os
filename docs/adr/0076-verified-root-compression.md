# ADR-0076: Verify complete Squashfs extraction against its source manifest

- Date: 2026-11-07
- Status: Native component and production refusal checks passed; full image pending
- Builds on: ADR-0047, ADR-0072, ADR-0073 and ADR-0075

## Decision

Add h10/compress_root.py as a separate gated operation after successful root
assembly. Require the preserved image manifest, matching assembly profile/code
generation, accepted installed Squashfs package/tools and exclusive build lock.
Refuse active build/input sync state, unprotected evidence, redirected paths,
existing output generations and overlapping source/output directories. The
component API can use hash-verified private native tools for experiments; the
production CLI cannot use those as package acceptance.

Compare the complete current source snapshot with the preserved assembly
manifest before compression. Use bounded two-processor/256 MiB xz compression,
explicit creation epoch, xattrs, NFS export metadata, no append and fatal error
handling. Explicitly exclude only access/default ACL attributes, whose exact
numeric sidecar is part of the verified image. Reject any other unsupported
xattr namespace before compression. Require enough disk space for the artifact,
native extraction and reserve. Native subprocess groups have a two-hour deadline
and kill-after grace; every action records its durable intent, exit and log hash.

Independently inspect the actual superblock for Squashfs 4.0, xz, requested epoch,
enabled xattrs, NFS export flag and a present in-bounds lookup table. Extract with
native Unsquashfs strict errors. Compare every physical entry, bytes, type/mode,
numeric owners, links, xattrs and hardlink groups before ACL restoration, then
run the actual restoration helper and compare again with all ACLs included.
Source sparse files must remain sparsely allocated. Recheck source/helper/tool
stability before returning complete=true and the artifact size/SHA-256.

Squashfs inode timestamps are uint32 whole seconds. Retain the original manifest
with nanoseconds and explicitly compare the format's second-resolution values;
reject out-of-range timestamps. No source timestamp is rewritten. This format
property does not authorize ignoring content, mode, ownership or xattr changes.

Retain the compressed artifact, extraction, original/extracted/restored manifests,
comparisons, logs and compression.json together. An interrupted or failed
generation is preserved with complete=false; a filename alone proves nothing.
No automatic overwrite/in-place retry exists. Compression success does not accept
credentials, licenses, full dependency closure, ISO generation or boot.

## Native validation

```sh
python3 scripts/host/probe_root_compression.py /mnt/lfs/sources/recovery/squashfs-native-PRINTED_GENERATION
python3 scripts/host/probe_root_assembly_preflight.py
```

Use a completed private source-built tool generation from ADR-0075. The first
probe creates a real metadata fixture containing UTF-8/newline/backslash names,
regular and symlink hardlinks, sparse data, user xattrs, a native executable's
security capability, access/default ACLs and fractional timestamps. Actual native
compression/extraction/restoration passes for all thirteen entries. Two fresh
generations yield the same 61,440-byte artifact in this experiment. This is a
small fixture, not the complete foundation root or a general reproducibility claim.

Fourteen negative cases pass: changed restored bytes, extra extracted entry,
changed symlink, mode, xattr and split hardlink; existing output, installed builder
as image, redirected output, changed assembled source; actual truncated-artifact
extraction failure, incorrect epoch, disabled export metadata and disabled xattrs.
Each corruption checks its specific difference, then resets metadata and passes
a full comparison before the next case. Native package status remains unchanged.
Successful fixtures are removed only after complete reports/logs are captured.

Both actual production compression profiles refuse before output while H07 is
unfinished. The assembly probe now records four premature CLI gates and six
unsafe layouts; actual source readiness still refuses the unfinished shared
Info index. No fake successful assembly journal is used to exercise production.

Successful raw compression report SHA-256:
b113f6fac83ce25c6a9c90ab56c2f255ab4d5bd4c87e987ecb20cbcbc6f11469
(.local/logs/h10-root-compression-<sha256>.log).
Component SHA-256:
f6636271a33886455ee32da8b72031feb7920c7b7b9dc2e12b35a2ebea24da0c.
Gate/readiness report SHA-256:
89bcb6f7a8dd74c8edc916c48436166d3c6c64cb1c0e325730b023f4f5a1e058
(.local/logs/h10-root-assembly-preflight-<sha256>.log).

Initial private harness attempts exposed an unnecessary dependency on QA-transfer
imports and an incorrect /usr/bin/setcap assumption. Compression now uses a
self-contained fsynced JSON writer; the probe invokes actual /usr/sbin/setcap.
No installed input was synchronized to hide these failures. Raw diagnostics and
failed private generations remain retained, including SHA-256
7458de1c53684dd9ced9d6431da4658039ed2562f483231df8894c075ea3bc12
and 244dd21613b3346cdac9ad2a4e23afe2e33bfeaa025cb334cf7c510d275e583e.

## Sources and consequences

Read actual frozen Squashfs-tools 4.7.5 help for error, xattr, timestamp and export
options, plus squashfs-tools/squashfs_fs.h from the verified source archive.
Header SHA-256: 759bc0c284f1aa0fcf269a568f353d0a61de81cec6a1da248c649265461cd04c.
Archive SHA-256: 547b7b7f4d2e44bf91b6fc554664850c69563701deab9fd9cd7e21f694c88ea6.
No version change or new source is introduced. Native tools retain ADR-0075 hashes.

Checking only a successful compressor exit or a checksum would miss altered
extracted metadata or a missing required format feature. Full readback costs
additional disk space and hashing/extraction time but supplies evidence against
the actual declared root. Keep that evidence for each release generation. The
complete foundation root, native installed tool acceptance and Linux 7.1.8
BIOS/UEFI/virtual-USB boot remain required and currently unexecuted.
