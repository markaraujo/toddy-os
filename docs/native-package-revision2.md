# Frozen-payload native revision2 preparation

`package_revision2.py` supplies the missing artifact prerequisite for
[native full-flow qualification](native-acquisition-full-flow.md). Source tests
produce no native archive, signature, installed status or qualification report.
The builder, separate signer, installed disposable guest and publisher remain
coordinator-controlled. Only public certificate/pins are script inputs.

## Build an actual archive without installing it

In the designated builder, with the current source synchronized and no other
writer, run as root:

```sh
cd /opt/toddy-build
python3 -I scripts/build/phase2/package_revision2.py prepare \
  --primary-record /var/log/toddy/packages/toddy-agent_0.2.0-1+toddy1_all.json \
  --archives /var/cache/toddy/packages --version 0.2.0-1+toddy2
```

The fixed target guard, native backend and exclusive build lock must pass. The
primary must be the actual installed:true native record and matching archive.
The new private stage is
`/mnt/lfs/sources/stage/acquisition-revision-toddy-agent-0.2.0-1+toddy2`.
Existing stages are preserved and refused, including uncertain interrupted work.
Capacity retains16GiB+512MiB plus complete extraction/archive headroom. This is an
unqualified root archive build with full-target before/after verification, not a
claim of qualified optimized build isolation. It invokes actual native
`dpkg-deb` only, never Dpkg installation or a package maintainer script.

Raw extraction preserves original DEBIAN metadata and every runtime, unit,
legal and source-manifest payload entry. Only the control Version line changes;
all other parsed control fields and every payload metadata/hash must match.
The same upstream/version prefix with a greater explicit +toddy revision is
required. The embedded source manifest intentionally identifies the frozen
primary payload; the new native record separately identifies its packaging
revision, helper/recipe closure, original record/archive hashes and unchanged
full-target projection/Dpkg status. Source provenance is revalidated against the
actual archive-owned manifest. The builder retains revision1 installed.

The stage contains both primary archive/record and new archive/record. The new
record honestly says installed:false. `prepared.json` says unsigned and not
runtime-qualified. Never edit those flags to satisfy a downstream consumer.

## Export before installation; sign separately

The separate unsigned exporter re-parses both actual archive/record pairs and
requires exact frozen control/payload/source custody. Actual UTC issue/expiry
seconds must satisfy the public certificate lifetime and maximum31day validity.

```sh
python3 -I scripts/build/phase2/package_revision2.py metadata \
  --record /mnt/lfs/sources/stage/acquisition-revision-toddy-agent-0.2.0-1+toddy2/toddy-agent_0.2.0-1+toddy2_all.json \
  --archives /mnt/lfs/sources/stage/acquisition-revision-toddy-agent-0.2.0-1+toddy2 \
  --output /mnt/lfs/sources/stage/toddy-agent-revision2-export-1 \
  --issued-unix "$ISSUED_UNIX" --expires-unix "$EXPIRES_UNIX" \
  --capacity-scope native-target
```

This emits flat Packages/Packages.gz/Release, public trust/key, unchanged public
legal assets and SHA-named .deb. `revision2-export.json` is deliberately distinct
from the primary `archive-export.json`: it is built-only, unsigned and unqualified.
It cannot authorize the normal acquisition declarations. Thus actual signed APT
artifact2 can exist **before** the owner installs it; installed:true is not a
signing prerequisite. No signing material enters either builder or guest.

Use the exact parent-controlled signing and public gpgv commands in
[native archive artifact glue](native-archive-artifact-glue.md#separate-parent-controlled-signing)
on this new export, preserving finite Release and asset bytes. Retain actual
signing/verifier exits and custody hashes. The parent selects a concrete reachable
qualification repository; no example URL is publication evidence.

## Actual owner lifecycle in a disposable installed guest

Use the full-flow document's protected root/UUID/current-owner context. Copy only
public verified artifacts, including both canonical record/archive pairs. Keep
the built-only record unchanged outside the final lifecycle directory. Do not
modify the canonical revision1 acquisition source/catalog or trust pins.

The coordinator may stage a separate root-owned signed-by APT source for the
actual artifact2 repository, then run authenticated native APT update and
**download-only** of exactly `toddy-agent=0.2.0-1+toddy2`. Existing executor
transactions intentionally use --no-download; a missing cached archive must fail.
No unauthenticated/trusted=yes option, forced dependency removal, model, key,
provider activation or assistant authorization follows from signing a package.

Explicitly authorize the existing executor owner session policy through its
actual Polkit/PAM path, separately from Setup terms/package consent:

```sh
pkexec /usr/lib/toddy/executor/owner_policy.py grant --mode session --expires-in 3600
```

As the same active owner, use the existing system-bus endpoint
`io.github.markaraujo.Toddy.Executor`, object
`/io/github/markaraujo/Toddy/Executor`, interface
`io.github.markaraujo.Toddy.Executor1`. Plan and dispatch one new operation ID
with kind `package_transaction` and exact JSON:

```json
{"action":"upgrade","packages":["toddy-agent=0.2.0-1+toddy2"]}
```

Retain the real PlanOperation/DispatchOperation/GetOperation results and native
exits. Poll GetOperation read-only; unknown outcomes never authorize repeated
DispatchOperation. Observe the actual package and all unchanged payload entries
before removal, using the source helper copied into the protected native
qualification tools (source tree need not be installed as a runtime package):

```sh
python3 -I /opt/toddy-build/scripts/build/phase2/package_revision2.py observe-installed \
  --record "$PUBLIC_ARTIFACTS/toddy-agent_0.2.0-1+toddy2_all.json" \
  --archives "$PUBLIC_ARTIFACTS" \
  --output /var/lib/toddy/native-acquisition-full-flow-1/lifecycle-artifact2/toddy-agent_0.2.0-1+toddy2_all.json
```

PUBLIC_ARTIFACTS must also contain the canonical primary archive/record pair.
The root full-flow guard runs first. This action verifies actual Dpkg
Status/Version/Architecture, stable native status, empty successful Dpkg audit,
and every installed owned payload entry/hash/link/metadata. Only then does it
write a **new** installed:true record with actual readback pins. It does not
perform a package operation or claim full-flow acceptance. Original false record
and its hash remain immutable. Retain both in component custody.

Use a different new executor operation ID for explicit removal:

```json
{"action":"remove","packages":["toddy-agent"]}
```

Prefer agent so the running executor is not removed. Preserve private user
profiles/keys and prior journal rows; legitimate lifecycle operations append
journal entries, so whole-journal byte identity is not the preservation check.
Stop any explicitly started user service at its safe boundary before upgrade.
Verify no automatic activation after every step. Restore/remove the temporary
artifact2 source under coordinator control and restore the exact original source
and metadata pins before the next Setup review.

Reinstall the declared revision1 set through a **new explicit** production Setup
review, fresh unchecked terms, actual Polkit authorization and new operation ID.
The bootstrap has no upgrade/remove/downgrade mode; removal makes this a fresh
install, never replay of a completed operation. Verify the actual Setup UI
packages_present state/reconnect/private-state recovery. Retain actual lifecycle
execution/postcondition/UI artifacts in the mandatory full-flow schema, including
the actual signed artifact2 repository and both native archive/record pairs.
Missing native execution, signer output, owner authentication, package cache,
revision2 readback or UI receipt remains a blocker. This procedure awards no B/G
acceptance and performs no action merely by being documented.
