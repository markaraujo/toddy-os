# Explicit MVP same-inode adoption

After source synchronization and actual signed MVP inputs, use the fixed commands:

```sh
bash /opt/toddy-build/scripts/build/phase2/image_native.sh mvp-base
bash /opt/toddy-build/scripts/build/phase2/image_native.sh qualify-mvp-base
# Independently inspect actual zero-blocker resource receipt and maps;
# place their exact bytes in generated-entries.json/expected-image-manifest.json.
bash /opt/toddy-build/scripts/build/phase2/image_native.sh adopt-finalize-mvp-base
bash /opt/toddy-build/scripts/build/phase2/image_native.sh mvp-live
bash /opt/toddy-build/scripts/build/phase2/image_native.sh qualify-mvp-live
# Independently review the separate live receipt/maps in the matching live inputs.
bash /opt/toddy-build/scripts/build/phase2/image_native.sh adopt-finalize-mvp-live
bash /opt/toddy-build/scripts/build/phase2/image_native.sh stage-mvp-live
```

The first-unpack intents record `planned_adoption: true` and `allocation_factor: 1`.
Adoption refuses earlier/unplanned candidates, existing destination/intents/report
directories, changed signed inputs/journals, nonzero blockers and mismatched maps.
Candidate roots move atomically to `toddy-mvp-offline-image-2/mvp-offline-root-2`
and `toddy-mvp-live-image-2/mvp-live-root-2`; their inode is retained. The old
candidate journals and new `adoption-intent.json`, `adopted.json` and synthetic
reset intent remain for audit. Do not run candidate1 custody after adoption: the
root has moved, not been deleted or replaced with a host archive.

All nine actual NativeFinalizer reports, independent whole-image validation,
archive/source readback and privacy/account/boot-artifact checks still apply.
`finalized.json` retains its existing consumer schema and is written only after
these checks. Adoption provenance is separate and explicitly records that a fresh
second-root reproduction did not occur. Standard/G2 finalization remains unchanged.
See [ADR-0250](adr/0250-mvp-qualified-root-adoption.md).

On any interrupted intent, ambiguous rename, reset or finalizer failure, preserve
both parents and all reports. `adoption-blocked.json` records the observed path
presence/error type where possible; an earlier intent also blocks replay if the
failure preceded that file. Inspect actual inode/path/hash postconditions before
choosing a separately reviewed recovery/new attempt. Never rerun an uncertain
adoption, reconstruct a success marker or delete a partial finalizer report tree.
This source guide is not actual native/ISO acceptance evidence.
