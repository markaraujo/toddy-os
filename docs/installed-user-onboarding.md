# Explicit installed-user backend onboarding

The Setup page now has a guided backend panel independent of provider contact.
The earlier deferred invitation remains usable offline. Installing optional
packages does not activate this panel's service, download weights, save a key or
grant root policy. The new source implementation does not establish native
installed-owner acceptance by itself.

## User flow and source interfaces

1. Review/install the required optional closure through the native acquisition
   panel. Missing/unqualified packages remain unavailable, never auto-installed.
2. Explicitly choose Activate installed user agent service. `activate_agent()`
   calls only StartUnit for toddy-agent.service on the actual same-UID user
   systemd manager; it never enables a unit or invokes the root executor. Service
   readiness remains observed through the existing unique-owner session D-Bus
   client with NO_AUTO_START. Activation starts no model or provider request.
3. For API setup, select adapter, HTTPS endpoint, model ID, masked protected key
   and separate explicit API consent. The key entry clears on submission/close;
   undo is disabled. `Onboarding.bind('remote',...)` stores the key in libsecret
   before ValidateProfile/ApplyProfile CAS. No plaintext/env fallback or provider
   request occurs. Remote setup permits later manually consented tasks; their
   existing per-task remote consent remains required and pricing is not guessed.
4. For local setup, explicitly review pinned model/license/size and actual CPU,
   available memory, disk and exact installed frozen llama-cpp runtime profile.
   `LocalModel.review()` uses the existing B03 choices API, actual CPU intersection
   and a resource floor including the frozen proposed model RSS plus512MiB.
   Missing engine or unsupported resources fail before model network activity.
5. Download requires separate exact license and network consent. The existing
   B03 Download implementation verifies exact bytes/SHA256, handles bounded
   interruption/explicit resume and retains private partials. Stop is cooperative
   and never starts inference or falls back to cloud. Existing exact user-owned
   0600 model bytes can be reused without network or another download after
   license consent. `LocalModel.existing()` and binding rehash exact weights.
6. Explicitly apply the verified local backend to the selected profile. The
   local inference helper starts only on a later real task; no model is added to
   the ISO. Doing this later records only the existing harmless invitation intent
   and preserves already configured profiles.

The panel captures the visible profile ID/revision at the Apply action and checks
it against the actual authenticated broker snapshot before writing a connection
or protected key. Profiles continue to use ValidateProfile/ApplyProfile CAS;
no direct profile database writes or implicit administrative grant exist.
The setup worker never submits a model/tool task.

## Private binding transaction and interruption

`runtime/setup/onboarding.py` writes a fresh opaque connection reference under
XDG_CONFIG_HOME/toddy/connections, mode0600 in a0700 private directory. Settings
contain only validated endpoint/model/budget metadata or exact local model path.
A separate0600 onboarding.json in the existing PendingStore directory retains
only profile/revision/reference/adapter/mode/settings hash and phase, never keys,
prompts, endpoints or transcript. An exclusive private lifetime lock serializes
binding, observation and cleanup across instances; atomic writes use the shared
PendingStore lock/fsync discipline.

A definite failure before ApplyProfile removes only the exact freshly written
binding and a successfully saved fresh credential. Credential-save timeout may
have committed: it leaves cleanup_required and its opaque reference, never
retries automatically. Cleanup failure/drift is preserved rather than claiming
rollback. Previously configured connections are not silently overwritten/deleted.

The applying state is durable before issuing ApplyProfile. A lost reply or crash
retains this binding and blocks another bind; no validation/apply is replayed.
Explicit Reconcile reads the original profile through a pinned unique owner and
marks configured only if it references that binding. Otherwise it reports
cleanup_required. Explicit Cleanup refuses a binding still referenced by its
original profile and refuses changed connection bytes; it removes only the
recorded unused binding/protected reference. Connection changes remain owner
configuration, not root authority.

The bounded UI worker runs at most one onboarding operation, coalesces download
progress and exports fixed public status codes. Closing keeps private state open
until the operation reaches its safe boundary. Python/libsecret may retain
transient credential strings; this is not a cryptographic erasure claim.

## Integration and acceptance boundary

The assistant package owns setup/onboarding.py and ui/onboarding.py. The optional
agent retains B03 acquisition/{choices,download}.py and the frozen model contract;
choices now supports package-relative imports alongside its original source CLI.
Missing optional modules yield a harmless unavailable guide before any download.
Root native acquisition permissions and public trust metadata are unchanged.

Source tests use synthetic service/keyring/model bytes. Actual GTK EN/PT panel
construction exercises no backend actions. Coordinator native acceptance still
must demonstrate installed-user service activation, real protected store lock/
failure/success, actual Service1 profile CAS/selection race and unknown-reply
reconciliation, exact preverified B03 weight reuse, real local task/Stop and
separate optional remote provider qualification with human credentials/consent.
No real keyring, provider, host package, guest or model network was touched here.
