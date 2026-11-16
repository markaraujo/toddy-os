# Native APT and acquisition artifact preparation

These source producers create unsigned metadata from actual verified native
records/archives. They do not sign, install, publish, create qualification reports
or make an unqualified release available. The parent coordinator separately owns
the isolated experimental signer and actual native signed-APT/owner-flow proofs.
Only the public certificate and independent pins at
`config/phase2/archive-public-key.gpg` and `archive-public-trust.json` are inputs.
No producer reads an existing signing home, private key or global user keyring.
Public certificate inspection copies only packet-checked public bytes into a new
isolated temporary GPG home, checks actual Ed25519 primary fingerprint/lifetime
against independent pins, and removes that temporary public-only context.

## Unsigned flat repository

After actual native archives/installed records and image projection exist, in
the guarded builder use the current projection at
`/mnt/lfs/sources/stage/toddy-image-projection-2`. Generation1 remains retained with its earlier inventory. Generation2 must be
produced after the actual base recovery and separate audio-tool transaction,
retaining the frozen desktop PipeWire revision; never overwrite or relabel
generation1. Its base/live/additional
component files must match actual `/var/log/toddy/packages` records and
`/var/cache/toddy/packages` archives. The optional records below show the current
source recipe versions; require their actual successful native records, not
source fixtures or a guessed latest file. A missing record is a concrete blocker.
Preserve old/partial export directories; do not rerun into them.

```sh
cd /opt/toddy-build
python3 -I scripts/build/phase2/archive_metadata.py \
  --projection /mnt/lfs/sources/stage/toddy-image-projection-2/projection.json \
  --projection /mnt/lfs/sources/stage/toddy-image-projection-2/live-projection.json \
  --additional-components /mnt/lfs/sources/stage/toddy-image-projection-2/additional-components.json \
  --acquisition-record /var/log/toddy/packages/toddy-agent_0.2.0-1+toddy1_all.json \
  --acquisition-record /var/log/toddy/packages/toddy-executor_0.2.0-1+toddy1_all.json \
  --acquisition-record /var/log/toddy/packages/nodejs_24.19.0-1+toddy1_amd64.json \
  --acquisition-record /var/log/toddy/packages/llama-cpp_0.9.0-1+toddy1_amd64.json \
  --issued-unix "$ISSUED_UNIX" --expires-unix "$EXPIRES_UNIX" \
  --capacity-scope native-target \
  --output /mnt/lfs/sources/stage/toddy-native-archive-export-1
```

The coordinator supplies actual UTC Unix seconds: current issue time, expiry
strictly later/current and at most31days, within the actual public certificate
lifetime. No date/release origin is guessed. `native-target` independently checks
project block-device/serial/stage identity and retains16GiB+512MiB plus all output
bytes/headroom. `host-export` instead retains100GiB+512MiB. A failed space/input
preflight creates no export; an interrupted copy remains incomplete and preserved.
There is no lower-reserve CLI flag, package install or source/root tree copy.

Every archive is verified through the existing offline_payload control, exact
payload, copyright/source-notices and record checks. Original packages require
the existing owned source-manifest/recipe/packager hash closure; the only whitelist
extension is toddy-agent/toddy-executor, which does not admit them to the offline
image. Missing manifests or foreign empty-source records remain blockers.
Package control cannot inject Filename/Size/hash fields or case-duplicate fields.
The exact original public legal files are exported as separate hashed assets;
no license text/SPDX declaration is invented or rewritten.

All release assets are flat:

```text
Packages
Packages.gz
Release
archive-keyring.gpg
native-trust.json
archive-export.json
NAME_ARCHIVE-SHA256.deb
copyright-NAME_COPYRIGHT-SHA256.txt
source-notices-NAME_INDEX-SHA256.json
```

Native logical name/version/architecture stay in Packages; SHA-named archive
assets avoid nested paths, epoch punctuation and unsupported GitHub asset names.
The unsigned export receipt binds every file, actual archive/record/source/legal
identity and exact vital-path hashes. Release binds both exact index hashes/sizes,
finite Date/Valid-Until and `Acquire-By-Hash: no`. Flat APT uses the `./` suite;
there is no unsupported nested by-hash/pool/dists upload layout. Exporting is not
proof that a URL is reachable or native APT accepts it.

## Separate parent-controlled signing

