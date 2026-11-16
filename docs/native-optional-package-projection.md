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

`package_sources.py` currently reconstructs only an owned `source-manifest.json`
for empty-source original packages. It cannot yet export the generated catalog's
corresponding-source/proof bundle, which intentionally has no such manifest.
Its present strict failure is preserved until the corresponding-source extension
is supplied. The new export attestation is emitted only after all actual builder
validators pass and binds the exact native record/archive, owned proof files,
producer and successful native write/check audit digests. The source exporter
must consume this exact retained attestation and extend that exact producer's source
export to retain and verify its actual audit/proof closure and reviewed project
inputs; do not introduce a generic empty-source fallback. Component/process/
transport-help proof still does not replace actual GNOME/PTT/device/playback,
optional signed acquisition or physical validation.

Focused source checks:

```sh
python3 -m unittest discover -s tests -p test_optional_projection.py -v
python3 -m unittest discover -s tests -p test_image_projection.py -v
```
