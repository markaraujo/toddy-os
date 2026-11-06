"""Inner recipe changes must change durable provenance independently of wrappers."""
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
