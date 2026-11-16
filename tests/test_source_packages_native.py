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


if __name__ == '__main__':
    unittest.main()
