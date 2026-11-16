"""Actual private file/process/crash rollback, no host system configuration writes."""
import hashlib
import json
import multiprocessing
import os
from pathlib import Path
import select
import socket
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'runtime/executor'))
from configuration import ConfigurationManager, ConfigurationError, qualified_bytes, digest, validate_request


def crashed(directory, target, candidate, before, phase):
    def checkpoint(current, _operation):
        if current == phase:
            os._exit(29 if phase == 'after_effect' else 31)
    manager = ConfigurationManager(Path(directory), registry={'managed-preview': Path(target)}, checkpoint=checkpoint)
    manager.apply('crash-operation', 'managed-preview', candidate, before)


class ManagedConfigurationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.directory = Path(self.temp.name)
        self.target = self.directory / 'preview.json'
        self.initial = {'version': 1, 'enabled': True, 'listen_port': 32001}
        self.candidate = {'version': 1, 'enabled': True, 'listen_port': 32002}
        self.target.write_bytes(qualified_bytes(self.initial)); self.target.chmod(0o644)
        self.state = self.directory / 'private'
        self.manager = ConfigurationManager(self.state, registry={'managed-preview': self.target})

    def tearDown(self):
        self.temp.cleanup()

    def hash(self):
        return hashlib.sha256(self.target.read_bytes()).hexdigest()

    def apply(self, operation='apply-one'):
        return self.manager.apply(operation, 'managed-preview', self.candidate, self.hash())

    def test_verified_apply_restore_backup_manual_rescue_and_duplicate_no_replay(self):
        original = self.target.read_bytes(); before = self.hash()
        result = self.apply()
        self.assertTrue(result['verified']); self.assertEqual(result['state'], 'completed')
        self.assertEqual(self.target.read_bytes(), qualified_bytes(self.candidate))
        backup = self.state / 'backups/apply-one.json'
        self.assertEqual(backup.read_bytes(), original)
        self.assertEqual(backup.stat().st_mode & 0o777, 0o600)
        after_info = self.target.stat()
        self.assertEqual(self.manager.apply('apply-one', 'managed-preview', self.candidate, before), result)
        self.assertEqual(self.target.stat().st_ino, after_info.st_ino)
        self.assertFalse(self.manager.inspect('managed-preview')['drift'])
        manifest = self.manager.rescue_manifest('apply-one')
        self.assertEqual(manifest['backup_sha256'], before)
        self.assertEqual(Path(manifest['backup_file']).read_bytes(), original)
        restored = self.manager.restore('restore-one', 'managed-preview', 'apply-one', result['after_sha256'])
        self.assertTrue(restored['verified']); self.assertEqual(self.target.read_bytes(), original)
        self.assertEqual(self.target.stat().st_mode & 0o777, 0o644)
        self.assertFalse(self.manager.inspect('managed-preview')['drift'])
        self.assertEqual(self.manager.restore('restore-one', 'managed-preview', 'apply-one', result['after_sha256']), restored)

    def test_owner_content_or_metadata_drift_is_reported_and_never_fought(self):
        result = self.apply()
        changed = {'version': 1, 'enabled': False, 'listen_port': 32003}
        self.target.write_bytes(qualified_bytes(changed))
        observed = self.target.read_bytes()
        self.assertTrue(self.manager.inspect('managed-preview')['drift'])
        with self.assertRaisesRegex(ConfigurationError, 'configuration_owner_drift'):
            self.manager.restore('restore-drift', 'managed-preview', 'apply-one', result['after_sha256'])
        with self.assertRaisesRegex(ConfigurationError, 'configuration_revision_changed'):
            self.manager.restore('restore-new-hash', 'managed-preview', 'apply-one', self.hash())
        self.assertEqual(self.target.read_bytes(), observed)
        self.target.write_bytes(qualified_bytes(self.candidate)); self.target.chmod(0o640)
        self.assertTrue(self.manager.inspect('managed-preview')['drift'])
        with self.assertRaisesRegex(ConfigurationError, 'configuration_owner_drift'):
            self.manager.restore('restore-mode', 'managed-preview', 'apply-one', result['after_sha256'])
        self.assertEqual(self.target.stat().st_mode & 0o777, 0o640)

    def test_sensitive_untyped_or_unsafe_inputs_are_never_backed_up(self):
        self.target.write_text('DUMMY-SECRET-THIS-IS-NOT-A-QUALIFIED-CONFIG')
        with self.assertRaisesRegex(ConfigurationError, 'unqualified_configuration'):
            self.apply()
        self.assertFalse(list((self.state / 'backups').iterdir()))
        with self.manager._db() as db:
            self.assertNotIn('DUMMY-SECRET', '\n'.join(db.iterdump()))
            self.assertEqual(db.execute('SELECT count(*) FROM configuration_operations').fetchone()[0], 0)
        for bad in ({'version': 1, 'enabled': True, 'listen_port': 32001, 'token': 'dummy'},
                    {'version': True, 'enabled': True, 'listen_port': 32001},
                    {'version': 1, 'enabled': True, 'listen_port': True}):
            with self.assertRaisesRegex(ConfigurationError, 'unqualified_configuration'):
                self.manager.apply('bad', 'managed-preview', bad, None)
        with self.assertRaisesRegex(ConfigurationError, 'invalid_configuration_identifier'):
            self.manager.apply('bad', '../../etc/shadow', self.candidate, None)

    def test_actual_process_loss_after_effect_reconciles_without_writing_again(self):
        before = self.hash()
        process = multiprocessing.Process(target=crashed,
            args=(str(self.state), str(self.target), self.candidate, before, 'after_effect'))
        process.start(); process.join(5)
        if process.is_alive():
            process.terminate(); process.join(5); self.fail('crash probe exceeded bound')
        self.assertEqual(process.exitcode, 29)
        inode = self.target.stat().st_ino
        self.assertEqual(self.target.read_bytes(), qualified_bytes(self.candidate))
        self.assertEqual(self.manager.operation('crash-operation')['state'], 'prepared')
        with self.assertRaisesRegex(ConfigurationError, 'configuration_reconciliation_required'):
            self.manager.apply('crash-operation', 'managed-preview', self.candidate, before)
        self.assertEqual(self.target.stat().st_ino, inode)
        reconciled = self.manager.reconcile('crash-operation')
        self.assertTrue(reconciled['verified']); self.assertEqual(reconciled['state'], 'completed')
        self.assertEqual(self.target.stat().st_ino, inode)
        self.manager.restore('restore-crash', 'managed-preview', 'crash-operation', reconciled['after_sha256'])
        self.assertEqual(self.target.read_bytes(), qualified_bytes(self.initial))

    def test_actual_loss_before_effect_is_known_not_applied_and_not_replayed(self):
        before = self.hash()
        process = multiprocessing.Process(target=crashed,
            args=(str(self.state), str(self.target), self.candidate, before, 'prepared'))
        process.start(); process.join(5)
        if process.is_alive():
            process.terminate(); process.join(5); self.fail('crash probe exceeded bound')
        self.assertEqual(process.exitcode, 31)
        self.assertEqual(self.hash(), before)
        with self.assertRaisesRegex(ConfigurationError, 'configuration_reconciliation_required'):
            self.manager.apply('fresh-but-uncertain', 'managed-preview', self.candidate, before)
        reconciled = self.manager.reconcile('crash-operation')
        self.assertEqual(reconciled['state'], 'not_applied'); self.assertFalse(reconciled['changed'])
        self.assertEqual(self.hash(), before)
        self.assertEqual(self.manager.apply('crash-operation', 'managed-preview', self.candidate, before), reconciled)
        self.assertEqual(self.hash(), before)

    def test_cancel_at_safe_precommit_boundary_retains_config_and_reserved_restore_works(self):
        canceled = False
        def checkpoint(phase, _):
            nonlocal canceled
            if phase == 'prepared':
                canceled = True
        manager = ConfigurationManager(self.state, registry={'managed-preview': self.target}, checkpoint=checkpoint)
        before = self.target.read_bytes()
        result = manager.apply('canceled', 'managed-preview', self.candidate, self.hash(), canceled=lambda: canceled)
        self.assertEqual(result['state'], 'canceled'); self.assertFalse(result['changed'])
        self.assertEqual(self.target.read_bytes(), before)
        limited = ConfigurationManager(self.directory / 'limited', registry={'managed-preview': self.target}, max_operations=1)
        applied = limited.apply('only-apply', 'managed-preview', self.candidate, self.hash())
        with self.assertRaisesRegex(ConfigurationError, 'configuration_store_full'):
            limited.apply('no-room', 'managed-preview', self.initial, self.hash())
        limited.restore('reserved-restore', 'managed-preview', 'only-apply', applied['after_sha256'])
        self.assertEqual(self.target.read_bytes(), before)

    def test_absent_preimage_restores_absence_and_corrupt_backup_refuses_mutation(self):
        self.target.unlink()
        added = self.manager.apply('new-file', 'managed-preview', self.candidate, None)
        self.assertFalse((self.state / 'backups/new-file.json').exists())
        self.manager.restore('remove-new', 'managed-preview', 'new-file', added['after_sha256'])
        self.assertFalse(self.target.exists())
        self.assertFalse(self.manager.inspect('managed-preview')['drift'])
        self.target.write_bytes(qualified_bytes(self.initial)); self.target.chmod(0o644)
        applied = self.manager.apply('corrupt-source', 'managed-preview', self.candidate, self.hash())
        backup = self.state / 'backups/corrupt-source.json'
        backup.write_bytes(qualified_bytes({'version': 1, 'enabled': False, 'listen_port': 32004}))
        current = self.target.read_bytes()
        with self.assertRaisesRegex(ConfigurationError, 'configuration_backup_corrupt'):
            self.manager.restore('bad-restore', 'managed-preview', 'corrupt-source', applied['after_sha256'])
        self.assertEqual(self.target.read_bytes(), current)
        backup.unlink(); os.mkfifo(backup, 0o600)
        with self.assertRaisesRegex(ConfigurationError, 'unsafe_configuration_store_file'):
            self.manager.restore('fifo-restore', 'managed-preview', 'corrupt-source', applied['after_sha256'])
        self.assertEqual(self.target.read_bytes(), current)

    def test_links_permissions_and_unknown_operation_identity_refuse_without_write(self):
        link = self.directory / 'alias'
        os.link(self.target, link)
        with self.assertRaisesRegex(ConfigurationError, 'unsafe_configuration_target'):
            self.apply()
        link.unlink()
        first = self.apply()
        with self.assertRaisesRegex(ConfigurationError, 'configuration_operation_conflict'):
            self.manager.apply('apply-one', 'managed-preview', self.initial, first['after_sha256'])
        self.state.chmod(0o755)
        with self.assertRaisesRegex(ConfigurationError, 'unsafe_configuration_store'):
            ConfigurationManager(self.state, registry={'managed-preview': self.target})
        self.state.chmod(0o700)

    def test_public_schema_rejects_paths_state_directories_and_caller_operation_ids(self):
        request = {'config_id': 'managed-preview', 'configuration': self.candidate, 'expected_sha256': None}
        self.assertEqual(validate_request('managed_config_apply', request), request)
        for extra in ('path', 'state_directory', 'operation_id', 'owner_uid'):
            with self.assertRaisesRegex(ConfigurationError, 'invalid_managed_configuration_operation'):
                validate_request('managed_config_apply', {**request, extra: 'not authority'})
        with self.assertRaisesRegex(ConfigurationError, 'configuration_not_registered'):
            validate_request('managed_config_apply', {**request, 'config_id': 'shadow'})

    def test_actual_consumer_configuration_failure_and_restore_to_working_process(self):
        service = self.directory / 'consumer.py'
        service.write_text('''import json,socket,sys
from pathlib import Path
c=json.loads(Path(sys.argv[1]).read_text())
s=socket.socket()
try:
 s.bind(('127.0.0.1',c['listen_port'])); s.listen(1)
except OSError:
 print('consumer_unavailable',file=sys.stderr); sys.exit(2)
print('READY',flush=True)
sys.stdin.buffer.read(1)
s.close()
''')
        reservation = socket.socket(); reservation.bind(('127.0.0.1', 0))
        occupied = reservation.getsockname()[1]
        free = socket.socket(); free.bind(('127.0.0.1', 0)); port = free.getsockname()[1]; free.close()
        self.initial['listen_port'] = port
        self.candidate['listen_port'] = occupied
        self.target.write_bytes(qualified_bytes(self.initial))
        def start(expect_ready):
            process = subprocess.Popen([sys.executable, str(service), str(self.target)], stdin=subprocess.PIPE,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if expect_ready:
                self.assertTrue(select.select([process.stdout], [], [], 5)[0])
                self.assertEqual(process.stdout.readline(), b'READY\n')
                process.stdin.close(); self.assertEqual(process.wait(timeout=5), 0)
                process.stdout.close(); process.stderr.close()
            else:
                stdout, stderr = process.communicate(timeout=5)
                self.assertEqual(process.returncode, 2); self.assertEqual(stderr, b'consumer_unavailable\n')
            return process
        try:
            start(True)
            applied = self.apply()
            start(False)
            self.manager.restore('restore-consumer', 'managed-preview', 'apply-one', applied['after_sha256'])
            start(True)
            self.assertEqual(self.target.read_bytes(), qualified_bytes(self.initial))
        finally:
            reservation.close()


if __name__ == '__main__':
    unittest.main(verbosity=2)
