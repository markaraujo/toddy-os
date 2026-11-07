import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location(
    'db_isolated_driver', Path(__file__).resolve().parents[1] /
    'scripts/build/h07/berkeley-db-isolated-driver.py')
driver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(driver)


class IsolatedDatabaseInputs(unittest.TestCase):
    def fixture(self, base):
        (base / 'source').mkdir()
        (base / 'source/runtime.c').write_text('unchanged native source\n')
        result = {'source_files': {'runtime.c': {
            'sha256': driver.digest(base / 'source/runtime.c')}}}
        for field, name in [('isolation_script_sha256', 'isolate.sh'),
                            ('isolation_probe_sha256', 'isolation-probe.py'),
                            ('outer_namespace_file_sha256', 'outer-namespaces.json')]:
            (base / name).write_text('original input\n')
            result[field] = driver.digest(base / name)
        return result

    def test_modified_code_or_namespace_inputs_cannot_reuse_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            expected = self.fixture(base)
            driver.verify(base, expected)
            for name in ('source/runtime.c', 'isolate.sh', 'isolation-probe.py',
                         'outer-namespaces.json'):
                path = base / name
                original = path.read_bytes()
                path.write_bytes(original + b'changed\n')
                with self.assertRaises(ValueError):
                    driver.verify(base, expected)
                self.assertEqual(path.read_bytes(), original + b'changed\n')
                path.write_bytes(original)

    def test_identical_bytes_outside_source_are_not_accepted_through_symlink(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            expected = self.fixture(base)
            source = base / 'source/runtime.c'
            outside = base / 'outside.c'
            outside.write_bytes(source.read_bytes())
            source.unlink()
            source.symlink_to('../outside.c')
            with self.assertRaises(ValueError):
                driver.verify(base, expected)
            self.assertEqual(hashlib.sha256(outside.read_bytes()).hexdigest(),
                             expected['source_files']['runtime.c']['sha256'])
