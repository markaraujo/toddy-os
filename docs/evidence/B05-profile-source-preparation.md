# B05 profile revision source preparation

This is source-only preparation for B05/S24-A, not guest acceptance, an installed
broker, a desktop settings surface or a completed B05 story. B04 remains a
prerequisite for integrated B05 execution. No guest or target image was changed.

`runtime/broker/profiles.py` provides an offline bounded evaluator for the exact
bundled v1 profile schema, installed-capability reference checks and canonical
SHA-256 manifests of submitted config/persona bytes. Unknown schema validation
keywords fail closed. It accepts only config.json and the four named persona
Markdown files; skill/workflow body imports remain unavailable through this API.
No connection value, root grant, executable hook or arbitrary file path is accepted.
Opaque connection references still require independent ownership/resolution checks
by the eventual broker immediately before dispatch.

Validated snapshots and the active pointer commit atomically in the canonical
private per-profile `state.sqlite`. Compare-and-swap rejects concurrent stale
edits. Restoring an immutable revision revalidates its bytes and installed
availability. Task profile pins remain stable across later profile changes and
reopening. The initial cap is eleven complete revisions (active plus ten prior)
and 16 MiB of encoded revision storage. Exhaustion refuses visibly and preserves
all snapshots; safe pruning/retention UI remains future service work. Same-UID
hostile code and root are outside the profile isolation boundary.

Explicit recovery searches a valid retained revision and returns a review-only
snapshot with routing, spending, tools, skills, extensions and automation disabled.
It changes no active pointer, resumes no task and performs no provider call.
External config-file materialization, validated IPC staging/expiry, import/export,
full task lifecycle, retention, managed Stop and actual guest recovery remain
unimplemented by this source slice.

Validation: `python3 -m unittest discover -s tests -p test_profile_store.py -v`
passed nine checks in 0.095 seconds on the development host. They include actual
subprocess exit with an uncommitted pointer/snapshot, SQLite integrity and retained
bytes after reopening, two concurrent writers with exactly one CAS winner,
invalid JSON/schema/reference/path rejection, permissions/hardlink rejection,
count/encoded-byte exhaustion, immutable task pins, explicit safe recovery from a
corrupt current revision, and refusal of unknown future schema rules. These are
actual host SQLite checks, not measured native guest/desktop evidence. Repository
`make check` also passed all 397 checks in 6.160 seconds on this slice.

Next integration: reuse the same per-profile database for tasks and memory;
connect ProfileStore through authenticated user-session service staging and run
the focused native S24-A/profile-restart checks after B04 is accepted. Never
advertise a source-only fixture as installed settings or complete recovery.
