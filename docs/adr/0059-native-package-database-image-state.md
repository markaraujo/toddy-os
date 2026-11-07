# ADR-0059: Copy quiescent native package metadata into fresh image staging

- Date: 2026-11-06
- Status: Native database-copy component verified; final image integration pending

The source-built image must retain its native package identities, file ownership,
conffile records and checksums. Copying only package payload leaves Dpkg unable
to manage it. Copying the entire mutable builder tree includes historical and
transient state. Use a separate package_database.stage_database component for
the current configured Dpkg state, alongside the independent payload inventory
from ADR-0057. Neither component alone establishes a complete image.

Hold nonblocking POSIX shared locks on the existing native lock-frontend and
lock files while inspecting/copying/read-checking the source. Dpkg 1.22.22 uses
POSIX F_SETLK/F_SETLKW write locks on these files. An active writer causes an
explicit refusal, not a wait/retry loop or deletion of locks. Source checks are
read-only. Never reopen and close a locked inode while holding these locks:
POSIX would release this process's locks, even if the other descriptor remains
open. Snapshot inspection uses metadata and the required empty content for lock
files without reopening them.

Require every native package configured and mapped to its own installed version
record. Exact file-list namespaces and regular-file checksum namespaces must
match those records; conffiles must be unique regular /etc payload entries.
Require native Dpkg audit without diagnostics. Reject unknown database files,
maintainer programs, diversions/overrides/other unreviewed state, pending updates
or triggers, redirects, special/shared files, non-root ownership, unexpected
modes/xattrs and source changes during inspection. This is the currently frozen
script-free foundation package format. Future package features require an
explicit extension and tests, not silently copying newly discovered state.

Copy status and the reviewed info files, preserving bytes/modes/ownership and
timestamps. Omit status-old, lock files and empty trigger queue state; generate
fresh empty database directories. A destination must be under designated guest
temporary/staging storage. It may be absent or contain only the exact reviewed
empty root-owned 0755 directories: the native Dpkg package already owns its
database directory layout, so a fresh root payload copy legitimately creates
those directories first. Preserve this layout without deleting owned paths.
Populated, redirected or unknown destination state is refused before copying.

After copying, require identical native dpkg-query package identities, clean
native dpkg --audit, the same own-record namespace checks, exact copied bytes and
metadata, and unchanged source DB/provenance. Only regular database files are
selected; archived logs, source trees, package cache and account data are not
part of this component.

## Measured native result

python3 scripts/host/probe_package_database.py creates a private stage and copies
the actual configured native database. Current counts are 124 packages,
66,449 file-list entries (including shared directories and each package's root
entry), 52,891 stored MD5 entries, 15 conffile paths, and 261 copied files totaling
7,525,809 bytes. These are metadata counts, not 66,449 distinct installed files.
Native identities are identical and audit is clean. Native ownership queries
correctly identify Bash, Dpkg, Python and Systemd executables from the copied DB.
A second full copy starting with the actual ten Dpkg-owned empty directory
entries retains all of them and yields identical file hashes.

In a disposable root only, the actual native Dpkg writer exits 2 with its lock
refusal while this component holds read locks; no database payload changes.
A separate process holding a POSIX writer lock also refuses acquisition by the
component. Nine negative cases preserve their inputs: pending update, pending
trigger, unknown maintainer program, redirected info file, file-list conflict,
checksum-namespace conflict, populated destination, redirected destination and
destination outside permitted staging storage. The installed source DB remains
unchanged. Successful fixtures are removed after retaining the report.

Final raw report .local/logs/h10-package-database-probe.json SHA-256:
7a18a0b671502e69500a4a39968083d5bfa91fdbd707c82a14f9f3ee61352681.
Complete per-file/report digest:
20c3dbc59c62eee882b4e0772193a8acffcaafb950632725557aefdeaf1f5834.
Component SHA-256:
d9b4e3ae1ab61fb0cc9655fac506fa5a3710c1a646a1f3d657620cba3c75f434.
Immutable hash-suffixed raw reports retain the complete manifest outside Git.

The first actual writer-refusal test exposed an overstrict timestamp assertion:
Dpkg opens both lock files with O_TRUNC before trying F_SETLK. Even a correctly
rejected writer can therefore change empty lock-file mtimes. Preserve the failed
report SHA-256 8141a799bd7ccbdddca34727783c068e0a591d893d16e32897cfe25bf2c79e03
and fixture /mnt/lfs/tmp/toddy-package-database-woon9hfr. The corrected snapshot
ignores only these two empty lock-file mtimes, still requiring regular unshared
root-owned empty files and actual writer exclusion. All database-data hashes and
timestamps remain checked. The repeated real writer test passes.

