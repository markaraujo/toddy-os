# Observed MVP live directory recovery

This is a single fixed recovery for the failed resource qualification of
`/sources/stage/toddy-mvp-live-image-1/root`. It preserves the old resource intent,
unpack intent and unpack completion byte for byte. It does not authorize a
retry after accounts, cache tools or loader generation have run.

After controlled source synchronization, the coordinator runs once:

```sh
/opt/toddy-build/scripts/build/phase2/image_native.sh recover-qualify-mvp-live-directories
```

The producer checks the three recorded journal hashes, original producer hash,
manifest/policy identity, root inode/device, every selected owned path, every
exact declared fresh directory, native package database attribution, empty
private/runtime state, and absence of all seven account outputs (including
machine-id). Only the already observed directory stage is eligible. It writes a
new exclusive `resource-directory-recovery-intent.json`; any uncertain later
effect blocks replay. The original intent is never removed or overwritten.

Actual cache and loader commands and resulting maps are generated normally.
Zero blockers still requires independent review. The existing MVP adoption
route pins the additional recovery intent alongside the original journals and
runs the same nine real finalizer checks. No installer acceptance follows from
this recovery. An early UI-only image may retain the unchanged old installer
payload and must disclose `installer_ready: false`; final installation media
requires the corrected installer package.

The first recovery subsequently failed before its first tool could execute:
its native chroot path was wrong. The coordinator independently observed all
seven exact synthetic account files, both exact service links, the empty
lost+found directory, unchanged selected cache outputs and no loader output.
The new fixed continuation is:

```sh
/opt/toddy-build/scripts/build/phase2/image_native.sh recover-qualify-mvp-live-accounts
```

This additionally pins the original recovery intent and the independently
observed whole-tree SHA256. It requires all seven account files with their exact
bytes/modes/owners and single-link custody, and does **not** rewrite them. It
creates the exclusive `resource-account-recovery-intent2.json` before continuing
real producers with the corrected frozen `/usr/sbin/chroot` path. Both older
intents remain intact and are included in later adoption provenance. Any
subsequent uncertain effect blocks this continuation permanently.
