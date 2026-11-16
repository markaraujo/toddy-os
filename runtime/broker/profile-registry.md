# Named profile registry

`profile_registry.py` adds an owned bounded catalog around existing canonical
`ProfileStore` databases. It is a source module, not an installed multi-profile
service/UI acceptance claim. It does not modify Service1, dispatch an engine,
activate a task, copy a database, query a credential store or grant privileges.

The registry root is an actual owned0700 directory; `catalog.sqlite` and its
operation lock are regular single-link0600 files. IDs use the existing lower-case
profile contract. Each profile has its own `<root>/<id>/state.sqlite`; canonical
profile revisions/tasks/memory remain there. The catalog contains only profile
publication state, selected-profile generation and task→profile/revision locators.
It never contains persona bytes, provider credentials, conversation or memory.
Same-UID arbitrary code remains outside this logical profile boundary.

`create(id)` uses the reviewed shipped defaults and does not select. `clone`
requires an actual source revision and does not select. `import_bundle`/`import_fd`
creates a new ID only and refuses existing directories; it cannot overwrite a
working profile or activate imported instructions. Explicit `adopt_existing(id)`
registers a verified legacy database without copying/resetting its state and
never selects it. This upgrade-only route is distinct from clone/import, and it
cannot bypass a preparing row's postcondition check.

Create/clone/import reset provider routing and connection references to deferred,
remote spend off, automation/workflow IDs disabled, extensions disabled and saved
history/retention off. Enabled tools reset to installed system-info only and
skills to the installed safe explanatory skill; shell/file-write/admin tools
require fresh explicit owner review before enabling. An existing OS account's
standing grant cannot make an imported tool selection executable. They copy no canonical state/history/memory/grant tables.
SOUL.md/IDENTITY.md/AGENTS.md remain portable user-authored persona text; text is
never executed or promoted to owner policy. USER.md is replaced by the agreed
empty marked `toddy-memory-v1` JSON projection. Stale/deleted preferences cannot
resurrect through that file. Existing legacy USER.md is preserved during explicit
adoption; conversion into canonical memory is a separate reviewed memory action.
Arbitrary secrets deliberately typed into persona prose cannot be automatically
identified/scrubbed; exports exclude credential sources/references and runtime
stores by construction, and their user-authored text still requires owner review.
Memory/history export is a separate explicit API, not a hidden option here.

The current canonical ProfileStore supports exactly config.json and four persona
Markdown files. Unknown paths, skill resources, workflows, executable files,
archives, links and runtime databases are rejected rather than silently imported.
The reset safe installed-skill/tool references still pass the canonical
installed-capability validator; imported enablement is not retained. Unsupported external profile/skill formats remain
unavailable. No new YAML/archive dependency is introduced.

Bundle format is strict UTF-8 JSON with exactly bundle_version, scope, routing,
files and sha256. The scope is profile-without-memory-or-authority; routing is
always deferred-rebind-required. Hashes bind the literal file bytes. Bounds are
8MiB/128 entries overall and the existing per-file limits. Input FDs must be
owned regular files; actual bytes are copied with a before/after identity/size/
mtime/ctime check. Pipes/devices are rejected. Export FDs are0600 sealed memfds
reopened read-only; no unsealed file fallback exists. The caller owns the returned
FD and must close it; import leaves its caller's descriptor open.

Profile creation reserves a preparing metadata row, applies the canonical store,
verifies actual revision/bytes, then publishes ready. A crash after apply can be
reconciled with `reconcile_prepared(id)` by checking the actual postcondition and
publishing metadata only. Missing/partial/mismatched state stays held; no apply,
extraction or task is replayed. Existing stages/directories are preserved. Catalog
schema initialization is atomic, unsupported schemas fail without mutation, and
corrupt ready profiles remain visible as recovery_required while healthy profiles
remain selectable. No automatic deletion/reset or schema downgrade occurs.

## Service integration contract

- `active()` and `select(id, expected_generation=...)` provide selection CAS.
  Selection updates a pointer only. It does not cancel/rebind/restart current work.
- The service must capture the task's actual core/store/revision before dispatch;
  a worker must not look up a mutable global selected core when it starts.
- After canonical task acceptance/pinning, `bind_task(task_id,profile_id)` must
  succeed before dispatch. If locator publication/capacity fails, hold accepted
  work without effects; do not blindly submit a second task. `locate_task` returns
  only actual verified profile/revision bindings. Unknown IDs are never searched
  or replayed across profiles.
- Keep one conflicting guest/native writer and existing executor policy/resource
  locks. Registry operations use a nonblocking operation flock; SQLite writes use
  explicit transactions. Selection does not make parallel package/root writes safe.
- A multi-profile service should route GetTask/Stop/text/ack by its captured
  locator, not the newly selected profile. UI/CLI must label an old running task's
  profile and clear unrelated displayed profile memory/history on selection.
- List/create/clone/select and FD export/import should be additive negotiated
  Service1 methods with actual peer authentication. Validate/Apply retains its
  independent per-profile expected-revision guard. FD imports must not accept an
  arbitrary root filesystem path. No grant/connection is copied on import.

Source checks cover selection CAS/reopen, separate stores, clone/export/import
sanitization, legacy adoption, sealed FDs, traversal/hash/grant/JSON rejection,
old task location after selection, corrupt-profile recovery visibility,
interrupted-create publication without replay and busy/capacity refusal.
Actual Service1/UI/CLI multi-profile behavior, packaging inclusion and native
S24 acceptance remain integration work; a module test is insufficient.

```sh
python3 -m unittest discover -s tests -p 'test_profile_registry.py' -v
```
