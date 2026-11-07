"""Inner recipe changes must change durable provenance independently of wrappers."""
import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('recipe_provenance', Path(__file__).resolve().parents[1] / 'scripts/build/provenance.py')
provenance = importlib.util.module_from_spec(spec)
spec.loader.exec_module(provenance)


class RecipeProvenance(unittest.TestCase):
    def test_changed_inner_script_is_detected_without_wrapper_change(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'wrapper.sh').write_text('bash inner/recipe.sh\n')
            (root / 'inner').mkdir()
            inner = root / 'inner/recipe.sh'
            inner.write_text('exit 0\n')
            first = provenance.recipe_set(root)
            inner.write_text('exit 1\n')
            second = provenance.recipe_set(root)
            self.assertNotEqual(first['sha256'], second['sha256'])
            self.assertEqual(first['files']['wrapper.sh'], second['files']['wrapper.sh'])
            self.assertNotEqual(first['files']['inner/recipe.sh'], second['files']['inner/recipe.sh'])
            (root / 'cache.pyc').write_bytes(b'ignored generated cache')
            self.assertEqual(second, provenance.recipe_set(root))

    def test_external_native_and_tcl_inputs_are_named_and_change_provenance(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'compile.sh').write_text('cc helper.c -o helper\n')
            (root / 'helper.c').write_text('int main(void) { return 0; }\n')
            (root / 'regression.tcl').write_text('exec ./helper\n')
            initial = provenance.recipe_set(root)
            self.assertEqual(set(initial['files']),
                             {'compile.sh', 'helper.c', 'regression.tcl'})
            for name in ('helper.c', 'regression.tcl'):
                before = provenance.recipe_set(root)
                path = root / name
                path.write_bytes(path.read_bytes() + b'\n')
                after = provenance.recipe_set(root)
                self.assertNotEqual(before['sha256'], after['sha256'])
                self.assertEqual(after['files'][name],
                                 hashlib.sha256(path.read_bytes()).hexdigest())
                self.assertEqual(before['files']['compile.sh'],
                                 after['files']['compile.sh'])
