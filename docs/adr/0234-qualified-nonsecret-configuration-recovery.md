# ADR-0234 — Qualified non-secret configuration recovery and owner drift

Status: accepted source policy; native root/consumer integration pending.
Date: 2026-11-16.

## Context

B05/S10 requires desired configuration, recoverable changes and a working manual
rescue path without repeatedly fighting owner edits. Existing unrestricted
config_replace/root_command provide the explicitly required full administration
under independent owner policy; automatically snapshotting their arbitrary inputs
would copy credentials or sensitive prose into backup/audit storage.

## Decision

Add an independently bounded manager for a fixed installed registry of explicitly
qualified **non-secret typed** configurations. Model/client arguments contain only
config ID, typed value, known hash and restore revision. The root service supplies
its authenticated durable operation ID out of band. Paths, schemas, state folders,
UIDs, callbacks and grants are never request fields. Existing unrestricted owner
administration remains available separately and is not automatically backed up.

Initial ID managed-preview maps only to
/etc/toddy/managed/preview-service.json. Its exact schema is version1,enabled boolean
and listen_port integer1024..65535. It is a qualification consumer, disabled unless
explicitly started for validation, and is not an advertised broker/control TCP
listener. No arbitrary string/credential/prose fields or extra properties are
accepted. Unknown/untyped current files are not copied into backups. Root/native
transport and the actual systemd consumer must be qualified before advertising
this representative managed path as installed functionality.

Store private0600 immutable preimage bytes plus owner/group/mode and hashes under
the executor's0700 configuration state. Record preparing, fsync backup/file/folder,
commit prepared, then perform one nofollow/CAS-checked same-directory replacement
and fsync. Only an actual verified postcondition commits completed/desired state.
An absent preimage is explicit and restores absence. Reject hardlinks, unsafe
ownership/modes, ACL/xattrs, symlinks and special files rather than silently dropping
metadata or following a privileged path. There is no automatic service restart.

Rollback requires the exact active revision and its recorded current hash/mode,
then verifies the backup before writing. A manual owner content/metadata change
reports drift and refuses rollback; even providing the new drift hash does not
turn an old rollback into permission to overwrite it. Read-only inspection never
converges or undoes owner changes. A fresh explicitly authorized apply can adopt a
qualified reviewed current file with its correct expected hash.

Preparation/effect crashes do not replay. Read-only reconciliation proves a known
completed effect or known not-applied preimage; other outcomes stay for review.
Cancellation before the atomic commit keeps the original configuration. After
commit, verified effects remain explicit. Each root policy check and serialization
remain outside the model and manager. The manager does not grant administrative
access or make a root-state receipt from an LLM assertion.

Initial normal history is64 operations within1MiB, with four additional restore
records and byte headroom reserved for recovery. Refuse new work visibly instead
of pruning a live/uncertain backup. Manual root rescue retains actual backup/hash/
metadata custody when the managed service, dispatcher or capacity is unavailable.
This is bounded preview recovery, not arbitrary sensitive-config backup or a full
system checkpoint manager.

## Validation and sources

Requirements/semantics: current B05, PHASE-2-INTERFACES and PHASE-2-OPERATIONAL-
PREWORK dated2026-11-07; current executor's nofollow configuration primitives and
no-replay policy are read directly from the checkout. No new external framework,
package, hosted service or target-version change is needed.

Actual source tests use private temporary files and real subprocesses. A harmless
loopback consumer reads the config and binds successfully, a valid typed occupied-
port change makes that actual process fail, and verified rollback makes a fresh
consumer work. Actual process death before/after replacement verifies backup
custody, no replay and read-only reconciliation. Focused drift, unsafe/secret-shaped
input, canceled precommit, absent preimage, corrupt/special backup, operation ID and
capacity/recovery-reserve checks remain separate from native root/guest acceptance.
