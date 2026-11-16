# Separate reviewed current-functional source admission

The actual immutable draft remains native-package-source-review-draft with
publication_eligible false. `package_sources_reviewed.py` admits it only through
an external, committed, package-specific coordinator decision. The old strict
source producer/verifier and old release review shape remain unchanged. No draft
kind/flag is renamed, no generic reviewed=true callback is accepted, and no source
review grants runtime/G2 or historical binary reproduction acceptance.

The actual export2 decision is
[coordinator review1](evidence/mvp-source-coordinator-review-1.json), bound to the
[actual technical accounting](evidence/mvp-source-technical-accounting-1.json).
Its scope is export2 and installer version1 only. Changes to an archive, record,
recipe, source inventory, source/project/license asset, technical row, conditions
or package set require new actual accounting and coordinator decisions.

The separate verifier checks the exact committed technical report and every
package's material/license decision, technical row SHA, license basis and required
publication conditions. It independently verifies the current signed repository,
source tar assets and every member/hash/size/safe metadata, complete current Git
snapshot, exact upstream sources, native archive/control/provenance records,
archive-owned source/notice documents, notice-index references, original preferred
inputs, bounded previous-defaults native inputs, NPM SHA512/size/closure, generated
voice attribution, controller references and every historical/current replacement.
Current generic profile upstream versions must match the selected frozen versions.
The historical ledger must exactly account unresolved actual native fingerprints.

The coordinator identity is retained verbatim, not relabeled as personal owner
approval. UTC ISO8601 review timestamps support Z or +00:00, including fractional
seconds. Per-package accepted material/license decisions and exact conditions are
mandatory; a single hold/missing decision refuses admission.

The actual source readback command, after integrating this source, is host-only:

```sh
python3 -I scripts/build/phase2/package_sources_reviewed.py \
  --repository "$PWD/.local/phase2/mvp-package-export-2/assets" \
  --inventory "$PWD/.local/phase2/mvp-package-source-review-1/source-review-inventory.json" \
  --acceptance "$PWD/docs/evidence/mvp-source-coordinator-review-1.json"
```

This produces a verification result, not a signed/public artifact or an install.
The actual independent readback completed successfully for329 packages; the
sanitized coordinator's local log is mvp-source-accepted-verifier-2.log. Focused
refusal tests cover an individual hold/missing decision, changed archive identity,
missing publication condition, generic boolean and false historical claim.

`package_release.py` selects this path only for the typed external acceptance.
Prepare/promote independently reread source assets; portal metadata verifies the
retained exact decision/report/asset pins. All existing package count/size, public
route, source attachment, source-review, signature, source commit, portal and
experimental limitation requirements remain. A verified source gate is not a
published release. Later export5/installer4 requires actual changed-package source
accounting and decisions; this verifier deliberately refuses automatic scope
expansion from export2.
