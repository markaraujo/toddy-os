"""First-install preparation refuses known hazards before staging/transactions."""
import importlib.util
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

PATH = Path(__file__).resolve().parents[1]/'scripts/build/phase2/source_packages_native.py'
spec = importlib.util.spec_from_file_location('source_native_test', PATH)
native = importlib.util.module_from_spec(spec)
spec.loader.exec_module(native)


class SourceNativeTests(unittest.TestCase):
    def test_existing_stage_is_never_replayed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            stage = root/'stage'
            stage.mkdir()
            with patch.object(native, 'paths', return_value=('toddy-assistant', '', stage, root/'receipt')):
                with patch.object(native.subprocess, 'run') as run:
                    with self.assertRaises(AssertionError):
                        native.install('assistant')
                    run.assert_not_called()

    def test_missing_dependency_precedes_source_staging(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fake = types.SimpleNamespace(native=lambda _: (_ for _ in ()).throw(ValueError('missing')))
            with patch.object(native, 'paths', return_value=('toddy-assistant', 'gtk', root/'stage', root/'receipt')):
                with patch.object(native.subprocess, 'run', return_value=types.SimpleNamespace(returncode=1)):
                    with patch.dict(sys.modules, {'dependency_preflight': fake}):
                        with self.assertRaisesRegex(ValueError, 'missing'):
                            native.install('assistant')
            self.assertFalse((root/'stage').exists())

    def test_target_reserve_precedes_source_staging(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.object(native, 'paths', return_value=('toddy-branding', '', root/'stage', root/'receipt')):
                with patch.object(native.subprocess, 'run', return_value=types.SimpleNamespace(returncode=1)):
                    with patch.dict(sys.modules, {'dependency_preflight': types.SimpleNamespace(native=lambda _: None)}):
                        with patch.object(native.os, 'statvfs', return_value=types.SimpleNamespace(f_bavail=1, f_frsize=4096)):
                            with self.assertRaisesRegex(AssertionError, 'reserve'):
                                native.install('branding')
            self.assertFalse((root/'stage').exists())

    def test_branding_manifest_pins_real_project_and_approved_art_inputs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            stage = root/'stage'
            def execute(command, **options):
                return types.SimpleNamespace(returncode=1 if 'dpkg-query' in command else 0)
            with patch.object(native, 'paths', return_value=('toddy-branding', '', stage, root/'receipt')), patch.object(native, 'ROOT', PATH.parents[3]):
                with patch.object(native.subprocess, 'run', side_effect=execute):
                    with patch.dict(sys.modules, {'dependency_preflight': types.SimpleNamespace(native=lambda _: None)}):
                        with patch.object(native.os, 'statvfs', return_value=types.SimpleNamespace(f_bavail=20*1024**3, f_frsize=1)):
                            original = list(sys.path)
                            sys.path.insert(0, str(PATH.parent))
                            try:
                                native.install('branding')
                            finally:
                                sys.path[:] = original
            import json
            manifest = json.loads((stage/'usr/share/doc/toddy-branding/source-manifest.json').read_text())
            self.assertIn('scripts/build/phase2/branding_stage.py', manifest['source_inputs'])
            self.assertIn('assets/brand/assets.json', manifest['source_inputs'])
            self.assertTrue(all(len(row['sha256']) == 64 for row in manifest['source_inputs'].values()))
            self.assertTrue((stage/'usr/share/doc/toddy-branding/copyright').is_file())

    def test_installer_branding_retains_actual_capture_source_and_evidence_pins(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            stage = root/'stage'
            def execute(command, **options):
                return types.SimpleNamespace(returncode=1 if 'dpkg-query' in command else 0)
            with patch.object(native, 'paths', return_value=('calamares-branding-toddy', '', stage, root/'receipt')), patch.object(native, 'ROOT', PATH.parents[3]):
                with patch.object(native.subprocess, 'run', side_effect=execute):
                    with patch.dict(sys.modules, {'dependency_preflight': types.SimpleNamespace(native=lambda _: None)}):
                        with patch.object(native.os, 'statvfs', return_value=types.SimpleNamespace(f_bavail=20*1024**3, f_frsize=1)):
                            original = list(sys.path)
                            sys.path.insert(0, str(PATH.parent))
                            try:
                                native.install('installer-branding')
                            finally:
                                sys.path[:] = original
            import json
            manifest = json.loads((stage/'usr/share/doc/calamares-branding-toddy/source-manifest.json').read_text())
            self.assertIn('docs/evidence/B02-native-owner-desktop.png', manifest['source_inputs'])
            self.assertIn('docs/evidence/B02-native-owner-session.json', manifest['source_inputs'])
            self.assertTrue((stage/'usr/share/calamares/branding/toddy/branding.desc').is_file())


if __name__ == '__main__':
    unittest.main()
