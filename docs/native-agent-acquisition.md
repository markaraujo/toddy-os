# Native agent acquisition without an installed agent

The new setup modules implement an actual signed APT/Dpkg package path independent
of broker/Pi/Node/executor availability. Their default is **unavailable** until the
publisher supplies a genuinely qualified signed native release. No signed release
or native bootstrap acceptance is fabricated by this source slice. Docker,
OpenCode, VS Code/Flatpak and other descriptive candidates remain unavailable.
PendingStore and the legacy Catalog retain their existing deferred-wish behavior.

## Base package integration

The coordinator-owned assistant generator must install these original modules
under `/usr/lib/toddy/setup/`: `acquisition.py`, `releases.py`,
`acquisition_journal.py`, `native_backend.py`, `native_acquire.py`, `platform.py`, `runtime_compat.py`, alongside
unchanged `pending.py`. The base shared namespace also includes `openpgp.py`. Only `native_acquire.py` needs executable mode 0755;
all code must be root-owned without group/world write. Its isolated Python
shebang imports only the fixed `/usr/lib/toddy` namespace. Install the policy at
`/usr/share/polkit-1/actions/io.github.markaraujo.Toddy.AcquireNative.policy`.
The exact pkexec executable annotation is
`/usr/lib/toddy/setup/native_acquire.py`, active `auth_admin`, inactive/other no,
with no retained authorization or root GUI environment. Base requires its already
qualified Python, gpgv, APT/Dpkg, Polkit, logind and `_apt` sandbox account.
The strict installed-OS guard reads root-owned nonwritable ID=toddy os-release
(or its exact canonical /usr/lib/os-release alias) and refuses foreign/live OS
before APT; the user review performs the same local check without Polkit.
The helper and catalog must be present before optional agent/executor acquisition.
This worker does not modify the generator/UI/shared installer handoff module.

The executor package must not contain a .wants enable link. Root service/unit and
D-Bus definitions are permissible for later explicit use, but installing must not
activate services. A native qualification must also confirm that package removal/
upgrade safely handles existing service lifetimes and preserves private user data.
No maintainer scripts, preset/cron/autostart/enable payloads or setuid capabilities
are accepted by this bootstrap route.

## Fixed publisher contract

Public metadata lives at `/usr/share/toddy/software/native/`, owned by root with
no writable/symlinked ancestor or hardlinked files. The source list is the fixed
`/etc/apt/sources.list.d/toddy-native.list`, not a manifest-supplied URL. It must
contain exactly one `deb [signed-by=.../archive-keyring.gpg] URI SUITE [main]` line.
URI is credential-free HTTPS or the explicit verified offline repository at
`file:/usr/share/toddy/software/native/repository`. No trusted=yes option, foreign
repository, owner proxy/credential environment or downloaded shell is accepted.
The entire source-list hash and signed InRelease bytes/size are pinned below.

Required root-owned files:

- `trust.json`: exact fields `version:1`, uppercase primary key `fingerprint`
  (40/64 hex), `keyring_sha256`; `archive-keyring.gpg` is its exact binary public keyring. The shared bounded packet parser rejects
  secret/private, unsupported and truncated packets before gpgv; no signing key
  may be shipped in this directory.
- `releases.json` and detached `releases.json.asc`: gpgv must return exactly the
  pinned valid primary fingerprint. Re-read catalog bytes after verification.
  Catalog fields are `version:1`, monotonic integer `generation`, Unix
  `not_before`/`expires` (at most 31 days), `repository`, `releases` (zero to three, unique curated IDs).
- `repository`: `id:'toddy-native'`, `sources_sha256`, `inrelease_sha256`,
  `inrelease_bytes`. These must describe the actual root source and APT release.
- Release: `id` from the curated table below, stable `artifact_id`, exact `packages`,
  `postconditions`, `terms_sha256`, public aggregate `license`,
  `permissions:['user-agent-service','privileged-executor-without-grant']`,
  `qualification_sha256`, `requires_owner_authorization:true`, `auto_activate:false`.
  Package sets match the exact curated table below. Each has `name`, `version`,
  `architecture` (amd64/all), exact archive `bytes`/`sha256`, `installed_bytes`.
  Derive these from accepted native artifacts/records, not estimates or wishes.
- `postconditions`: hashes for the fixed vital code/unit paths in releases.py's
  POSTCONDITIONS. Root verifies file hash, nonwritable root custody, Dpkg ownership,
  exact installed versions and a clean native audit before recording installed.
- `terms/<terms_sha256>.txt`: exact UTF-8 public legal/source/permission review;
  show it with package versions/sizes/source and a separate unchecked acceptance.
- `qualifications/<qualification_sha256>.json`: exact `version:1`,
  `scope:'installed-native-agent-acquisition'`, `native_result:'passed'`,
  `package_set_sha256`, `checks`, `retained_evidence_sha256`. The package-set hash
  uses pending._encode(packages), including list order. Checks must exactly cover
  REQUIRED_CHECKS in releases.py, all true, backed by actual native evidence.
- `qualifications/<retained_evidence_sha256>.evidence.json`: retained sanitized
  actual native result bytes with the above scope, `environment:'native-installed-user'`,
  `fixture_only:false`, runner/postconditions integer exits 0, and identical
  `package_set_sha256`. Hashes alone or callable/fixture presence are not acceptance.

The publisher must retain the actual native logs/qualification inputs and bind
these report bytes to that accepted release. Test fixtures inject fake verification
in a temporary source API only; the fixed production CLI has no such switch.
Nothing in this repository installs fabricated metadata or a signing key.

## UI/client API

