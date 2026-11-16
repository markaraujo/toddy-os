# Live candidate1 custody before fresh generation2

This second fixed profile resolves a concrete capacity cycle: keeping the fully
expanded live1 candidate while admitting a fresh live2 finalizer can require more
space than the mandatory 16 GiB reserve and three-copy envelope allow. It selects
only `/sources/stage/toddy-live-image-1/root`. It does not wait for a nonexistent
finalizer2, claim the candidate was accepted, delete a journal/map, reduce a
reserve or choose another cache path.

All full archive/member/metadata/ACL/hardlink/decompression and durability rules
in [Offline candidate custody](offline-candidate-root-custody.md) apply unchanged.
A separate fixed host entry and private context are used:

```sh
python3 scripts/host/phase2_live_candidate_root_custody.py
```

Its fixed host context is `.local/phase2/live-candidate-root-custody-1`, with
`live-candidate1-root.tar.gz`. The guest metadata/intent remains in
`/sources/stage/toddy-live-image-1/root-custody-1` outside the selected root. The
underlying guest helper accepts only the literal `live` profile plus its existing
bounded inspect/export/receipt/metadata/retire actions; there is no caller-defined
root, command or approval flag. Both profile producers must be synced together,
and no producer can be changed while custody is running. Recorded producer and
verifier source bytes are rechecked before retirement.

Before this profile can inspect or export, the coordinator must have actually:

1. Completed the live1 native unpack and resource recipe, with unchanged inode/
   device pins and real configured-package/log/resource receipts, zero blockers
   and all candidate metadata outputs retained.
2. Independently reviewed those actual generated entries, source/account/PAM/
   service/cache attribution and complete expected image, then placed their exact
   bytes in fixed `toddy-live-native-inputs`. The helper does not perform or
   manufacture that review.
3. Supplied every real signed payload/archive/record/profile/catalog/public-trust
   input and protected reviewed policy/generated map/expected-image/boot profile
   consumed by `ReviewedInputs.recheck()` and `finalize_native('live')`.
4. Kept `toddy-live-image-2` wholly absent. Any partial/existing generation2
   requires reconciliation and blocks this specific pre-finalizer profile.

The helper uses the **same** `ReviewedInputs.recheck` implementation on the fixed
builder view of those files, including signature/archive closure, installed
handoff source match, canonical policy and installed kernel/module boot profile.
It requires byte equality of both reviewed maps with the actual candidate
outputs, audits the current candidate against that complete reviewed image and
captures/rechecks the complete input/source pinset. Every prepared bundle file
and resource/assembly consumer source is retained and hash-bound in provenance.
Protected ancestry remains required: ordinary legacy LFS `/sources` ownership
cannot satisfy that validator. Until the source pipeline supplies its private
protected stage view, the command intentionally refuses. Do not chmod the legacy
cache or weaken `secured()` to admit it.

The implementation trace is concrete: `finalize_native(kind)` reads
`ReviewedInputs(kind)` and creates a new `AssemblyRoot(kind + '-reviewed', ...)`
from its signed prepared archives. It never calls `adopt_unpacked`, the first
resource recipe or an old candidate root. No required source1 tree reference is
silently discarded. The captured `image_assemble.py`/`resource_recipe.py` hashes
must remain identical at the retirement boundary. Future code that reintroduces
a source1 dependency requires reviewing eligibility again; an archived candidate
is never promoted into final2.

After the full durable private host proof and repeated current metadata/input/
consumer checks, only the expanded live1 root may be retired. The preserved
candidate journals and complete full-metadata archive permit recovery into a
**new** guarded private native directory using the offline guide. All source
archives, signed bundles, reviewed inputs and future final2 paths are retained.
The live provenance explicitly records `finalizer2_performed: false`, an empty
finalizer-report set and `workflow_boundary:
reviewed-live-inputs-before-fresh-finalizer2`. These are cache-custody facts, not
acceptance. It writes no real/fake finalizer report, installed-ready marker,
composition seal, boot assertion or owner approval receipt.

Now run the original fresh `finalize-live`, reproduce all resources and require
the actual NativeFinalizer/whole-image match. Its failure remains a real failure;
use the retained archive/journals to inspect it without replaying generation1.
Actual live session/media generation, BIOS/UEFI boots, blank-disk install,
recovery, release/privacy/artwork and physical testing gates remain mandatory.
Capacity evidence is the observed allocated snapshot plus the actual guest free
change in its completed retirement receipt; neither static image bounds nor
compressed archive size prove reclaimed host bytes.
