"""Background execution must preserve normal signal semantics in build tests."""
import importlib.util
from pathlib import Path
import signal
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('runner', ROOT / 'scripts/build/run_step.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class RecipeSignals(unittest.TestCase):
    def test_ignored_launcher_interrupt_does_not_leak_into_recipe(self):
        with tempfile.TemporaryDirectory() as directory:
            recipe = Path(directory) / 'interrupt.sh'
            recipe.write_text('kill -INT $$\nexit 42\n')
            original = signal.signal(signal.SIGINT, signal.SIG_IGN)
            try:
                result = subprocess.run(runner.recipe_command('root') + [str(recipe)],
                                        start_new_session=True)
            finally:
                signal.signal(signal.SIGINT, original)
            self.assertEqual(result.returncode, -signal.SIGINT)
