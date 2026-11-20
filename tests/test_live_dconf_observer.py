"""Unprivileged filesystem fixtures; no native VM/mount/Dconf acceptance."""
from contextlib import contextmanager
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('live_dconf_observer', ROOT / 'scripts/build/phase2/verify_live_dconf.py')
m = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = m
SPEC.loader.exec_module(m)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def receipts():
    pin = [17, 28, 39]
    live = {'state': 'source-attributed-live-profile-candidate', 'root': m.VIRTUAL,
            'assembly_pin': pin, 'base_image_manifest_sha256': 'a' * 64,
            'source_sha256': 'b' * 64, 'media_id': 'c' * 64,
            'production_ready': False, 'native_boot_verified': False,
            'native_login_verified': False}
    finalized = {'state': 'native-finalizer-verified', 'root': m.VIRTUAL,
                 'assembly_pin': pin, 'image_manifest_sha256': 'a' * 64,
                 'payload_manifest_sha256': 'd' * 64,
                 'checks': {name: {'passed': True, 'exit_status': 0} for name in m.media.p.CHECKS}}
    journal = {'media_id': 'c' * 64, 'payload_manifest_sha256': 'd' * 64}
    return journal, live, finalized, pin


class BindingTests(unittest.TestCase):
    def test_only_same_live_root_source_and_finalizer_may_be_observed(self):
        args = receipts()
        m.receipt_binding(*args, 'b' * 64)
        for field, value in (('root', '/sources/stage/old/root'), ('assembly_pin', [17, 28, 40]),
                             ('source_sha256', 'e' * 64), ('production_ready', True),
                             ('native_boot_verified', True)):
            with self.subTest(field=field):
                changed = list(receipts());changed[1][field] = value
                with self.assertRaisesRegex(ValueError, 'binding differs'):
                    m.receipt_binding(*changed, 'b' * 64)

    def test_missing_or_nonzero_actual_finalizer_is_not_a_query_prerequisite(self):
        for mutation in ('missing', 'failed'):
            args = list(receipts())
            checks = args[2]['checks'];name = next(iter(checks))
            if mutation == 'missing':checks.pop(name)
            else:checks[name]['exit_status'] = 1
            with self.subTest(mutation=mutation), self.assertRaisesRegex(ValueError, 'completed finalizer'):
                m.receipt_binding(*args, 'b' * 64)

    def test_redirected_root_is_refused_before_query_or_mount(self):
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary);actual = work / 'actual';actual.mkdir()
            link = work / 'redirect';link.symlink_to(actual, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, 'redirects'):
                m.root_pin(link, work)

    def test_entry_has_no_user_selected_path_or_command_arguments(self):
        with patch.object(m.sys, 'argv', ['verify_live_dconf.py', '/another/root']):
            with self.assertRaisesRegex(ValueError, 'Fixed root'):
                m.main()


class ObserverFilesystemTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name);self.lower = self.base / 'lower';self.lower.mkdir()
        (self.lower / 'run').mkdir();(self.lower / 'native-input').write_bytes(b'fixed database bytes')
        self.control = self.base / 'control.json';self.control.write_text('{"fixed":"input"}\n')
        self.expected = m.media.snapshot(self.lower, m.media.tree_names(self.lower))
        self.bound = m.Inputs([17, 28, 39], self.expected, {str(self.control): sha(self.control)}, 'a' * 64, 'b' * 64)
        self.mounts_closed = False
        self.patches = [patch.object(m, 'IMAGE', self.lower),
                        patch.object(m, 'root_pin', return_value=self.bound.pin),
                        patch.object(m, 'digest', side_effect=sha)]
        for item in self.patches:item.start();self.addCleanup(item.stop)

    @contextmanager
    def fixture_overlay(self):
        """Model isolated writable view; no kernel mount claim is made."""
        view = self.base / 'view';upper = self.base / 'upper'
        shutil.copytree(self.lower, view);upper.mkdir()
        try:yield view, upper
        finally:self.mounts_closed = True

    def native_read_fixture(self, command, **kwargs):
        # Real Dconf initializes /run/user/0/dconf/user even for a read. The
        # observer must select the disposable view for every native invocation.
        self.assertEqual(command[:2], ['/usr/sbin/chroot', str(self.base / 'view')])
        self.assertNotIn(str(self.lower), command)
        self.assertEqual(command[-3:-1], ['/usr/bin/dconf', 'read'])
        for directory in (self.base / 'view', self.base / 'upper'):
            output = directory / 'run/user/0/dconf/user';output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(b'\0\0')
        expected = dict(m.QUERIES)[command[-1]]
        return subprocess.CompletedProcess(command, 0, expected + '\n', '')

    def test_native_read_side_effects_stay_in_disposable_view_and_are_reported(self):
        with patch.object(m, 'disposable_overlay', self.fixture_overlay), patch.object(m, 'run', self.native_read_fixture):
            result = m.observe(self.bound)
        self.assertTrue(self.mounts_closed)
        self.assertEqual(result['values'], dict(m.QUERIES))
        self.assertIn('run/user/0/dconf/user', result['disposable_upper_paths'])
        self.assertFalse((self.lower / 'run/user').exists())
        self.assertEqual(m.media.snapshot(self.lower, m.media.tree_names(self.lower)), self.expected)
        self.assertTrue(result['lower_full_snapshot_unchanged'])
        self.assertFalse(result['native_boot_verified'])
        self.assertFalse(result['g2_eligible'])

    def test_lower_namespace_or_mtime_drift_is_a_failure_not_a_new_snapshot(self):
        def mutate(command, **kwargs):
            result = self.native_read_fixture(command, **kwargs)
            (self.lower / 'run/forbidden-observer-write').write_bytes(b'changed')
            return result
        with patch.object(m, 'disposable_overlay', self.fixture_overlay), patch.object(m, 'run', mutate):
            with self.assertRaisesRegex(ValueError, 'lower image changed'):
                m.observe(self.bound)
        self.assertTrue(self.mounts_closed)
        self.assertEqual(self.bound.expected, self.expected)

    def test_input_mutation_during_native_query_is_refused(self):
        def mutate(command, **kwargs):
            result = self.native_read_fixture(command, **kwargs)
            self.control.write_text('changed source binding\n')
            return result
        with patch.object(m, 'disposable_overlay', self.fixture_overlay), patch.object(m, 'run', mutate):
            with self.assertRaisesRegex(ValueError, 'inputs changed'):
                m.observe(self.bound)
        self.assertTrue(self.mounts_closed)

    def test_query_failure_still_closes_overlay_and_rechecks_lower(self):
        def fail(command, **kwargs):
            self.native_read_fixture(command, **kwargs)
            raise subprocess.CalledProcessError(1, command)
        with patch.object(m, 'disposable_overlay', self.fixture_overlay), patch.object(m, 'run', fail):
            with self.assertRaises(subprocess.CalledProcessError):m.observe(self.bound)
        self.assertTrue(self.mounts_closed)
        self.assertEqual(m.media.snapshot(self.lower, m.media.tree_names(self.lower)), self.expected)

    def test_wrong_setting_or_unrelated_ibus_output_cannot_pass(self):
        def wrong(command, **kwargs):
            return subprocess.CompletedProcess(command, 0, 'wrong\n', '')
        with patch.object(m, 'disposable_overlay', self.fixture_overlay), patch.object(m, 'run', wrong):
            with self.assertRaisesRegex(ValueError, 'native query differs'):m.observe(self.bound)
        # A distinct ephemeral view is used for the next independent fixture.
        shutil.rmtree(self.base / 'view');shutil.rmtree(self.base / 'upper')
        def ibus(command, **kwargs):
            result = self.native_read_fixture(command, **kwargs)
            path = self.base / 'upper/etc/dconf/db/ibus';path.parent.mkdir(parents=True, exist_ok=True);path.write_bytes(b'bad')
            return result
        with patch.object(m, 'disposable_overlay', self.fixture_overlay), patch.object(m, 'run', ibus):
            with self.assertRaisesRegex(ValueError, 'unexpected disposable output'):m.observe(self.bound)


if __name__ == '__main__':unittest.main()
