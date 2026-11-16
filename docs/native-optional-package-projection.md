# Optional native archive projection

This source utility prepares no native package and claims no runtime, GUI, signed
acquisition or release acceptance. It never adds voice/model/integrations to the
offline base or ISO. The frozen voice native2 driver, recipes, runtime and existing
prepared/install/audit receipts remain unchanged.

After actual PipeWire2, native2 reconciliation/catalog package install/check and
ordinary optional voice/integrations native package delivery pass, the sole
coordinator syncs these source files through the existing verified input route:

- `scripts/build/phase2/optional_projection.py`
- `scripts/build/phase2/voice_catalog_provenance.py`
- `scripts/build/phase2/image_projection.py`

With all original frozen native inputs still present and no running native job:

```sh
python3 /opt/toddy-build/scripts/build/phase2/optional_projection.py
```

The designated-builder guard and global build lock apply. The command reads
actual configured dpkg inventory and validates exactly `toddy-voice`,
`whisper-cpp`, `espeak-ng`, `toddy-voice-model-base`,
`toddy-voice-native-catalog`, and `toddy-integrations` through the existing native
archive/control/payload/legal verifier. Repeated inventory must match. It writes
only a NEW private `/mnt/lfs/sources/stage/toddy-optional-projection-1` generation
with hash-bound `optional-projection.json`, `generated-catalog-attestation.json`
and `complete.json`; existing output
is never overwritten. Keep the completed generation, all exact native archives/
records, original source/legal inputs, full-root native write audits and retry
proofs. A failure or partial generation requires inspection, never deletion and
blind replay.

The two ordinary original packages use the existing owned source-manifest and
canonical supporting recipe-set checks. No foreign-source exception changes.
The generated catalog has its own exact identity/version/architecture branch:
all producer/helper/wrapper pins must belong to its native recipe closure; actual
unchanged native2 component source/install/check audits, actual new readonly
process job and original failed process, actual catalog creation audit, actual
controlled catalog-package installation audit and independent checked receipt
must revalidate. Its installed payload must consist exclusively of the catalog,
exact real process/qualification documents and reviewed legal/attribution data.
Owned qualification bytes must equal retained actual evidence; self-declared
`status` fields or an extracted archive do not qualify it. Missing/private native
evidence outside the designated builder fails closed.

Supply this projection as an additional `--projection` to the existing
`archive_metadata.py export` command alongside the existing offline/live and
curated-agent inputs, using the same actual records/cache and finite signed
archive policy. This does not broaden `--acquisition-record`, sign metadata,
publish assets, grant owner consent or mark any capability available. Existing
native acquisition full-flow and explicit notice/owner authorization gates apply.

## Source handoff

`package_sources.py` accepts the exact generated catalog through a separate
public data/source verifier. Append these two arguments to the existing signed
repository corresponding-source export command:

```sh
--generated-catalog-attestation /mnt/lfs/sources/stage/toddy-optional-projection-1/generated-catalog-attestation.json \
--generated-catalog-projection /mnt/lfs/sources/stage/toddy-optional-projection-1/optional-projection.json
```

On a host export, use the exact copied generation paths instead. The projection
SHA must match `archive-export.json.inputs["optional-projection.json"]`; its
attestation SHA must match the supplied attestation bytes. Both documents enter
the complete source inventory and source tar assets. Missing arguments, changed
pins or an unrelated projection fail before any source output is created. Do not
supply these arguments when that exact package is absent.

The public source verifier requires exactly catalog version/package/architecture
and the known fixed generator/wrapper hashes, supported by exact historical Git
source. It accepts only the fixed non-executable JSON/legal/attribution payload;
no engine, model, link, arbitrary source-empty package or native permission flag.
Every owned generated catalog/proof/document byte becomes source material in the
bundle. Catalog/process/runtime hashes, bilingual process/Stop data, original
component/legal proof identities and the actual builder's audit/check digest
bindings must agree. The exact original MIT and CC-BY documentation licenses,
reviewed human attribution/README and both attributed human WAV source inputs
must resolve to committed project bytes. The complete recorded native supporting
recipe/helper closure is already retained through the normal exporter.

Public source verification does not rerun private builder audits and never
accepts a temporary extraction as native evidence. Actual builder qualification
is required before the export attestation can be emitted; public source
metadata and signatures plus independent owner review bind that retained actual
attestation and all owned data. Keep the full private native receipts separately.
The signer must review this distinction. Component/process/transport-help proof
still does not replace actual GNOME/PTT/device/playback, optional signed
acquisition, final same-ISO installer/recovery or physical validation.

Focused source checks:

```sh
python3 -m unittest discover -s tests -p test_optional_projection.py -v
python3 -m unittest discover -s tests -p test_image_projection.py -v
python3 -m unittest discover -s tests -p test_voice_catalog_sources.py -v
python3 -m unittest discover -s tests -p test_package_sources.py -v
```