Transfer the exact export with verified hashes through the coordinator's existing
capacity/custody path. The signer is separate from guest/source preparation. The
following are explicit parent operator commands, not calls made by these tools.
`SIGNER_HOME` names the already isolated signer context; never print/archive/copy
its contents or put it under ASSETS. `ASSETS` is the new verified public export.
The independently approved public fingerprint is
453CD646B5F61C586812690F1AF1606035781DB1; recheck it against the reviewed public
pins before use. GPG refuses existing output; do not add an overwrite/retry flag.

```sh
gpg --no-options --homedir "$SIGNER_HOME" --batch \
  --local-user 453CD646B5F61C586812690F1AF1606035781DB1 \
  --digest-algo SHA256 --detach-sign --output "$ASSETS/Release.gpg" "$ASSETS/Release"
gpg --no-options --homedir "$SIGNER_HOME" --batch \
  --local-user 453CD646B5F61C586812690F1AF1606035781DB1 \
  --digest-algo SHA256 --clearsign --output "$ASSETS/InRelease" "$ASSETS/Release"
gpgv --keyring "$ASSETS/archive-keyring.gpg" "$ASSETS/Release.gpg" "$ASSETS/Release"
gpgv --keyring "$ASSETS/archive-keyring.gpg" "$ASSETS/InRelease"
```

Retain actual signing/verification exits and public input hashes without private
material. Detached Release and InRelease must verify to that exact primary and
have identical cleartext. Do not sign a changed index/archive/output generation.
The scripts do not create a key, request a password or make a signing decision.

## Unsigned curated component declarations

Choose the actual public release origin/tag separately. It must be credential-free
HTTPS with no query/fragment, or the exact qualification-only offline origin
`file:/usr/share/toddy/software/native/repository`. There is no default release URL.
`REPOSITORY_ORIGIN` below is an actual parent-selected concrete origin, for example
the project's real GitHub releases/download/TAG endpoint after tag selection, not
a string to publish literally. The URI's content/reachability remains a real
native/publication proof. Changing origin changes source/trust pins and invalidates
qualification for the old source; never relabel an offline test as online proof.

```sh
python3 -I scripts/build/phase2/acquisition_declarations.py \
  --repository "$ASSETS" \
  --base-projection "$PROJECTION/projection.json" \
  --additional-components "$PROJECTION/additional-components.json" \
  --origin "$REPOSITORY_ORIGIN" --generation "$CATALOG_GENERATION" \
  --output "$DECLARATIONS"
```

This verifies the actual two parent signatures, independent public certificate,
finite matching Release, both index representations, every exported asset hash,
exact four curated archive controls/vital paths and native dependency closure
against the separately reviewed offline base. It emits only:

```text
candidate-agent-backend.json
candidate-local-runtime.json
candidate-agent-local.json
native-terms-TERMS-SHA256.txt
toddy-native.list
declarations-export.json
```

Each candidate has exactly the component driver's version/generation/repository/
release schema; package/size/hash/licenses/terms/permissions/postconditions derive
from actual native artifacts. The local runtime retains the frozen B03 exact
archive/runtime/CPU profile. Legal review includes exact original public asset
URLs/hashes, sources and byte counts. Installation, activation, model/network
consent, protected API keys and owner grants remain separate. No terms acceptance,
qualification_sha256, releases.json or native-full-flow report is fabricated.
A valid repository signature alone never makes production NativeCatalog ready.

The parent signs each exact candidate for the root-only component driver:

```sh
gpg --no-options --homedir "$SIGNER_HOME" --batch \
  --local-user 453CD646B5F61C586812690F1AF1606035781DB1 \
  --digest-algo SHA256 --armor --detach-sign \
  --output "$DECLARATIONS/candidate-agent-backend.json.asc" \
  "$DECLARATIONS/candidate-agent-backend.json"
```

Repeat only the explicitly selected other candidate names in their own actual
qualification runs. Stage as root: archive-keyring.gpg at the fixed native
metadata key path, native-trust.json as trust.json, toddy-native.list at the fixed
APT source path, flat native-terms-HASH.txt as terms/HASH.txt, and the selected
candidate/signature as the component context's candidates.json/candidates.json.asc.
Use protected nonwritable root metadata and the existing fixed component context;
no user manifest is authority and no signer context enters the guest. The exported
install map contains only nonsecret paths, not an executing hook.

Follow [the actual component procedure](native-acquisition-qualification.md), then
separately seal genuine component preview metadata and perform the clean-overlay
production helper/UI flow. Final publication still requires the existing
native_acquisition_release_guard.py, exact same package/code/trust pins and actual
native-full-flow evidence. These producers do not bypass that gate or other G2/
ISO/firmware/physical-owner/release-to-portal requirements.
