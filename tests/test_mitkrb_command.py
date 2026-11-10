"""Guard actual historical input/work/recipe identity before native promotion."""
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('qualify_mitkrb', ROOT / 'scripts/build/phase2/qualify_mitkrb.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class MitkrbCommandTests(unittest.TestCase):
    def setUp(self):
        self.command = json.loads((ROOT / 'tests/fixtures/mitkrb-original-command.json').read_text())['command']

    def test_actual_original_vector_is_accepted(self):
        module.validate_original_command(self.command)

    def test_another_input_or_worker_is_refused(self):
        for index in (2, 3):
            changed = list(self.command)
            changed[index] += '-other'
            with self.assertRaises(AssertionError):
                module.validate_original_command(changed)

    def test_different_recipe_is_refused(self):
        changed = list(self.command)
        changed[-1] = '/src/toddy-build-scratch.sh'
        with self.assertRaises(AssertionError):
            module.validate_original_command(changed)
