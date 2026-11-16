"""Connection metadata validation is independent of credentials/model activation."""
import copy
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'runtime/broker'))
from configured_engine import ConfiguredEngine
from engine import EngineAdapter, EngineError


@unittest.skipIf(os.geteuid() == 0, 'managed engine deliberately refuses root')
class ConfiguredEngineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.directory = Path(self.temp.name)
        self.profile = json.loads((ROOT / 'config/phase2/profile/config.json').read_text())
        self.profile['provider'] = {'mode': 'remote', 'adapter_id': 'openai', 'model_id': 'owner-choice',
            'connection_ref': 'owner-connection', 'allow_remote_fallback': False}
        self.engine = ConfiguredEngine(ROOT / 'config/phase2', config_directory=self.directory,
                                      runtime_directory=self.directory / 'runtime')
        self.path = self.directory / 'owner-connection.json'
        self.settings = {'version': 1, 'adapter_id': 'openai', 'model_id': 'owner-choice',
                         'base_url': 'https://api.example.invalid/v1', 'context_tokens': 4096, 'max_output_tokens': 1024}

    def tearDown(self):
        self.temp.cleanup()

    def write(self, settings):
        self.path.write_text(json.dumps(settings)); self.path.chmod(0o600)

    def test_owned_private_metadata_contains_references_only_and_exact_binding(self):
        self.write(self.settings)
        self.assertEqual(self.engine.connection_settings(self.profile), self.settings)
        invalid = copy.deepcopy(self.settings); invalid['credential'] = 'must never be accepted in metadata'
        self.write(invalid)
        with self.assertRaisesRegex(EngineError, 'connection_mismatch'):
            self.engine.connection_settings(self.profile)
        invalid = copy.deepcopy(self.settings); invalid['model_id'] = 'other-model'
        self.write(invalid)
        with self.assertRaisesRegex(EngineError, 'connection_mismatch'):
            self.engine.connection_settings(self.profile)

    def test_endpoint_tokens_insecure_transport_permissions_and_links_are_refused(self):
        for endpoint in ('http://api.example.invalid', 'https://user:key@api.example.invalid',
                         'https://api.example.invalid/?token=secret', 'https://api.example.invalid/#token'):
            settings = copy.deepcopy(self.settings); settings['base_url'] = endpoint
            self.write(settings)
            with self.assertRaisesRegex(EngineError, 'invalid_provider_endpoint'):
                self.engine.connection_settings(self.profile)
        self.write(self.settings); self.path.chmod(0o644)
        with self.assertRaisesRegex(EngineError, 'connection_unavailable'):
            self.engine.connection_settings(self.profile)
        self.path.unlink(); target = self.directory / 'other'; target.write_text('{}'); target.chmod(0o600)
        self.path.symlink_to(target)
        with self.assertRaisesRegex(EngineError, 'connection_unavailable'):
            self.engine.connection_settings(self.profile)

    def test_remote_requires_fresh_task_consent_before_any_connection_or_key_lookup(self):
        files = {'config.json': json.dumps(self.profile).encode()}
        with self.assertRaisesRegex(EngineError, 'remote_consent_required'):
            self.engine(files, 'a' * 64, 'task-one', 'No remote consent.', False,
                        lambda *_: self.fail(), lambda *_: self.fail(), lambda: False)
        self.assertFalse(self.path.exists())
        self.assertFalse(self.engine.available(self.profile))

    def test_fresh_local_helper_failure_and_cancel_are_bounded_without_model_or_download(self):
        self.profile['provider'] = {'mode': 'local', 'adapter_id': 'local-llama-cpp',
            'model_id': 'toddy-qwen3-1.7b-q8_0', 'connection_ref': 'owner-connection', 'allow_remote_fallback': False}
        settings = {'version': 1, 'adapter_id': 'local-llama-cpp', 'model_id': 'toddy-qwen3-1.7b-q8_0',
                    'model_path': str(self.directory / 'absent-model.gguf')}
        import time
        started = time.monotonic()
        with self.assertRaisesRegex(EngineError, 'local_readiness_failed'):
            self.engine._local(self.profile, settings, lambda: False)
        with self.assertRaisesRegex(EngineError, 'canceled'):
            self.engine._local(self.profile, settings, lambda: True)
        self.assertLess(time.monotonic() - started, 5)
        self.assertFalse((self.directory / 'absent-model.gguf').exists())
        self.assertFalse(list(self.directory.rglob('key')))

    def test_local_metadata_cannot_silently_choose_remote_or_another_model(self):
        self.profile['provider'] = {'mode': 'local', 'adapter_id': 'local-llama-cpp',
            'model_id': 'toddy-qwen3-1.7b-q8_0', 'connection_ref': 'owner-connection', 'allow_remote_fallback': False}
        self.write({'version': 1, 'adapter_id': 'local-llama-cpp', 'model_id': 'toddy-qwen3-1.7b-q8_0',
                    'model_path': str(self.directory / 'absent.gguf')})
        self.assertEqual(self.engine.connection_settings(self.profile)['model_id'], 'toddy-qwen3-1.7b-q8_0')
        self.assertFalse(self.engine.available(self.profile))
        settings = json.loads(self.path.read_text()); settings['model_id'] = 'other'
        self.write(settings)
        with self.assertRaisesRegex(EngineError, 'connection_mismatch'):
            self.engine.connection_settings(self.profile)


if __name__ == '__main__':
    unittest.main(verbosity=2)
