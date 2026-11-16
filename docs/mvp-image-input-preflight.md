# MVP input and assembly preflight

This source review changes only assembly directory creation under the private
`umask 077`: a fresh root receives its required explicit `0755`, while the work
journal and empty `lost+found` remain `0700`. No target operation has been run.

The current fixed input coordinator reads MVP projection1 and signed package
export3. It merges assistant/branding additions only for the offline base, uses
the complete live component union without duplicate additions, and regenerates
policy/boot/cache provenance from the selected native records. Standard inputs
continue using their separate projection2/export2. Required approved artwork is
owned by the actual branding archive; it is not copied from the builder root.

Run in the designated builder, after actual projection/export3 signature custody:

```sh
bash /opt/toddy-build/scripts/build/phase2/image_native.sh inputs-mvp-base-requirements
bash /opt/toddy-build/scripts/build/phase2/image_native.sh inputs-mvp-live-requirements
bash /opt/toddy-build/scripts/build/phase2/image_native.sh inputs-mvp-base-prepare
bash /opt/toddy-build/scripts/build/phase2/image_native.sh inputs-mvp-live-prepare
bash /opt/toddy-build/scripts/build/phase2/image_native.sh mvp-base
bash /opt/toddy-build/scripts/build/phase2/image_native.sh qualify-mvp-base
```

Review the **actual** `toddy-mvp-offline-image-1/candidate-resource-receipt.json`:
require zero blockers, actual commands and exact current input/producer pins.
The owned cache tools are selected by the existing fixed native recipe vocabulary;
requirements provenance does not claim selected-union cache regeneration. Do not
re-run a failed or uncertain generation or edit an owned archive to suppress drift.
After independent review, copy the exact candidate-generated-entries.json and
candidate-clean-image-manifest.json bytes to generated-entries.json and
expected-image-manifest.json in the matching MVP installer input directory.
Keep the originals/receipt and verify both SHA256 pairs. Never substitute an
unreviewed map, old standard input or a fabricated finalizer receipt.

Then run `image_native.sh finalize-mvp-base`. Only its actual matching nine
reports and whole-image verification permit offline candidate1 custody via
`phase2_mvp_offline_candidate_root_custody.py`. Next run `image_native.sh mvp-live`
and `image_native.sh qualify-mvp-live`, independently review that generation's
zero-blocker outputs and place their exact maps in MVP live inputs. If space
requires live candidate1 custody, use its fixed host entry **before** creating
live generation2. Then run `image_native.sh finalize-mvp-live` followed by
`image_native.sh stage-mvp-live`. Fresh generation2 always unpacks the signed
archives; no candidate tree is promoted.

The account projection contains fresh locked service accounts only, clears all
supplementary memberships and rejects inherited human/build/live users. The boot
profile binds the archived 7.1.8-toddy kernel/module namespace and exact virtual
storage modules. No new PAM policy, physical boot claim or source/root copy is
introduced. Every capacity threshold remains unchanged, including the native
16GiB reserve and independent host custody admission. Installer seals/embedded
inputs and the actual ISO/UEFI install/two detached boots remain later steps.
