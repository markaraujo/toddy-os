"""Calamares3.4.3 adapter/FD guards; no device, native finalizer or GUI acceptance."""
import copy
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
from types import SimpleNamespace

from runtime.installer.backend import Journal
from runtime.installer.disk_plan import InstallError, QualificationPolicy, make_plan
from runtime.installer.live_bindings import create
from runtime.installer.calamares.adapter import (CalamaresAdapter, PipeCancellation,
    SealedConfirmation, process_start_ticks, sealed_json, encoded, private_pipe)


def inputs():
    disk = {'path': '/dev/fixture-disk', 'major_minor': '253:16', 'serial': 'TODDY-INSTALL-FIXTURE',
        'size': 16 * 1024**3, 'sector_size': 512, 'model': 'QEMU HARDDISK', 'driver': 'virtio_blk',
        'readonly': False, 'mounted': False, 'blank': True, 'virtual': True}
    options = {'operation_id': 'a' * 32, 'boot_mode': 'uefi', 'username': 'owner',
        'uid': max(1000, os.getuid()), 'gid': max(1000, os.getgid()), 'locale': 'pt_BR.UTF-8',
        'timezone': 'UTC', 'hostname': 'toddy-owner', 'ai_choice': 'later', 'extras': ['vscode', 'docker']}
    payload = {'sha256': 'b' * 64, 'catalog_sha256': 'c' * 64, 'bytes': 2 * 1024**3}
    return disk, options, payload


def memfd(body, *, seal=True):
    descriptor = os.memfd_create('test-calamares-plan', os.MFD_CLOEXEC | os.MFD_ALLOW_SEALING)
    os.fchmod(descriptor, 0o600)
    os.write(descriptor, body if type(body) is bytes else encoded(body))
    if seal:
        fcntl.fcntl(descriptor, fcntl.F_ADD_SEALS,
                    fcntl.F_SEAL_WRITE | fcntl.F_SEAL_GROW | fcntl.F_SEAL_SHRINK | fcntl.F_SEAL_SEAL)
    return descriptor


class CalamaresAdapterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.directory = Path(self.temp.name)
        self.disk, self.options, self.payload = inputs()
        self.plan = make_plan(self.disk, self.options, self.payload)
        parent = self
        class System:
            def __init__(self):
                self.calls = []
            def probe(self, path):
                parent.assertEqual(path, parent.disk['path'])
                return copy.deepcopy(parent.disk)
            def require_root(self):
                pass  # Source fixture only; production LinuxDisk checks root.
            def preflight(self, firmware):
                parent.assertIn(firmware, ('bios', 'uefi'))
            def run(self, *_args, **_kwargs):
                self.calls.append('native-command')
                raise AssertionError('No native write is permitted by this fixture')
        self.system = System()
        self.ready = {'verified': True, 'payload_manifest_sha256': self.payload['sha256'],
            'catalog_sha256': self.payload['catalog_sha256'], 'finalizer_source_sha256': 'd' * 64,
            'native_qualification_report_sha256': 'e' * 64, 'supported_firmware': ['bios', 'uefi']}
        class Payload:
            def verify_payload(self, plan):
                return {'verified': True, 'payload_sha256': plan['payload']['sha256'], 'catalog_sha256': plan['payload']['catalog_sha256']}
            def install_payload(self, *_):
                raise AssertionError('No fixture finalizer/completion accepted')
        self.bindings = SimpleNamespace(readiness=lambda: copy.deepcopy(self.ready), payload=Payload(),
            policy=QualificationPolicy(self.disk['serial']), build_boot=lambda *_: self.fail('boot callback must not execute'),
            save_pending=lambda *_: self.fail('pending handoff must not execute'), payload_identity=lambda: dict(self.payload))
        self.adapter = CalamaresAdapter(self.bindings, system=self.system)
        self.password, writer = os.pipe()
        os.write(writer, b'private-fixture-login-password-12'); os.close(writer)
        self.control, self.stop = os.pipe()
        self.cancellation = PipeCancellation(self.control)
        self.journal = Journal(self.directory / 'journal')

    def tearDown(self):
        for descriptor in (self.password, self.control, self.stop):
            os.close(descriptor)
        self.journal.close()
        self.temp.cleanup()

    def confirmation(self, **changes):
        now = int(time.monotonic() * 1000)
        body = {'version': 1, 'plan_sha256': self.plan['plan_sha256'], 'target_serial': self.disk['serial'],
                'creator_pid': os.getpid(), 'creator_start_ticks': process_start_ticks(os.getpid()),
                'boot_id': Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
                'issued_monotonic_ms': now - 10, 'expires_monotonic_ms': now + 60000}
        body.update(changes)
        descriptor = memfd(body)
        self.addCleanup(os.close, descriptor)
        return SealedConfirmation(descriptor, creator_pid=os.getpid(), executable=None)

    def test_control_eof_requests_safe_stop_and_write_only_password_is_refused(self):
        read_end, write_end = os.pipe()
        try:
            cancellation = PipeCancellation(read_end)
            self.assertFalse(cancellation.is_set())
            os.close(write_end); write_end = -1
            self.assertTrue(cancellation.is_set())
        finally:
            os.close(read_end)
            if write_end >= 0:
                os.close(write_end)
        read_end, write_end = os.pipe()
        try:
            with self.assertRaisesRegex(InstallError, 'installer_private_pipe_required'):
                private_pipe(write_end)
            self.assertEqual(private_pipe(read_end), read_end)
        finally:
            os.close(read_end); os.close(write_end)

    def test_fixed_native_source_contract_has_safe_stop_and_no_writer_kill(self):
        # Source guard only. This does not assert compilation or graphical behavior.
        root = Path(__file__).resolve().parents[1] / 'runtime/installer/calamares'
        settings = (root / 'settings.conf.in').read_text()
        source = (root / 'ToddyViewStep.cpp').read_text()
        writer = source.split('class ToddyInstallJob final', 1)[1].split('ToddyViewStep::ToddyViewStep(', 1)[0]
        self.assertIn('disable-cancel-during-exec: true', settings)
        self.assertIn('class SafeStopDialog final', source)
        self.assertIn('m_state->showStop(true)', writer)
        self.assertIn('child.state() != QProcess::NotRunning', writer)
        for forbidden in ('child.kill(', 'child.terminate(', 'startDetached(', '/bin/sh', '/bin/bash'):
            self.assertNotIn(forbidden, writer)
        self.assertIn('/usr/lib/toddy/installer/calamares/cli.py', source)
        catalog = json.loads((root / 'strings.json').read_text())
        self.assertEqual(set(catalog), {'en', 'pt-BR'})
        self.assertEqual(set(catalog['en']), set(catalog['pt-BR']))

    def test_actual_root_cli_unavailable_factory_never_creates_journal(self):
        from runtime.installer.calamares import cli
        import io
        stream = io.TextIOWrapper(io.BytesIO(), encoding='utf-8')
        with patch.object(cli.os, 'getuid', return_value=0), patch.object(cli.os, 'geteuid', return_value=0), \
                patch.object(cli.os, 'umask'), patch.object(cli.resource, 'setrlimit'), \
                patch.object(cli, 'Journal', side_effect=AssertionError('No journal before qualification')), \
                patch.object(cli.sys, 'stdout', stream):
            self.assertEqual(cli.main(['capabilities']), 2)
            stream.flush()
            response = json.loads(stream.buffer.getvalue())
        self.assertEqual(response['state'], 'unavailable')
        self.assertEqual(response['code'], 'installer_composed_closure_unavailable')

    def test_exact_actual_backend_review_for_bios_uefi_never_dispatches(self):
        for firmware in ('bios', 'uefi'):
            options = dict(self.options, boot_mode=firmware)
            response = self.adapter.review(self.disk['path'], options)
            self.assertEqual(response['state'], 'review_required'); self.assertFalse(response['disk_writes'])
            plan = json.loads(response['plan_json'])
            self.assertEqual(plan, make_plan(self.disk, options, self.payload))
            self.assertNotIn('password', response['plan_json'])
        self.assertEqual(self.system.calls, [])

    def test_default_factory_and_callable_only_readiness_cannot_authorize_disk_write(self):
        with self.assertRaisesRegex(InstallError, 'installer_composed_closure_unavailable'):
            create()
        self.ready = {'verified': True}
        with self.assertRaisesRegex(InstallError, 'installer_native_closure_not_qualified'):
            self.adapter.execute(self.plan, self.journal, confirmation=self.confirmation(),
                credential_fd=self.password, cancel=self.cancellation)
        self.assertEqual(self.system.calls, [])
        self.assertIsNone(self.journal.snapshot(self.options['operation_id']))
        # Merely adding a marker/report field to the disk plan cannot qualify it.
        altered = dict(self.plan, finalizer_qualified=True)
        with self.assertRaisesRegex(InstallError, 'installer_plan_schema'):
            self.adapter.execute(altered, self.journal, confirmation=self.confirmation(),
                credential_fd=self.password, cancel=self.cancellation)

    def test_sealed_parent_boot_identity_and_expiry_bind_exact_human_confirmation(self):
        self.assertTrue(self.confirmation()(self.plan))
        self.assertFalse(self.confirmation(expires_monotonic_ms=int(time.monotonic() * 1000) - 1,
                                         issued_monotonic_ms=int(time.monotonic() * 1000) - 1000)(self.plan))
        self.assertFalse(self.confirmation(creator_start_ticks=1)(self.plan))
        self.assertFalse(self.confirmation(boot_id='0' * 8 + '-0000-0000-0000-' + '0' * 12)(self.plan))
        self.assertFalse(self.confirmation(target_serial='TODDY-INSTALL-CHANGED')(self.plan))
        changed = copy.deepcopy(self.plan); changed['plan_sha256'] = '0' * 64
        self.assertFalse(self.confirmation()(changed))

    def test_unsealed_regular_file_and_duplicate_json_descriptor_are_refused(self):
        descriptor = memfd(self.plan, seal=False); self.addCleanup(os.close, descriptor)
        with self.assertRaisesRegex(InstallError, 'installer_sealed_descriptor_required'):
            sealed_json(descriptor)
        duplicate = memfd(b'{"version":1,"version":1}'); self.addCleanup(os.close, duplicate)
        with self.assertRaisesRegex(InstallError, 'installer_calamares_duplicate_json'):
            sealed_json(duplicate)
        file = self.directory / 'not-a-private-memfd.json'; file.write_bytes(encoded(self.plan)); file.chmod(0o600)
        descriptor = os.open(file, os.O_RDONLY); self.addCleanup(os.close, descriptor)
        with self.assertRaisesRegex(InstallError, 'installer_sealed_descriptor_required'):
            sealed_json(descriptor)
        self.assertEqual(self.system.calls, [])

    def test_cancel_control_byte_prevents_first_write_and_password_stays_only_in_pipe(self):
        os.write(self.stop, b'x')
        result = self.adapter.execute(self.plan, self.journal, confirmation=self.confirmation(),
            credential_fd=self.password, cancel=self.cancellation)
        self.assertEqual(result['state'], 'canceled-before-write'); self.assertFalse(result['disk_writes'])
        self.assertEqual(self.system.calls, [])
        self.assertEqual(os.read(self.password, 1024), b'private-fixture-login-password-12')
        dump = '\n'.join(self.journal.db.iterdump())
        self.assertNotIn('private-fixture-login-password', dump)
        self.assertNotIn('credential_fd', dump)

    def test_changed_payload_and_firmware_or_confirmation_refuse_before_native_command(self):
        self.ready['payload_manifest_sha256'] = 'f' * 64
        with self.assertRaisesRegex(InstallError, 'installer_live_payload_identity_changed'):
            self.adapter.execute(self.plan, self.journal, confirmation=self.confirmation(),
                credential_fd=self.password, cancel=self.cancellation)
        self.ready['payload_manifest_sha256'] = self.payload['sha256']
        self.ready['supported_firmware'] = ['bios']
        with self.assertRaisesRegex(InstallError, 'installer_firmware_not_qualified'):
            self.adapter.review(self.disk['path'], self.options)
        self.ready['supported_firmware'] = ['bios', 'uefi']
        with self.assertRaisesRegex(InstallError, 'installer_current_destructive_authorization_required'):
            self.adapter.execute(self.plan, self.journal, confirmation=lambda _: False,
                credential_fd=self.password, cancel=self.cancellation)
        self.assertEqual(self.system.calls, [])

    def test_actual_cli_rejects_nonroot_and_never_echoes_unknown_secret_argv(self):
        if os.geteuid() == 0:
            self.skipTest('This source case deliberately checks the ordinary-user entry')
        script = Path(__file__).resolve().parents[1] / 'runtime/installer/calamares/cli.py'
        result = subprocess.run([sys.executable, '-I', str(script), 'execute', '--password=DUMMY-ARG-SECRET'],
                                capture_output=True, timeout=5)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stdout)['code'], 'installer_root_required')
        self.assertNotIn(b'DUMMY-ARG-SECRET', result.stdout + result.stderr)
        self.assertEqual(self.system.calls, [])


if __name__ == '__main__':
    unittest.main(verbosity=2)