Use `AcquisitionClient(existing_pending_store, progress=callback)` from
`toddy.setup.acquisition` in one bounded UI worker. `review()` is unprivileged,
local and harmless offline; it never invokes Polkit/network/secret storage. It
returns unavailable, reconciliation_required, packages_present or review_required,
with `can_install`. An available row includes the exact packages/derived closure,
source/revision, download/installed bytes, public license/terms text/hash,
permissions and review hash. Package presence is not working backend readiness.

`install(review, accepted_terms=True)` requires fresh explicit review and invokes
only nonsecret fixed argv:

```text
pkexec /usr/lib/toddy/setup/native_acquire.py install OPERATION_ID agent-backend REVIEW_SHA256 TERMS_SHA256
```

Polkit authenticates the installed owner separately from terms and from later
API/local model/key/grant consent. Root derives caller UID only from pkexec and
checks actual active/unlocked/local logind state; live media/reserved build accounts
are refused. No inherited descriptor >=3 is required. One child reports bounded
NDJSON progress phases and a result. The progress callback runs on the worker;
schedule native UI updates on its normal main loop. It creates no new thread or
repeated PAM prompt by itself.

`action('status'|'cancel'|'reconcile')` refers only to the private saved operation;
it never calls install again. These explicit owner actions use normal Polkit
rather than a background authentication poll. A lost or invalid reply leaves
`outcome_unknown`; new submissions are held until known-state reconciliation.
The private 0600 acquisition.json is an operation cursor, not a second installer
handoff or reusable authorization. It shares PendingStore's private directory,
lock/CAS/atomic/fsync discipline; pending.json itself remains unchanged.

## Root transaction and recovery

The private 0700 root state at `/var/lib/toddy/setup-acquisition` uses a schema 1
SQLite journal with synchronous durable transitions. Duplicate UID/operation/review
identity returns the original row before current catalog/busy/lock checks. A new
operation cannot bypass a prior uncertain write or roll back catalog generation.
Unknown status opens read-only and creates no state directory, operation or work.

APT uses isolated lists/archive caches and only the fixed signed source. It
updates/downloads separately, requires exact pinned InRelease/signer, snapshots
root-owned indexes, and rejects a solver removal/change outside the reviewed
missing set. Archive size/hash/control identity and forbidden activation payloads
are checked before copying into root-only verified inodes. Catalog, inventory,
owner session and Stop are checked again before durable native write intent.
Actual install uses no download/removal, preserves owner conffiles and never
kills healthy Dpkg for a timer, UI disconnect or Stop. Output is drained with a
bounded retained buffer and never printed as raw package diagnostics.

An interrupted pre-write phase may reconcile as deferred. An interrupted writer
stays uncertain: observe actual package locks/status/code hashes/ownership and
clean audit before installed; otherwise retain needs_reconciliation and use the
native rescue/package recovery route. Never replay the transaction or claim
whole-system rollback. Cancellation can stop before write or wait for a safe
completed transaction; committed effects remain. No model/provider/service/grant
activation follows package completion. Probe actual backend capabilities only
after the user's separate explicit activation/setup choice.

Native qualification remains mandatory: actual installed-owner pkexec/Polkit,
signature/repository tamper refusal, absent-agent install path, exact closure and
file ownership, offline failure, safe Stop, crash/reconnect reconciliation, real
upgrade/remove/recovery and no automatic service/model/key/grant activation.

## Curated local runtime extension

The same agent-independent installed-owner flow also supports these separate
unchecked reviews. It does not require a broker, model or existing engine:

| Release ID | Exact package set | Extra capability |
| --- | --- | --- |
| agent-backend | toddy-agent, toddy-executor, nodejs | No local engine/model implied |
| local-runtime | llama-cpp | Install only the optional engine |
| agent-local | toddy-agent, toddy-executor, nodejs, llama-cpp | Explicit combined closure; every dependency shown |

Use `client.review('local-runtime')` or `client.review('agent-local')`; the rest of
the API/operation deduplication is unchanged. Existing private cursors without a
release_id retain their original agent-backend meaning. No arbitrary package or
release ID is accepted. Root argv carries the chosen curated ID, never a model URL.

Local releases require exact `runtime_profile` equal to RUNTIME_PROFILE in
setup/runtime_compat.py and add native checks `local_runtime_cpu_denial` and
`runtime_profile_compatibility` to the retained qualification. The package is
**llama-cpp 0.9.0-1+toddy1**, exact accepted B03 archive SHA-256
`c528b72c8a9c8a6182fabf82317e71129fed3d63516b25a02c451a5ed15c9287`.
The frozen source commit is cd959bae99ff4bed22bef2604f45241c09bbb8c8, source SHA
fbe74146a3cdc00f706773eb233bc4aedb7d8c3c7e2122440e492a99c1ec5a76.
See [B03 evidence](evidence/B03.md) and the
[frozen model/runtime contract](../config/phase2/local-model.lock.json). Reuse
that runtime/archive proof; do not infer the new acquisition transport passed.

Actual x86_64 CPU flags must contain SSE4.2/AVX/AVX2/FMA/F16C/BMI2 on every
reported processor. User review and the root path check before package work and
again before native write; unsupported systems stay unavailable with no cloud
fallback. Installed cpu-profile.json must retain the exact frozen CPU/no-GPU/
no-native-optimization/no-HTTPS/no-subprocess/no-weights profile. Root verifies
llama-server/completion/profile hashes and native ownership without starting an
engine or loading a model.

The review reports runtime_compatible, runtime_activated:false, model_required,
model_installed:false and automatic_cloud_fallback:false. This is a package/CPU
compatibility assessment, not an inference-memory/readiness claim. Model weights,
resource assessment, license/download consent and activation remain separate user
steps. No GGUF payload may enter this bootstrap; no model is added to the ISO.
The earlier B03 native engine tests remain accepted, while actual installed-owner
APT/Polkit/Stop/recovery for these new release IDs remains pending qualification.