## Limits, alternatives and sources

Stored MD5 values are retained native metadata, not cryptographic authenticity
evidence. This component checks their namespace and stable transfer; independent
own-archive and actual installed-payload SHA-256 verification remains mandatory.
Native dpkg --audit is not an APT dependency-closure check. The known unfinished
H07 shared Info-index ownership correction is neither changed nor waived here.
Final image staging must use the post-closure database corresponding to the same
payload generation, then account for any native package transformations (such as
the separate Python QA handoff) and recheck actual image contents/dependencies.
No package install/update inside a booted live image or G1 acceptance is claimed.

Alternatives rejected: rebuilding status text manually discards native semantics;
copying every DB file includes historical/interrupted state; copying without
locking permits a mixed transaction; deleting lock files defeats exclusion;
assuming a clean query proves payload integrity confuses distinct acceptance
requirements. Reinstalling every unchanged package is unnecessary for an exact
metadata snapshot and would replay future maintainer actions if added.

Primary sources inspected locally: frozen Dpkg 1.22.22 src/main/enquiry.c
(audit opens msdbrw_readonly), lib/dpkg/file.c (POSIX write locking) and
lib/dpkg/dbmodify.c (lock-file open modes), plus actual native metadata/records.
Source archive dpkg_1.22.22.tar.xz SHA-256:
d5ea9f132deec8030b50ab2a02ade2b49f0c7a195805a302c8301156fe833a57,
pinned in config/supplemental-sources.lock.json. ADR-0032/0035/0036 define the
native backend and remaining metadata closure. H07/H10/G1 remain unaccepted.


## Nested image assembly lock lifetime correction (2026-11-07)

Integration requires one outer read transaction around payload selection/copy
and native database staging. The original context manager opened and closed
its own descriptors on every call. A nested stage_database call therefore
released the process's outer POSIX locks when its inner context closed a second
descriptor for the same inode. This is an implementation defect, not an external
permission failure or a reason to stop the running Berkeley suite.

Reproduced in a disposable database with actual native Dpkg 1.22.22: writer
exit 2 while both contexts were held, then exit 0 after only the inner context
ended, despite the outer context still being active. That command was configure
--pending against a fully configured private copy, never the installed database.
Failure report SHA-256:
1e63f1aad05771ea195927a5e39346fe23f7599848e27f7dd5312c1c56cd8ea4;
fixture /mnt/lfs/tmp/toddy-package-database-heol_10o is preserved.

Share one descriptor pair per process/database device+inode and reference-count
active contexts. A small mutex serializes registry acquisition/release; it is
not held across copying or native queries. Nested calls verify that lock path
inodes still match the held descriptors without reopening them. Only the last
context closes the descriptors. Exceptions decrement the same reference count.
Use the same imported package_database module throughout assembly, and never
open/close/hash these lock inodes through another helper while a transaction is
held. Do not unlink lock files or replace Dpkg locking with unrelated flock.

Alternatives: separate copy windows plus final hash comparison can detect drift
but permit interleaving and waste image work; non-nestable contexts force a
special unlocked database-copy interface that is easy to call incorrectly;
Linux open-file-description locks require a different fcntl ABI/interface.
Retaining the tested Dpkg-compatible POSIX lockf path with shared descriptor
lifetime directly fixes the reproduced problem. Frozen Dpkg lib/dpkg/file.c
F_WRLCK/F_SETLK and dbmodify.c O_RDWR|O_CREAT|O_TRUNC were re-inspected from
the same source archive cited above; no package version or recipe changed.

The corrected native probe passes writer refusal with exit 2 while nested, after
inner exit, and after a controlled inner exception. The writer succeeds with
exit 0 only after the outer context ends. A real 124-package stage_database copy
inside an outer source transaction also retains both locks: separate kernel
write-lock probes report EAGAIN (probe exit 73) for lock-frontend and lock. These
probes open without truncation and perform no installed database operation.
All earlier copy/native-query/audit/ownership checks, nine malformed-state
refusals and opposing writer exclusion pass. The installed database snapshot is
unchanged; complete copied file/report digest remains
20c3dbc59c62eee882b4e0772193a8acffcaafb950632725557aefdeaf1f5834.

Current report .local/logs/h10-package-database-probe.json SHA-256:
2ddb0496a1e67a8bde49fc0fb3e8e96781a859d091be8295a9764c81d362ac11.
Corrected helper SHA-256:
abdbc5ef7064500ea72ecf9b4a3c12e90e28bf1081136e5276331d305bc4d6e4.
This makes nested composition safe for the verified lock lifetime; it does not
prove complete payload/database generation consistency or assembled-image boot.
Those remain explicit whole-image acceptance requirements.
