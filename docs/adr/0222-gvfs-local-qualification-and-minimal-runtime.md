# ADR-0222: Gvfs local qualification and minimal runtime selection

Status: accepted
Date: 2026-11-11
Scope: B02 Gvfs packaging; native Trash acceptance remains pending

## Evidence

Installed Files can create/rename/copy local files and move a file into the
user's trash, but browsing `trash:///` fails as unsupported. Gvfs is absent.
The frozen BLFS13.1-systemd `gnome/gvfs.html` selects Gvfs1.60.2. The exact
official archive matched its frozen checksum and was pinned before extraction.
Its isolated release compiler/stage passed without patches or fallback downloads.

The original `test/unit/outputstream.c` local-file invocation passed eleven
cases, then aborted: `/write/append-tell` expects initial position26, while
baseline GLib2.88.3 GLocalVfs reports0. The frozen GLib source
`gio/glocalfileoutputstream.c:_g_local_file_output_stream_append` opens with
`O_APPEND` and no initial seek. This invocation uses GLib's local backend,
not a new Gvfs backend. A separate consumer linked only to the installed GLib
reproduced initial position0 and verified that appending preserves all previous
bytes. Six previously unrun original replace cases subsequently passed.
[Exact evidence](../evidence/B02-gvfs-stage.json) preserves the original failure.

## Decision

Reuse the eleven actual original passes and six remaining passes. Report17
passes and the retained append-position failure, never18passes or a full-suite
pass. Preserve the exact compiler/source/stage and baseline GLib; do not patch
or upgrade it to satisfy this test. The collector verifies unchanged compiler
and stage hashes during its followup. Actual new backend behavior, Trash
browsing/restoration, refusal and privileged mediation still need native proof.
An interrupted native or package operation must be reconciled before any replay.

The full SSH client is absent. Preserve the original compiled SFTP backend and
its mount descriptor in staging, but omit those two entries from the minimal
published runtime and record their hashes. SFTP remains unavailable until its
owned client dependency qualifies. Other compiled backends remain candidates
until their scoped tests pass; inclusion alone does not advertise support.

Keep upstream admin authentication policy unchanged. The active/local wheel
rule allows only starting the helper; the distinct per-client file-operation
action still requires admin authentication. Do not create privileged users,
grant blanket policy, or treat CLI refusal as real privilege mediation proof.

GLib2.88.3 `gio/giomodule.c` scans and loads modules absent from its discovery
cache. Preserve the existing shared GIO cache and verify its hash unchanged;
do not overwrite its other modules with a compiler-local cache. The new stock
SMB schema requires separate owned shared-schema integration before qualifying
that backend. No user settings or credentials are part of these build inputs.
