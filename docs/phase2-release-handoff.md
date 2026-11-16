# Offline Phase 2 release-to-portal handoff

This source utility does not build, tag, upload, publish or deploy anything. No
Phase 2 public metadata row or available ISO is created by adding it. Until a
verified public row exists, the existing foundation download section is returned
byte for byte, with its release, artwork and evidence unchanged. All six approved
portal languages remain supported. Read [RELEASES.md](RELEASES.md) first.

## Actual final inputs, not earlier component acceptance

Use `scripts/phase2_release.py` only after real B01-B12 acceptance and every
required same-final-ISO technical/native/source/legal proof is recorded and
committed. B13 must explicitly be `in_progress` and canonical G2 must remain
`pending`: publication and deployed portal verification are B13 work, so requiring
their completion before preparing the release would be circular. Recorded owner
Phase2 authorization is mandatory; an owner execution hold prevents a new
handoff. The tool never changes status or awards acceptance.
Require a clean checkout and an existing local experimental `v0.*` tag containing
`phase2` or `preview`, pointing to the actual accepted source commit. Stable1.0
promotion is deliberately outside this preview utility.

Keep all intended upload files in private local release custody outside Git. The
request JSON has exactly `version:1`, `tag`, `source_commit` (full40hex),
`release_url`, `g2_evidence:{path,sha256}` and `artifacts`. Each artifact has exactly
`role`, absolute canonical local `path`, and its explicit real GitHub asset `url`.
The tool does not invent tag names, URLs, checksums, receipts or source commits.
All URLs must belong to this repository's exact tag/download paths; filenames
are bounded portable basenames. No example eligible release instance is shipped.

Required artifact roles are `iso`, `checksums`, `source`, `inventory`, `guide`,
`build-guide`, `recovery`, `licenses`. There is one ISO and one checksum file;
source/legal/documentation roles may contain multiple attached parts. The ISO is
stream-hashed with stable file identity/size checks and must have an ISO9660 volume
descriptor. This header check is not boot acceptance. The supplied SHA256SUMS must
list exactly every attached file except itself, with no duplicate or extra name.
The tool hashes the checksum file separately. Corresponding-source completeness,
license terms and reproducibility still require the actual reviewed evidence.

## Retained native G2 envelope

The future G2 JSON must be tracked under `docs/evidence/` and linked by the B13
status evidence list. Its exact fields are:

| Field | Required value |
| --- | --- |
| `version`, `gate`, `state` | `1`, `G2`, `technical-passed-delivery-pending` |
| `source_commit` | Actual accepted source commit, matching the local tag |
| `iso` | Exact `{sha256,bytes}` of the final attached ISO |
| `experimental_preview`, `physical_validation` | `true`, `pending` |
| `native_package_manifest` | `{path,sha256}` of retained actual package inventory, byte-identical to the attached inventory artifact |
| `native_checks` | The complete named receipt map below |

This immutable technical envelope describes the proofs available before delivery;
it does not claim canonical G2 completion. It remains unchanged when delivery
later completes. A plain `state:passed` envelope is refused at this boundary.

The native inventory has a nonempty `components` list. Every unique component
retains its actual `name`, `version`, `archive_sha256`,
`component_record_sha256`, `recipe_sha256` and `sources` list. Each upstream source
retains at least its filename and SHA256. Original project components can have an
empty source archive list with their existing recipe/owned source-manifest
provenance. This transport validator does not replace the native dependency,
source/legal closure or independent whole-image audits.

Required check IDs are `installed-boot`, `install`, `credential-privilege`,
`cancel-replay`, `recovery`, `offline-base`, `acquired-experience`, `hygiene`,
`browser`, `profile-harness`, `bios-installed-detached-boot`,
`uefi-installed-detached-boot`, `native-acquisition-full-flow`, `owner-setup`, and
`source-license-inventory`. Each entry is exactly `{state:"passed",path,sha256}`
and refers to a retained tracked actual final-native receipt. Each referenced
JSON binds `final_iso:{sha256,bytes}`, `source_commit`, `native_guest:true` and
`all_required_checks_passed:true` to that SAME final release candidate. These
fields summarize reviewed actual receipts; never manufacture them from source
fixtures, a draft root or a successful component build. Keep the actual child
reports/log identities and postconditions in those receipts as well.

The two firmware receipts additionally require actual `firmware:"bios"` or
`"uefi"`, `installed_boot:true`, `installation_media_detached:true`. An earlier
B02 boot or an attached live installation medium cannot satisfy them. Actual
Calamares installation/owner setup, no-replay/recovery and full acquired-experience
scope remain distinct named checks, not inferred from a boot alone.

