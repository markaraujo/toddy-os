# Deterministic selected corresponding-source assets

`package_sources.py` prepares only public unsigned source/license assets and an
inventory for the [package-artifact release](package-artifact-release.md). It
never downloads, builds, installs, signs, publishes or copies a complete cache.
Actual source/license review remains required. This is not native runtime or G2
qualification, nor proof that a public route exists.

## Exact inputs

Require the actual parent-signed flat primary repository, its public pinned
certificate, finite unchanged Packages/Release/InRelease, and **all exact native
records** referenced by archive-export.json. Use records copied with measured
hashes through existing custody; no source fixture record or fake installed flag.
Each selected archive is re-parsed against its native record/payload and record
hash. Every recorded native recipe/helper closure is included by exact content
hash, together with selected upstream sources and original source/legal documents.

Supply explicit canonical source-root directories. The producer looks up only
the exact flat filenames in signed selected source rows and verifies SHA256;
it never recursively enumerates .local or guesses a URL. Missing inputs fail
before creating an output directory. An optional foundation source tar must
match the actual immutable public artifact SHA256
f06ae9910e4f38338f35e472e71c92f0031a1b40c4762c30583e3688d4d30911.
Only selected matching regular members are read into new bundles; unrelated
foundation contents are not copied. This is additional measured custody, not an
upstream-URL substitute. Corrupt or missing members remain blockers.

For toddy-agent, actual archive-owned npm-custody.json requires all88 component
locations/87 distinct archives. Each explicit npm-cache file is selected by its
audited SHA512 name and independently checked by SHA512/SHA256/size. No npm
install/lifecycle script runs. All original retained upstream notices, exact
archive-owned supplemental notices and source-manifest inputs are included.
No omission is allowed merely because an archive is already compiled/installed.

The separate project snapshot comes from the exact explicit existing Git commit,
using a fixed tracked source/documentation/config/art allowlist. Git links,
private cache/keyring/env directories, node_modules, untracked files and foreign
roots are refused or excluded. No working-tree substitution is allowed. Where a
frozen native source input predates that tag, resolve its **exact content SHA**
only from that path's committed ancestry of the supplied commit, retain it as
project-inputs/SHA/path, and name the actual resolved commit in the inventory.
This preserves old native build inputs and the tagged current snapshot together.
A missing historical source/recipe blob blocks output; it never silently takes
current mismatching bytes or searches a private filesystem. Exact-source review
must still account any externally referenced/generated build input not recorded
in the native closure; this tool cannot invent custody for an unrecorded input.

## Operator command

After the coordinator has retained the actual public signed export and canonical
native records, the host-side read-only preparation is:

```sh
python3 -I scripts/build/phase2/package_sources.py \
  --repository "$ACTUAL_SIGNED_EXPORT" \
  --records "$ACTUAL_NATIVE_RECORDS" \
  --source-root "$VERIFIED_SELECTED_SOURCE_CACHE" \
  --source-root "$VERIFIED_ADDITIONAL_FROZEN_CACHE" \
  --npm-cache "$VERIFIED_NPM_ARCHIVE_CACHE" \
  --foundation-source-tar "$IMMUTABLE_FOUNDATION_SOURCE_TAR" \
  --source-commit "$TAGGED_SOURCE_COMMIT" \
  --capacity-scope host-export --output "$NEW_SOURCE_ASSET_DIRECTORY"
```

Use the actual absolute canonical paths; omit the optional foundation argument
if every selected source is independently present. Repeat source-root only for
reviewed actual frozen caches. The host standard cache is the main checkout's
.local/sources, but no directory is copied wholesale. Guest preparation, if
chosen by the sole coordinator, uses native-target and a new fixed stage under
/mnt/lfs/sources/stage, source roots /mnt/lfs/sources and the exactly synchronized
/opt/toddy-build/.local/sources, npm-cache the latter. The producer itself invokes
no guest command/VM transport. It retains100GiB+512MiB on host or16GiB+512MiB on
the guarded native target plus all output bytes/headroom; there is no reserve
lowering flag. Partial generations remain preserved and cannot be overwritten.

