# B05 managed configuration recovery — source preparation

This is an isolated source slice, not native root-D-Bus/systemd/B05 acceptance.
No host system config or designated guest was changed. The module is
runtime/executor/configuration.py; the exact registry/limits/boundary are in
ADR-0234. Root operations/owned GetOperation reconciliation and packaging remain
the coordinator's integration work.

Actual focused command:
`python3 -m unittest discover -s tests -p test_managed_configuration.py -v`.
Ten checks passed in0.163seconds before the final additional FIFO-backup guard.
They exercise real private SQLite/fsync/file operations, subprocess loss before
and after the effect, no replay, owner byte/mode drift refusal, corrupt preimage
and absence recovery, safe cancellation, bounded capacity with reserved rollback,
and a real harmless consumer bind failure/restoration. The first test pass expected
unknown-registry refusal for a traversal ID; actual stricter identifier rejection
was correct and the expected code was fixed. No acceptance failure was relabeled.

The actual consumer has no admin/control API. It reads a private temporary JSON
config, binds a loopback port, prints READY and waits for its private stdin to close.
The test retains a different port to cause a real bind failure after a typed change.
Verified restore returns the original bytes/mode and a fresh process prints READY.
This does not prove a native installed unit, networking provider or physical host.

The manager's public wrapper schemas are:
managed_config_apply(config_id,configuration,expected_sha256) and
managed_config_restore(config_id,revision_id,expected_sha256). The actual durable
operation ID is a trusted separate parameter, never a model field. Root dispatch
is independently required. The fixed managed-preview registry is qualification-only;
existing root_command/config_replace remain full owner tools and are not blindly
snapshotted. New file/listener activation is not automatic.

Manual rescue remains possible without running the conversation/model/broker.
Inside the designated Toddy target/rescue environment, an authenticated root owner
can inspect ConfigurationManager.rescue_manifest(revision_id) from the installed
module. It verifies and returns the known target, private backup filename, actual
SHA-256, original owner/group/mode and explicit absent-preimage flag. First inspect
current config/drift and stop the recorded qualification consumer. Verify the
backup hash and metadata before deliberately restoring the known target (or
removing only that owned target for an absent preimage). Restart/check the recorded
consumer. Do not blindly copy over unrelated owner edits. The source test verifies
the actual manual manifest backup bytes/hash; native unit/rescue commands remain
pending until the coordinator records the actual unit and package identities.

Known limits: only the strict non-secret registry is supported, unknown existing
prose is refused, ACL/xattrs/special files are not transformed, old completed
backup retirement is not automated, and healthy service/package transactions are
not killed to meet this manager's test timer. Required unknown-operation records
are not pruned. No automatic runtime root-policy grant, retry, service restart or
owner-drift convergence is implemented.

Final repository `make check` passed529checks in10.234seconds, including all ten
managed-configuration checks with the actual nonblocking FIFO-backup refusal.
