"""Filesystem guards for copying native inputs; no native success is simulated."""
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts/build'))
spec = importlib.util.spec_from_file_location('db_standard_prepare', ROOT / 'scripts/build/db_standard_prepare.py')
prepare = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prepare)


class DatabasePreparation(unittest.TestCase):
    def native_shape(self, source):
        build = source / 'build-test'
        (build / '.libs').mkdir(parents=True)
        for name in ('Makefile', 'config.status', 'db_config.h', 'include.tcl', 'cutest',
                     'db_repsite', '.libs/libdb-5.3.so'):
            (build / name).write_text('filesystem fixture only\n')
        for name in ('config.status', 'cutest', 'db_repsite'):
            (build / name).chmod(0o755)
        (build / 'db_repsite.c').write_bytes((ROOT / 'scripts/build/h07/db_repsite.c').read_bytes())
        (build / '.libs/libdb.so').symlink_to('libdb-5.3.so')
        (source / 'src').mkdir()
        (source / 'src/input.c').write_text('source fixture\n')
        return build

    def test_prior_test_outputs_are_excluded_and_relative_library_links_survive(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            source = base / 'source'
            build = self.native_shape(source)
            (build / 'TESTDIR').mkdir()
            (build / 'TESTDIR/live.db').write_text('must not copy transient state')
            (build / 'ALL.OUT').write_text('must not copy an old outcome')
            (source / 'build-production').mkdir()
            (source / 'build-production/unrelated').write_text('not test input')
            rows = prepare.inventory(source)
            target = base / 'copy'
            prepare.copy_inputs(source, target, rows)
            self.assertFalse((target / 'build-test/TESTDIR').exists())
            self.assertFalse((target / 'build-test/ALL.OUT').exists())
            self.assertFalse((target / 'build-production').exists())
            self.assertTrue((target / 'build-test/.libs/libdb.so').is_symlink())
            self.assertEqual(rows, prepare.inventory(target))

    def test_source_change_between_inventory_and_copy_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            source = base / 'source'
            self.native_shape(source)
            rows = prepare.inventory(source)
            (source / 'src/input.c').write_text('changed after snapshot')
            with self.assertRaisesRegex(ValueError, 'Copied native input changed'):
                prepare.copy_inputs(source, base / 'copy', rows)

    def test_external_and_absolute_input_links_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            source = base / 'source'
            self.native_shape(source)
            (base / 'outside').write_text('outside')
            alias = source / 'src/alias'
            alias.symlink_to('../../outside')
            with self.assertRaisesRegex(ValueError, 'External'):
                prepare.inventory(source)
            alias.unlink()
            alias.symlink_to(source / 'src/input.c')
            with self.assertRaisesRegex(ValueError, 'absolute'):
                prepare.inventory(source)
