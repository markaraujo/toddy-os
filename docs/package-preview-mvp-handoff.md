# Current package preview operator handoff

This is a pending operator plan, not published metadata or native acceptance.
The intended package-only tag is `v0.2.0-preview.1`. Keep the actual old
`.local/phase2/revision2-signed-metadata-1/assets/` immutable: it predates legal
content deduplication. The following creates a new primary export. Only the
coordinator runs native commands/signing/publication; preserve its single writer
lock, guards and current operation postconditions before starting another command.

## New primary export

After synchronizing committed source containing the legal deduplication change,
run in the designated guarded outer builder, with no active native writer:

```sh
cd /opt/toddy-build
ISSUED_UNIX=$(date -u +%s)
EXPIRES_UNIX=$((ISSUED_UNIX + 7 * 86400))
python3 -I scripts/build/phase2/archive_metadata.py \
  --projection /mnt/lfs/sources/stage/toddy-image-projection-2/projection.json \
  --projection /mnt/lfs/sources/stage/toddy-image-projection-2/live-projection.json \
  --projection /mnt/lfs/sources/stage/toddy-optional-projection-1/optional-projection.json \
  --additional-components /mnt/lfs/sources/stage/toddy-image-projection-2/additional-components.json \
  --acquisition-record /var/log/toddy/packages/toddy-agent_0.2.0-1+toddy1_all.json \
  --acquisition-record /var/log/toddy/packages/toddy-executor_0.2.0-1+toddy1_all.json \
  --acquisition-record /var/log/toddy/packages/nodejs_24.19.0-1+toddy1_amd64.json \
  --acquisition-record /var/log/toddy/packages/llama-cpp_0.9.0-1+toddy1_amd64.json \
  --issued-unix "$ISSUED_UNIX" --expires-unix "$EXPIRES_UNIX" \
  --capacity-scope native-target \
  --output /mnt/lfs/sources/stage/toddy-package-export-2
```

The optional projection contains exactly seven packages **including**
`toddy-voice-native-catalog`: toddy-voice, whisper-cpp, espeak-ng,
pipewire-audio-tools, toddy-voice-model-base, toddy-voice-native-catalog and
toddy-integrations. Its record custody selects the actual reconciled catalog r1;
never add another guessed catalog record or substitute a stale archive. Curated
agent/executor/Node/llama records remain separate. The exporter revalidates actual
archive/control/legal/provenance bytes and capacity before copying. Preserve
partial/new generations after failures; do not overwrite or repeat uncertain work.

Retain the real command exit and `archive-export.json`. The coordinator separately
signs this exact new Release using the isolated signer and verifies both signatures
with the public-only certificate, following
[native archive preparation](native-archive-artifact-glue.md). Do not inspect or
copy its private signing material. Signing does not qualify acquisition.

## Source assets, actual review and publication

Copy the completed signed export and every referenced native record through
measured custody to canonical host paths. Set the following variables to those
**actual** paths and the reviewed existing Git commit; these are required inputs,
not default filenames or fictional receipts. Use only verified explicit source
caches; the foundation archive argument is optional when all sources are present.

```sh
python3 -I scripts/build/phase2/package_sources.py \
  --repository "$ACTUAL_SIGNED_EXPORT" --records "$ACTUAL_NATIVE_RECORDS" \
  --source-root "$VERIFIED_SELECTED_SOURCE_CACHE" \
  --source-root "$VERIFIED_ADDITIONAL_FROZEN_CACHE" \
  --npm-cache "$VERIFIED_NPM_ARCHIVE_CACHE" \
  --foundation-source-tar "$IMMUTABLE_FOUNDATION_SOURCE_TAR" \
  --source-commit "$TAGGED_SOURCE_COMMIT" \
  --capacity-scope host-export --output "$NEW_SOURCE_ASSET_DIRECTORY"
```

See [corresponding sources](package-corresponding-sources.md) for exact selected
source/NPM/foundation hashes. Missing source custody blocks preparation; upstream
URLs alone do not replace corresponding-source assets.

Copy [request.template.json](templates/package-preview/request.template.json) and
[review.template.json](templates/package-preview/review.template.json) to private
operator paths. Their nulls/empty arrays/false deliberately fail production
validation. Fill request artifacts from **every actual** repository file and
source/license/project snapshot/inventory/guide asset, with its exact intended
flat `https://github.com/markaraujo/toddy-os/releases/download/v0.2.0-preview.1/NAME`
route. That route is a publication target until independent retrieval succeeds.
SHA256SUMS must cover every other asset. Derive the review's ordered package rows
from the actual export and source asset hashes/sizes from actual output files.
Set reviewed true only after that review, commit the real review, create the actual
reviewed immutable tag, and use a clean checkout. Total attachments must be at
most1,000 and each strictly below2GiB, including source/license/checksum assets.

