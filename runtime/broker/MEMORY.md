# Canonical owner memory integration

`MemoryAPI` binds one actual private `ProfileStore` and its existing SQLite DB to
a current authenticated-owner predicate. It adds no model-facing memory tool,
UID field, credential access, grant or IPC method. Default owner access is denied.
The session service must authenticate the actual peer and choose the profile;
an imported profile or document cannot supply that authority.

CRUD, explicit document adoption and restore use one `BEGIN IMMEDIATE` for the
canonical memory mutation, tombstones/retention, memory generation and validated
current USER/profile revision. `ProfileStore.apply_in_transaction` and
`snapshot_in_transaction` share the connection and preserve existing semantic,
capacity, capability and compare-and-swap checks. USER capacity remains32768bytes.
A full profile revision budget or projection failure rolls back all memory,
generation and profile changes; no partial deletion or silent truncation occurs.

`EMPTY_USER_DOCUMENT` is the common clone/import/reset projection. The marked
Markdown contains a strict JSON object mapping stable preference IDs to text.
The UI should inspect canonical API records, their provenance/expiry and current
revision; raw USER bytes are an editable input/review surface, not a second truth.
`put` is an explicit owner edit and can deliberately revive a deleted ID.
`review_user_document` binds the current displayed document SHA and CAS revision
to an explicitly chosen structured map. `apply_profile` keeps normal validated
config/persona edits, requiring a reviewed candidate hash for changed USER data.
Stale files/imports and old backups never revive tombstoned IDs.

Unstructured manual notes are preserved until explicit owner conversion. They
are never guessed into preferences, discarded, silently copied into another
profile or sent to the model. A conflict with existing canonical values blocks
saved-context egress pending review, rather than sending a possibly deleted old
preference. The known empty shipped example is safe to initialize automatically.
Normal config/persona-only edits preserve memory generation and task profile pins.

The service should wrap its configured runner as
`MemoryEngine(ConfiguredEngine(...), memory_api)`. It supplies current bounded
canonical preferences and source-labeled document excerpts in place of every
raw/pinned USER snapshot. Other task-pinned persona/config bytes remain unchanged.
The same profile ID is required; profile switching needs a separately bound API.
Generation changes and expiry cancel active model work and deny later tool/output
admission even if an engine tries to report completion.

Memory mutation, tool admission and checked output append share one short-lived
in-process gate keyed by canonical profile DB path. No SQLite transaction is held
over a tool callback or provider network wait. A tool already admitted may reach
its safe boundary; concurrent memory edits fail fast with
`memory_effect_or_edit_in_progress_safe_boundary_required`, rather than blocking
the UI, killing a committing write or claiming it was undone. The owner can use
normal broker Stop and retry the edit after that safe boundary. Two API instances
for the same path share the gate. Direct same-UID SQLite tampering or a second
independent writer is outside the one canonical service-writer contract; CLI/GUI
must use the authenticated service.

Export returns an explicit memory-only byte bundle and does not silently mutate
profile/retention state. Expired entries are represented as deleted in its snapshot.
Restore never imports task IDs, active schedules, credentials or executor grants.
The separate profile registry must reset USER on no-memory clone/export/import,
using the common empty projection; copying a stale source USER is unsafe.

Immutable historical/task-pinned profile revisions remain available for explicit
owner recovery and can contain older USER bytes. They are never automatically
rehydrated into current model context or ordinary no-memory exports. Canonical
deletion is not forensic erasure of SQLite pages, historical snapshots, separately
exported backups or text already sent to a provider. Already-sent text cannot be
unsent; already-admitted effects cannot be pretended rolled back. Arbitrary secrets
deliberately pasted into prose cannot be reliably discovered by this store; the
broker must never pass provider/keyring credentials into memory.

Parent integration remains explicit: route memory owner methods and USER changes
through this API, wrap the actual runner, return changed profile revisions to the
UI, handle review/busy/capacity codes, and qualify native authenticated endpoints,
two-user isolation, the fixed lookup fixture and actual cancellation flow. This
source slice does not change service/XML/core or claim B07 acceptance.
