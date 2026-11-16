# Package-artifact prerelease bootstrap

This procedure resolves the final-origin qualification dependency described in
[ADR0247](adr/0247-package-repository-before-acquisition-qualification.md).
`scripts/package_release.py` prepares/verifies local custody only. It never
signs, uploads, publishes, installs, changes story state or makes Setup available.
The existing `phase2_release.py` remains the final-ISO/G2 path.

## Inputs and review

First build the actual native package archives and
[flat signed repository](native-archive-artifact-glue.md). Keep the repository
export directory limited to its original exact flat assets plus Release.gpg and
InRelease. Put the corresponding-source archives, license bundle, package testing
guide and SHA256SUMS outside it. No credentials, private signer context, provider
keys, models, user state, guest images or build-root copy belong in public assets.

The guide must clearly limit use to disposable Toddy qualification systems, record
exact archive/runtime/native build scope and limitations, describe signed-APT
verification, source/licenses and safe recovery, and state that no desktop ISO,
G2/full-flow qualification, automatic activation or assistant authority is supplied.
Archive build/crypto success is not an installed-user acquisition acceptance.

The coordinator chooses and creates a real immutable tag at the reviewed source
commit. The intended first tag is v0.2.0-preview.1. Publish no placeholder/example
URL. Create a request outside tracked public metadata with exactly:

```text
version: 1
tag: actual preview tag
source_commit: its full actual Git commit
release_url: https://github.com/markaraujo/toddy-os/releases/tag/ACTUAL_TAG
repository_directory: canonical absolute signed export directory
source_review: {path: docs/evidence/ACTUAL_REVIEW.json, sha256: actual digest}
artifacts: [{role, path: canonical absolute local file, url: actual planned release asset URL}, ...]
```

Every repository file has role repository, including archive-export.json,
Packages, Packages.gz, Release, Release.gpg, InRelease, public key/trust, every
SHA-named native archive and exported legal file. Additional roles are source
(one or more corresponding-source archives), project-source (one exact tagged
project source snapshot), inventory (one public corresponding-source/component
inventory), licenses (one or more exact legal
bundles), guide (one package qualification guide), checksums (exactly SHA256SUMS).
All assets use flat unique names and the actual same-tag GitHub download route.
No ISO/img/qcow2 is accepted. All source, project snapshot and inventory assets must actually be attached;
upstream URLs alone are not an alternative. Split large source bundles into
reviewed flat assets below GitHub's per-asset limit, accounting every selected
source hash, original project input, NPM archive and required notice. Do not
bundle the private .local tree. SHA256SUMS lists **every other attached asset**
exactly once; it does not list itself. Nothing needs an ISO/G2-completed flag.

Commit the actual review at the referenced evidence path before preparation. Its
exact fields are:

```text
version: 1
scope: native-package-source-license-review
source_commit: actual tagged source commit
packages: actual ordered native repository rows, each with name/version/architecture/
          archive_sha256/component_record_sha256/recipe_sha256
source_assets: [{name, sha256, bytes}, ...] matching role source in request order
project_source_assets: [{name, sha256, bytes}] matching role project-source
inventory_assets: [{name, sha256, bytes}] matching role inventory
license_assets: [{name, sha256, bytes}, ...] matching role licenses in request order
reviewed: true, only after the actual source/license review
```

Derive package rows from the actual archive-export.json; do not invent installed
or runtime qualification. Review correspondence against its actual original
source manifests/recipe closures and public legal files. The tool independently
verifies both real repository signatures against public pins, finite current
Release, identical InRelease plaintext, index/archive hash/size/control custody,
and the exact full repository attachment set. A signed export alone does not
prove complete corresponding-source compliance; the retained review is required.

With reviewed inputs committed and clean checkout:

```sh
python3 scripts/package_release.py prepare \
  --request "$REQUEST" --output "$NEW_PREPARED_RECEIPT"
```

The new receipt says package-publication-unverified and includes no available
release claim. No output is overwritten. It leaves status/G2 and portal unchanged.

## Separate actual publication and verification

The parent creates the draft prerelease at the actual tag, uploads exactly the
reviewed assets and source/licenses, and reviews the package-only release notes.
The notes must explicitly say that the desktop ISO, G2 and installed-user
acquisition qualification are pending. Publish this narrowly scoped package
artifact milestone through the authorized release workflow. This step uses the
parent's publishing session, never installed assistant credentials.

After actual publication, retain the actual GitHub release response under a new
committed docs/evidence path. Download **every** asset through its public
browser_download_url into a separate canonical directory, retaining actual
network exits/route evidence. A draft/private response, samefile link or mismatched
server digest/size fails. Then run:

```sh
python3 scripts/package_release.py promote \
  --prepared "$NEW_PREPARED_RECEIPT" \
  --github-response "$COMMITTED_ACTUAL_RESPONSE" \
  --downloads "$INDEPENDENT_PUBLIC_DOWNLOADS"
```

This re-verifies unchanged local bytes/signatures/tag/source review, actual
published prerelease asset set and every independent downloaded hash/size. Only
then does it exclusively create config/phase2/public-package-release.json and
regenerate dashboard/site. Commit/push the verified metadata and generated portal
using the authorized workflow, deploy Pages, fetch the deployed page/resources,
and retain the actual deployed six-language package-only scope/link checks.
A missing response/download/legal review never produces public metadata. The
pending-deployment-verification handoff remains truthful until deployment proof
is retained separately. Merely running source fixtures creates no release.

## Qualification after a real origin exists

1. Freeze the actual published Packages/Release/InRelease and public asset URLs.
2. Generate candidates using the **actual HTTPS origin** ending in the selected
   release download tag. The exact source line changes its hash versus file:.
3. Run actual native signed-APT component cases, including real masked-CPU denial
   where required, against those exact source/InRelease/code/trust/package pins.
4. Independently sign a component-qualified preview catalog. Run the real fresh
   absent-agent production helper/Polkit/UI cases, Stop/reconnect/offline/tamper
   and signed revision2 upgrade/remove/new primary reinstall. Assemble mandatory
   retained full-flow evidence; no component-level renaming is accepted.
5. Seal the actual full-flow catalog and run the final publication guard. The
   final ISO may point to the already qualified package repository origin. The
   final ISO/source/native evidence is published later via phase2_release.py.

Do not move the repository to the final ISO tag, replace an archive, add an asset
to this verified exact set, re-sign Release, change trust/code or let metadata
expire and reuse stale evidence. Any pin change needs the affected real
qualification again. Publishing a qualified catalog inside a later ISO is
separate from advertising this earlier package release as acquisition-ready.
The package-only portal block preserves the foundation download and existing
final-ISO block; no B13/G2 completion or stable release label is inferred.