```sh
python3 scripts/package_release.py prepare \
  --request "$ACTUAL_REQUEST" --output "$NEW_PREPARED_RECEIPT"
```

Only after this succeeds does the coordinator publish the exact package-only
prerelease through its authorized publishing session. Retain its actual response
in committed evidence and independently download every public asset. Then:

```sh
python3 scripts/package_release.py promote \
  --prepared "$NEW_PREPARED_RECEIPT" \
  --github-response "$ACTUAL_COMMITTED_RESPONSE" \
  --downloads "$INDEPENDENT_PUBLIC_DOWNLOAD_DIRECTORY"
```

Promote alone produces `config/phase2/public-package-release.json` and regenerates
the portal. Never copy the planning-only
[portal handoff template](templates/package-preview/portal-handoff.template.json)
there. Commit/push the actual generated portal changes and verify deployed links
and the package-only block in all six locales. Preserve foundation links and the
separate final ISO/G2 release path. Record actual route/deployment hashes and
remaining limitations in the handoff. No acquisition availability, final ISO,
G2, physical-machine acceptance or automatic activation is implied.

## Signed repository to image inputs

The first remaining image prerequisite is an actual signed repository plus exact
measured generated-cache bindings, not a public package release or an ISO claim.
The signed flat Packages may include optional assets, while the base/live profiles
still exclude acquired agent/runtime/model/voice packages. In the outer builder,
read-only `offline_payload.py requirements --projection ... --records ...` lists
the exact generated paths/input namespaces; its null tool/evidence fields are
**not** valid bindings. Retain and review actual native cache receipts first.

With `ACTUAL_BASE_BINDINGS` and the signed export available, prepare a new base
bundle (this does not install anything):

```sh
python3 -I /opt/toddy-build/scripts/build/phase2/offline_payload.py prepare \
  --profile /mnt/lfs/sources/stage/toddy-image-projection-2/profile.json \
  --projection /mnt/lfs/sources/stage/toddy-image-projection-2/projection.json \
  --records /var/log/toddy/packages --cache /var/cache/toddy/packages \
  --catalog /opt/toddy-build/config/phase2/software-catalog.json \
  --keyring /mnt/lfs/sources/stage/toddy-package-export-2/archive-keyring.gpg \
  --key-sha256 41c8ca50efdcb996d902dd5d5adaf4215354fc184b1636bef3e9a859ea961c77 \
  --release /mnt/lfs/sources/stage/toddy-package-export-2/Release \
  --signature /mnt/lfs/sources/stage/toddy-package-export-2/Release.gpg \
  --packages /mnt/lfs/sources/stage/toddy-package-export-2/Packages \
  --index-path Packages --origin 'Toddy OS' \
  --generated-bindings "$ACTUAL_BASE_BINDINGS" \
  --additional-record "$ACTUAL_ASSISTANT_RECORD" \
  --additional-record "$ACTUAL_BRANDING_RECORD" \
  --output /mnt/lfs/sources/stage/toddy-installer-native-inputs/payload
```

Set the two additional record variables from the exact name/version/architecture
rows in actual projection2 `additional-components.json`, under
`/var/log/toddy/packages`; do not guess versions. The containing fixed input
directory must be privately created and reviewed by the coordinator; the output
payload directory must be absent. Preparation retains guarded capacity and
produces actual manifest/catalog hashes.

**Live preparation currently needs narrow source glue:** actual live projection
already includes assistant/branding, while the existing CLI always requires those
two as additions outside the projection. Adding them again duplicates components;
omitting them fails `payload_unreviewed_additional_roots`. Do not claim the base
CLI works unchanged for live. A fixed trusted live caller must use
`prepare(..., required_additions=())` with exact live-profile/live-projection,
actual live bindings, the same signed repository, no extra components and new
`/mnt/lfs/sources/stage/toddy-live-native-inputs/payload`. The image-glue owner
is handling that seam; it is not a reason to alter the retained actual projection.

Next supply actual reviewed policy, generated-entries, expected-image-manifest
and boot-profile inputs. Follow [native resources](native-image-resources.md)
and [image pipeline](phase2-native-image-pipeline.md): candidate assembly/resource
measurement, independent review, fresh generation2 real finalizer, live transform,
compression/initramfs/ISO, then actual blank-disk and detached-owner boots. No
placeholder map/hash or successful signature substitutes for these prerequisites.
The media driver remains blocked until those actual inputs and receipts exist.
