# Optional acquired-package source staging

`optional_packages.py` stages three separate payloads without network access,
npm/lifecycle execution, archive creation, guest mutation or installation. It
requires a fresh canonical destination and preserves any existing stage. Every
payload records original source hashes, legal notices, explicit ownership,
`offline_base=false`, `installed=false` and `native_archive_built=false`.
All three depend explicitly on `toddy-assistant`, which alone owns the root
`/usr/lib/toddy/__init__.py`, shared parser and protected connection helpers.
They do not bundle another copy or a cyclic runtime alias.

## Agent closure

`agent` owns broker, tools, local/acquisition helpers and the production worker
under `/usr/lib/toddy/{broker,tools,local,acquisition,worker}`. The production Pi
worker and source/configured adapters are actual runtime code, not spike/test
files. The installed worker fallback must exist in the source adapter. Native
Node24.19.0 is a separate already-qualified dependency; no host Node binary is
copied. Agent engine helpers/models remain separate verified optional inputs.

The profile schema, disabled default profile files and local-model contract live
under `/usr/share/toddy/profiles`. Generated session-D-Bus/systemd entries pass
that exact directory via `--defaults`; installation does not enable a user unit,
change account settings, create a connection or grant administration.

The complete Pi1.5/npm closure must match the committed B01 evidence and lock:
88 component locations,87 distinct archives and10,860 original files. The
generator rechecks SHA512 integrity, observed archive SHA256/size, every normalized
archive member, package metadata, per-component complete file-manifest SHA256,
original notices and exact supplemental-notice hashes. Missing/changed custody
blocks the whole agent stage. No partial SDK subset or newly resolved dependency
is substituted. Normalized duplicate members must be byte-identical. Symlinks,
special files, unsafe archive paths and undeclared native ELF/PE/Mach-O payloads
are refused. No archive is downloaded and no install/build hook runs.

Original notices remain beside source in node_modules; supplemental exact notices
and the complete B01 source inventory are retained under
`/usr/share/doc/toddy-agent`. The disclosed upstream omitted-notice limitation is
preserved; the generator does not invent missing upstream copyright text.
The native packager must resolve actual frozen Python/GIO/SQLite/libsecret/Node
package dependencies and retain this first-party source manifest in its release
source/build inventory. A generic outer recipe label is not a substitute for it.

## Voice and integrations

`voice` owns adapters only under `/usr/lib/toddy/voice`. Engine/model/voice
acquisition remains separate with explicit integrity/license consent. No selected
artifact, device, microphone, playback or always-listening configuration is shipped.
Installed package-relative imports support text fallback with every optional
speech artifact absent.

`integrations` stages the actual reviewed adapters under `/usr/lib/toddy/plugins`,
matching the canonical broker import/catalog namespace. It requires toddy-agent
as well as the assistant; canonical skill parsing and independent owner policy
belong to the agent. The agent alone owns its default pinned skill under
`/usr/share/toddy/profiles/profile/skills`. No orphan `/usr/share/toddy/skills`
copy or root namespace alias is emitted.

The package now includes the useful release-reference MCP server source, exact
public B02 metadata projection/manifest/attribution and the harmless local browser
guide. Source metadata lookup never claims current installed package status.
The generator independently checks the entire release projection against the
committed accepted B02 manifest and verifies every declared bundled source hash.
It never executes those sources. A corrupt/incomplete binding blocks staging.

Disabled defaults live under `/usr/share/toddy/plugins`. No qualified receipt,
activation, provider/account credential, browser profile or hook is generated.
`/usr/share/doc/toddy-integrations/activation-inputs.json` records exact manifest,
reader/page hashes and required native proof, with qualification explicitly false.
The native single-writer package transaction must verify signed package/source/
legal/ownership closure and actual target containment/browser behavior before it
creates a root-owned catalog receipt and requests separate owner activation.
A receipt's own-package archive hash must be a separately managed generated path;
it cannot be a circular self-hash embedded in that archive.

The exact production receipt schemas and paths are documented in
[the broker integration contract](../../../runtime/plugins/BROKER.md). The source
stage does not substitute a `qualified:true` marker for native proof. Changes to
Firefox/reader/page or MCP source pins require review; import or installation
alone does not activate an integration. There is no unknown-code unconfined path.

## Commands and validation boundary

Run source-only staging into fresh temporary directories for inspection:

```sh
python3 scripts/build/phase2/optional_packages.py agent --destination /absolute/new-agent-stage \
  --npm-cache /absolute/verified-npm-cache --engine-notices /absolute/verified-notices
python3 scripts/build/phase2/optional_packages.py voice --destination /absolute/new-voice-stage
python3 scripts/build/phase2/optional_packages.py integrations --destination /absolute/new-integrations-stage
python3 -m unittest discover -s tests -p 'test_optional_packages.py' -v
```

When these files are later staged inside the designated builder, first verify
actual guest/mount/disk identity and package ownership using the existing native
transaction workflow. This generator never invokes stage_package.py and supplies
no DEBIAN/control directory or maintainer scripts. Existing native target guards,
archive validation, dependency checks and serialized install/recovery remain
mandatory; nothing here authorizes a host-system installation.

Source tests cover optional ownership/defaults, installed voice imports, missing
or tampered npm custody, native-binary rejection and existing-stage refusal. One
integration ownership fixture uses synthetic module bodies and explicitly real
bundled reference data. The actual-source stage also verifies deterministic
namespace/payload/source hashes and the absence of qualified receipts. Separately, actual committed
agent/integration source plus retained B01 archives were staged and combined with
the assistant/voice payloads for installed-namespace and direct service-help checks.
Those observations establish payload/import custody, not a running native broker,
model task, microphone, plugin confinement, installable image or B13/G2 acceptance.
