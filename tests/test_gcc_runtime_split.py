"""Native runtime ownership must preserve bytes/aliases and reject bad staging."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('runtime_split', Path(__file__).resolve().parents[1] / 'scripts/build/h07/split-gcc-runtime.py')
splitter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(splitter)


class RuntimeSplit(unittest.TestCase):
    def fixture(self, directory):
        stage = Path(directory) / 'gcc'
        libs = stage / 'usr/lib'
        libs.mkdir(parents=True)
        (libs / 'libstdc++.so.6.0.35').write_bytes(b'\x7fELFtest-runtime-data')
        (libs / 'libstdc++.so.6').symlink_to('libstdc++.so.6.0.35')
        (libs / 'libstdc++.so').symlink_to('libstdc++.so.6')
        (libs / 'libgcc_s.so.1').write_bytes(b'\x7fELFunwinder-data')
        notice = stage / 'usr/share/doc/gcc/copyright'
        notice.parent.mkdir(parents=True)
        notice.write_text('test notice')
        return stage, Path(directory) / 'gcc-runtime'

    def test_versioned_runtime_moves_without_changing_bytes_or_development_alias(self):
        with tempfile.TemporaryDirectory() as directory:
            stage, runtime = self.fixture(directory)
            records = splitter.split(stage, runtime)
            self.assertEqual(len(records), 3)
            self.assertTrue((stage / 'usr/lib/libstdc++.so').is_symlink())
            self.assertEqual((runtime / 'usr/lib/libstdc++.so.6').read_bytes(), b'\x7fELFtest-runtime-data')
            self.assertEqual((runtime / 'usr/share/doc/gcc-runtime/copyright').read_text(), 'test notice')

    def test_bad_candidate_or_escaping_alias_rejected_before_any_move(self):
        for kind in ['not-elf', 'escaping']:
            with tempfile.TemporaryDirectory() as directory:
                stage, runtime = self.fixture(directory)
                bad = stage / 'usr/lib/libbad.so.1'
                if kind == 'not-elf':
                    bad.write_text('not an ELF shared runtime')
                else:
                    bad.symlink_to('/outside/staging')
                with self.assertRaises(ValueError):
                    splitter.split(stage, runtime)
                self.assertFalse(runtime.exists())
                self.assertTrue((stage / 'usr/lib/libgcc_s.so.1').exists())
