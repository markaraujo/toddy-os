# Private MVP source-review preparation

`package_sources_mvp.py` is separate from the unchanged strict
`package_sources.py`. It creates a private **review draft**, not accepted
corresponding-source output or permission to distribute binaries. It never signs,
uploads, installs, changes package code, weakens the existing publication guard or
claims reproducible binaries/G2. See the
[functional/historical assessment](mvp-corresponding-source-assessment.md).

The producer verifies the actual signed repository and reuses the existing
upstream/NPM/legal/archive/record checks and deterministic bounded tar writer.
Original payload-declared preferred source inputs remain exact committed inputs;
they cannot silently use current replacements. The only external native build
inputs allowed are the exact previous defaults archive/record declared in the
selected defaults source manifest, with independently pinned SHA256 and actual
control/payload/legal verification. There is no arbitrary external-file mode.

The full current tracked project snapshot is included. For historical broad
supporting-script fingerprints, exact committed bytes are retained when found;
otherwise the current committed script is included with both actual/current and
historical hashes. A removed historical path becomes an explicit ledger entry,
never invented source. A missing declared recipe/packager with neither actual
historical nor current source aborts. Per-package mappings identify included
entrypoints, provenance members, actual frozen profile versions where applicable,
and unresolved fingerprints requiring necessity review. The current generic
profile version must match the selected frozen upstream version.

In the main host checkout, after complete actual export/metadata transfer, set
TAGGED_SOURCE_COMMIT to the reviewed full Git commit, including accepted source
recovery ancestry. For the actual export2 inputs:

```sh
python3 -I scripts/build/phase2/package_sources_mvp.py \
  --repository "$PWD/.local/phase2/mvp-package-export-2/assets" \
  --records "$PWD/.local/phase2/mvp-package-export-2/source-inputs/records" \
  --source-root "$PWD/.local/sources" \
  --source-root "$PWD/.local/phase2/voice-native-inputs-1" \
  --npm-cache "$PWD/.local/sources" \
  --native-build-inputs "$PWD/.local/phase2/source-recovery-offline-2" \
  --generated-catalog-projection "$PWD/.local/phase2/mvp-package-export-2/source-inputs/optional-projection.json" \
  --generated-catalog-attestation "$PWD/.local/phase2/mvp-package-export-2/source-inputs/generated-catalog-attestation.json" \
  --source-commit "$TAGGED_SOURCE_COMMIT" \
  --capacity-scope host-export \
  --output "$PWD/.local/phase2/mvp-package-source-review-1"
```

The output must be new. Capacity retains100GiB+512MiB plus all output/headroom.
Interrupted generations remain preserved; do not replay into an uncertain output.
A later signed export must use its matching actual records and catalog proofs,
never old export2 input pins by assumption.

The draft includes deterministic selected-source/license tars, the current project
snapshot, all actual selected native provenance records, a functional-closure
mapping and a complete unresolved historical fingerprint ledger. Its final
source-review-inventory.json has kind native-package-source-review-draft,
publication_eligible false, source-completeness/license reviews pending, and no
historical binary reproduction claim. The existing package release guard rejects
this kind. Every selected package still requires actual source/license review:
necessary compilation/installation scripts, patches, configuration and build
inputs must all be accounted for. Unrelated broad fingerprints can be explained;
a required missing script/input cannot be excused by a ledger or MVP label.
No conversion/promotion operation exists in this producer.