## Output and independent readback

The producer writes:

- selected-sources-NNN.tar: deterministic flat release assets with declared
  upstream archives, exact original Git inputs and archive-owned source/notice
  documents. Sorted members, fixed mode/owner/time, no host path metadata.
- source-licenses-NNN.tar: exact original copyright/source/supplemental notice
  bytes, preserving upstream text rather than inventing a single license.
- toddy-project-source.tar: the exact tagged tracked project source snapshot.
- source-inventory.json: native package/record/archive/recipe pins, every selected
  member hash/size/origin, per-package complete coverage, source/license asset
  hashes/sizes and project commit/snapshot identity. URLs are additional only.

Source/license tars split deterministically below1,900,000,000bytes, beneath the
GitHub per-asset limit. A single larger input or oversized project snapshot is a
concrete unsupported split prerequisite and fails; it is never truncated.
Hashes are checked again while copying selected source bytes. The final inventory
is written/fsynced only after all assets succeed. There is no source-only success
receipt for an interrupted generation.

Attach every selected-source tar with source role, every license tar with licenses
role, the project snapshot with project-source role and source-inventory.json
with inventory role. Include every asset in exact release SHA256SUMS, then retain
the source/license review required by package_release.py. Prepare/promote now
independently re-read each tar member/hash/size/metadata, reject extra/missing
coverage and compare every project snapshot entry against the exact Git commit.
The source inventory's archive-export pin must equal the actual signed repository.

Retain actual command exit/output hashes and inspect concrete missing-input
failures. Source tests use tiny unqualified Git/tar fixtures only. Existing
foundation source URLs or package source URLs alone never satisfy attachment of
corresponding source. No real native qualification, source asset or publication
is claimed by this document.

## Current export2 host custody

For the MVP package export, the fixed host collector is
`python3 -I scripts/host/collect_package_source_inputs2.py`. Run it only when the
coordinator's actual designated candidate is running, after the completed export
asset transfer. It reads the exact329 native records and two catalog-proof files
referenced by actual export2 into
`.local/phase2/mvp-package-export-2/source-inputs`, verifies every size/hash and
catalog attestation chain, and publishes its own verified.json last. It performs
no guest writes, install, signing or whole-directory cache transfer. Preserve
partial output and reconcile it; there is no overwrite/retry mode.

A read-only host audit on2026-11-16 matched all342 selected upstream source
filename/SHA rows and all87 distinct audited NPM archives (88 component locations)
against the actual exported agent custody, with no missing files. The producer
independently verifies them again. Native record/catalog-proof transfer is still
required; source-cache presence alone does not supply those records or prove
source review. For this exact selection, no foundation source tar is needed.

After that metadata transfer and actual signing, in the clean main checkout set
TAGGED_SOURCE_COMMIT to the reviewed actual full existing commit and run:

```sh
python3 -I scripts/build/phase2/package_sources.py \
  --repository "$PWD/.local/phase2/mvp-package-export-2/assets" \
  --records "$PWD/.local/phase2/mvp-package-export-2/source-inputs/records" \
  --source-root "$PWD/.local/sources" \
  --source-root "$PWD/.local/phase2/voice-native-inputs-1" \
  --npm-cache "$PWD/.local/sources" \
  --generated-catalog-projection "$PWD/.local/phase2/mvp-package-export-2/source-inputs/optional-projection.json" \
  --generated-catalog-attestation "$PWD/.local/phase2/mvp-package-export-2/source-inputs/generated-catalog-attestation.json" \
  --source-commit "$TAGGED_SOURCE_COMMIT" \
  --capacity-scope host-export \
  --output "$PWD/.local/phase2/mvp-package-sources-2"
```

The two generated-catalog inputs are mandatory for this actual selection. The
export's optional projection hash must bind the supplied projection, which binds
the attestation SHA; arbitrary proof JSON or a renamed catalog receipt is refused.
The destination must be new and the host reserve remains enforced. Missing
historical Git recipe/original input custody remains a concrete blocker even
when every upstream/NPM archive is already cached. The result is corresponding
source assets for actual review/publication, not runtime or installer acceptance.
