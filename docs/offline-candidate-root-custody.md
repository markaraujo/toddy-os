# Offline candidate1 expanded-root custody

This is a source-only, one-profile capacity operation. Its sole removable path is
`/mnt/lfs/sources/stage/toddy-offline-image-1/root` in the guarded candidate.
No live candidate, reviewed/final root, signed bundle, archive, log, manifest,
source tree, accepted foundation/B02 backing or published ISO is selected. No
space has been reclaimed by implementing or fixture-testing this source.

The first profile is eligible only after the matching **actual** generation2
`NativeFinalizer` has completed. It requires generation1 unpack/resource journals,
zero resource blockers, matching independently reviewed payload/policy/generated
map/expected-image inputs, current fixed assembly device/inode pins, real
source-bound generation2 finalization and all nine exact native reports. Current
complete candidate/final-root attribution must match that reviewed expected
image. These checks prove the workflow boundary; the old content-only resource
snapshot is never used as the archive/restore metadata proof.

`finalize_native` creates its new `offline-root-2` from signed archives and the
reviewed files in `toddy-installer-native-inputs`. Its executable path never reads
candidate1's expanded `root`. The generation1 JSON/maps/journals remain outside
that root. Once this first profile's actual generation2 gates hold, the expanded
candidate1 root is optional reconstructible development custody, not an installer
input. Missing generation2 reports/roots block this profile rather than granting
an exception. A separate fixed live1-before-live2 profile is not implemented by
this initial helper; do not substitute paths to work around a capacity cycle.

The coordinator first syncs these committed source helpers into the designated
builder. After inspecting the actual candidate/job/mount state, it can run this
read-only native eligibility/measurement command:

```text
/usr/bin/python3 /opt/toddy-build/scripts/build/phase2/candidate_root_custody.py inspect
```

The result contains actual unique logical file bytes, allocated regular-file
bytes and a conservative complete tar-stream upper bound. Allocation excludes
unknown directory/filesystem effects, so it is potential guest filesystem space,
not a claim of host qcow2 trimming or guaranteed recovery of a static image bound.
The 16 GiB target reserve remains mandatory for custody metadata writes. The
host admission preserves its existing configured reserve plus the whole stream
upper bound and 512 MiB; compression ratios are not assumed.

After reviewing those actual prerequisites, the unprivileged host coordinator
runs the fixed no-argument entry from the committed checkout:

```sh
python3 scripts/host/phase2_candidate_root_custody.py
```

It takes the existing native boot lock and verifies the exact owned candidate
container and accepted backing identities. The guest helper independently takes
the global native build lock and refuses input-sync markers, root transactions
and recognized unclosed compiler jobs. It validates no nested/bind mounts in any
visible process namespace, loop consumers, open files/directories, process
cwd/root references or mappings into the selected inode set. Source files with
external hardlinks, special devices or crossing/redirected filesystem parents
are refused. Those checks repeat at the destructive boundary.

The guest records a new full snapshot with every regular byte SHA, complete
mode/UID/GID, nanosecond mtime, **raw** xattr bytes, symlink text, complete internal
hardlink classes and stable device/inode/ctime identity pins. This is stronger
than the existing resource snapshot. It streams the exact explicit inventory
through authenticated native GNU tar 1.35 with numeric ownership, PAX nanosecond
times, ACLs, all xattrs and sparse support. Explicit sorted NUL-separated paths,
no recursion, fixed PAX header names and omitted access/change-time headers make
the stream deterministic for unchanged required bytes/metadata. Access/change
times are not restored as image metadata; ctime is a source stability guard.
No payload tar is written into the already constrained guest filesystem.

The host writes private 0600 gzip custody under a fresh private 0700
`.local/phase2/offline-candidate-root-custody-1` directory and fsyncs it. It then
**fully** decompresses the archive independently, checks every logical member and
file byte, nsmtime, owner/mode, raw binary xattr and ACL semantics, symlink,
sparse logical byte stream and exact hardlink class. The entire decompressed
stream's byte count/SHA must equal the guest export, including bytes beyond the
member reader's end markers. The host never extracts or executes a root-owned
setuid/capability payload, and no privileged Docker restore is needed. Fixture
checks use public unprivileged temporary files, never a guest or accepted cache.

Only after immutable `host-verified.json`, compressed archive and full
member/decompression proof are durable does the host request the fixed root's
retirement. The guest rechecks full source snapshot, device/inodes, assembly and
reviewed input/report/source bindings and all consumers. A durable once-only
retirement intent precedes fd-safe removal of that exact `root` directory.
Every journal/map/log and the custody snapshot remain in its parent, and final2
is retained. A completed receipt records **actual** before/after guest free bytes;
it makes no host trimming or acceptance claim. Any partial intent/archive/custody
blocks automatic replay. Preserve it and inspect actual postconditions instead
of rerunning an export, deletion or unpack command.

## Recovery and evidence retention

Keep the complete host context: `offline-candidate1-root.tar.gz`, immutable
`host-verified.json`, source metadata, original guest export/retirement receipts,
producer hashes and logs. Verify gzip SHA, complete decompression and the same
member proof again before recovery. The archived root remains explicitly a
candidate; reconstructibility does not make it an accepted image or boot proof.

Recovery must occur only in a **new**, reviewed private directory inside the
same guarded native disposable VM after target identity, mount/consumer checks
and 16 GiB plus measured restored-size/metadata allowance. Never extract this
payload on the executable host workspace, over an installed root, or into the
old generation1 pathname to evade its journal. Stream the retained archive through
native GNU tar using `--extract --gzip --numeric-owner --same-owner
--same-permissions --acls --xattrs --xattrs-include=* --delay-directory-restore`
with the new explicit destination. Nothing from the restored root is executed.
Re-run `candidate_root_archive.snapshot(new_root)` in that VM and compare its
`entries` and `hardlink_groups` exactly with retained `source-metadata.json`;
new device/inode/ctime identities and allocation are expected to differ.
The complete comparison must pass before treating the backup as restored.
Retain new recovery receipts; do not replay old assembly/resource journals.