The acquisition receipt additionally retains `native_acquisition_guard` with
exact `script_sha256`, actual integer `exit:0`, and the actual `result` from
[scripts/qualification/native_acquisition_release_guard.py](../scripts/qualification/native_acquisition_release_guard.py).
The script hash must match the committed guard. Its actual result must report
`all_advertised_entries_full_flow:true` and `expected_public_trust_matched:true`.
Run it against the verified final native root with the publisher's independently
pinned public key SHA/fingerprint. Component-only qualification is refused by
that existing guard. This utility does not run it or turn source flags into a
successful native receipt. Broader physical-machine validation remains pending.

## Prepare locally, then verify actual publication

With the actual request and final evidence already supplied:

```sh
python3 scripts/phase2_release.py prepare \
  --request /absolute/private/release-request.json \
  --output /absolute/private/prepared-release.json
```

The output is a new mode0600 file with state
`prepared-publication-unverified`. It contains private local paths and must not be
committed or published. It cannot expose a current release in the portal.
Existing outputs are never overwritten. Retain immutable ISO/source/legal files
through publication and recheck them after any interruption.

The authorized publisher follows RELEASES.md to publish the real prerelease and
all listed assets. Retain the actual GitHub release API response under
`docs/evidence/`, commit it, and download **every asset through its real public
release route into a separate new directory**. For the actual tag, an authorized
operator can use `gh api repos/markaraujo/toddy-os/releases/tags/ACTUAL_TAG` and
`gh release download ACTUAL_TAG --repo markaraujo/toddy-os --dir ACTUAL_NEW_DIR`;
replace the labels only with real values. Preserve the actual transfer logs and
HTTP results separately. Never pass upload source files as supposed downloads.
Run SHA256SUMS in the download directory as an independent operator check.

Then supply those actual retained inputs:

```sh
python3 scripts/phase2_release.py promote \
  --prepared /absolute/private/prepared-release.json \
  --github-response /absolute/repository/docs/evidence/ACTUAL_RELEASE_RESPONSE.json \
  --downloads /absolute/private/ACTUAL_PUBLIC_DOWNLOADS
```

Promotion rehashes the original files, rechecks tag/evidence/component pins and
checksum coverage, requires `draft:false` and `prerelease:true`, and compares the
complete actual GitHub asset set, uploaded states, exact URLs, sizes and server
SHA256 digests. It independently hashes each supplied downloaded file and refuses
same-file aliases to upload sources. Network provenance/authenticity and download
logs are the publisher's responsibility; synthetic API fixtures cannot be
presented as real publication. No network request or write is made by the tool.

Only then is NEW `config/phase2/public-release.json` written, without private local
paths. The existing `make dashboard` and `make site` generators run. The download
section retains current classes/layout, foundation and release-history links,
experimental status and physical-validation limits. New fixed source-language
copy has all five translation columns in `ui/translations.js`. Public metadata
and retained G2/GitHub evidence are revalidated on every dashboard/site render.
No new framework, artwork or release record is installed automatically at boot.

## Pages is still a separate real postcondition

The public metadata deliberately says `pages_handoff:pending-deployment-verification`.
It is an immutable artifact-publication receipt, not proof that Pages deployed.
Run `make check`, review the generated page in English and at least one translated
view, then commit/push through the authorized workflow. Verify the actual Pages
run/commit, deployed tag, real ISO/checksum links and translated limits. Record a
separate publication/Pages receipt and journal entry. Only AFTER those actual
postconditions pass may the parent mark B13 completed and canonical G2 passed.
Existing published metadata continues to render with that consistent finished
state; new prepare/promote operations are refused so the completed release stays
immutable. An inconsistent early G2 pass is rejected, and neither the technical
envelope nor a source/API fixture replaces delivery acceptance. Do not close delivery from
an upload, local HTML render, transport acknowledgement or workflow trigger alone.

On partial failure preserve the prepared/public manifest, generated files and
actual logs. Inspect postconditions before another action; do not overwrite a
release, replace a tested asset or rerun an uncertain promotion. A newer release
needs a separately reviewed immutable tag/artifact handoff; this first-Phase2 tool
refuses an existing public row. Foundation fallback and historical receipts are
never deleted to repair a new publication.

Focused source check:

```sh
python3 -m unittest discover -s tests -p test_phase2_release.py -v
```

Its temporary Git repository, tiny ISO header, API response and downloaded files
are explicitly unqualified fixtures, not native boot/G2/publication evidence.
