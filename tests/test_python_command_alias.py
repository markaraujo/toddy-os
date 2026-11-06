import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest

BUILD=Path(__file__).resolve().parents[1]/'scripts/build'
sys.path.insert(0,str(BUILD))
try:
    spec=importlib.util.spec_from_file_location('metadata_alias',BUILD/'upgrade_native_metadata.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
finally:
    sys.path.remove(str(BUILD))


class PythonCommandAlias(unittest.TestCase):
    def test_later_metadata_generation_preserves_canonical_alias(self):
        with tempfile.TemporaryDirectory() as directory:
            stage=Path(directory);binary=stage/'usr/bin';binary.mkdir(parents=True)
            module.ensure_python_command_alias(stage)
            alias=binary/'python';before=alias.lstat()
            # A second metadata generation must retain an existing link even
            # if its target is in a separately assembled runtime stage.
            module.ensure_python_command_alias(stage)
            self.assertEqual(alias.readlink().as_posix(),'python3')
            self.assertEqual(alias.lstat().st_ino,before.st_ino)

    def test_unexpected_payload_is_preserved_and_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            stage=Path(directory);binary=stage/'usr/bin';binary.mkdir(parents=True)
            alias=binary/'python';alias.write_text('preserve owner data')
            with self.assertRaises(SystemExit):module.ensure_python_command_alias(stage)
            self.assertEqual(alias.read_text(),'preserve owner data')
            alias.unlink();alias.symlink_to('/unexpected/interpreter')
            with self.assertRaises(SystemExit):module.ensure_python_command_alias(stage)
            self.assertEqual(alias.readlink().as_posix(),'/unexpected/interpreter')
