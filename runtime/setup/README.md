# Agent-independent setup intent

`pending.py` persists the private non-secret handoff consumed by the later native
setup and installer. It imports only Python standard-library modules; Pi, Node,
D-Bus, GTK, inference and the privileged executor can all be absent.
This source slice is not an installed setup UI or B06/B12 acceptance.

Pass the installed user's actual absolute `$XDG_STATE_HOME/toddy/setup` directory
to `PendingStore`, after its parent directories and real account ownership exist.
The directory is owned by the current UID with mode 0700; the state and lock are
regular single-link files with mode 0600. Symlinks, shared files and stale editor
revisions are refused. The private directory must not be moved or replaced while
open. This is ordinary per-user custody, not protection against arbitrary code of
the same UID or root. Installer transfer from private pre-user staging remains B12.

After verified base installation, `create(installation_id)` creates an empty
`later` manifest only if absent. `load()` returns `(manifest, revision)`; retain
that opaque revision for `save(..., expected_revision=revision)` or
`dismiss(expected_revision=revision)`. A mismatch is `stale_revision`; reload and
present current intent rather than overwriting it. An active controller returns
`setup_busy` immediately, so a native main loop need not block on a lock. Saving
uses a private temporary file, fsync, atomic replacement and directory fsync.
An error after replacement is an uncertain durability result: reload before retry.

The manifest contains schema version, immutable installation ID, catalog-byte
SHA-256 revision, non-secret `ai_choice` (`later`, `api`, `local`), deferred choices,
empty consent receipts and invitation dismissal. Dismissing the first-session
invitation persists once; the ordinary launcher may still open setup. A dismissed
invitation does not delete pending intent. The installer must not create an API
credential, provider connection, model download, grant or package transaction.
Existing API/local hardware/acquisition validation stays in
`runtime/acquisition/choices.py`; saving an AI intention does not activate it.

`Catalog` reads the bundled `config/phase2/software-catalog.json`. Its candidate
IDs validate retained deferred wishes; Git/base requirements and unknown IDs are
rejected. `review(manifest)` reports every such wish as unavailable with
`can_install=false`, including catalog changes. The current catalog has no
qualified releases. This slice rejects nonempty release records until their
trusted metadata verification is implemented. Do not expose unqualified candidates
as selectable installation options. Do not infer `installed` from pending state.

Only a future qualified release route, installed-user review and the shared
native package authorization backend can implement acquisition. Accordingly this
slice refuses artifact guesses, selected/installing/installed states, nonempty
consent receipts, raw errors and unknown fields. It never runs package commands,
networks, reads a secret store or treats a manifest as authorization. Preserve
corrupt state for diagnosis; there is no automatic reset that loses prior intent.

Focused host checks:

```sh
python3 -m unittest discover -s tests -p 'test_setup_pending.py'
python3 -m unittest discover -s tests -p 'test_software_catalog.py'
```

These cover custody, stale editor/double-create refusal, lock contention,
interrupted precommit save, dismissal/reopen, unsafe JSON, secret/grant rejection,
and unavailable catalog behavior. Native GTK/installer handoff, actual account
isolation, verified catalog acquisition and package transactions remain unrun.
