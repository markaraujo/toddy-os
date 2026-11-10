"""Qualify testfile cwd relocation without claiming an upstream test execution."""
import ast
from pathlib import Path
import shlex
import shutil
import subprocess
import tempfile
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[1]


class CupsTmpfsFixtureTests(unittest.TestCase):
    def exercise(self, fail):
        recipe = (ROOT / 'scripts/build/phase2/cups-build.sh').read_text()
        program = recipe.split("python3 - <<'PYTEST'\n")[1].split('\nPYTEST')[0]
        function = next(n for n in ast.parse(program).body if isinstance(n, ast.FunctionDef) and n.name == 'run_local_unit')
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            makefile = work / 'tree/cups/Makefile'
            makefile.parent.mkdir(parents=True)
            original = 'testfile:\n\techo original linker unchanged\n\t./testfile\n'
            makefile.write_text(original)
            fixture = work / 'original-testfile.txt'
            fixture.write_bytes(b'exact original fixture\n')

            def run(command, **kwargs):
                self.assertEqual(command, ['make', '-C', '/build/tree/cups', 'testfile'])
                text = makefile.read_text()
                self.assertIn('\techo original linker unchanged\n', text)
                shell = text.split('\tcd ', 1)[1].strip()
                args = shlex.split(shell)
                self.assertEqual(args[1:], ['&&', '/build/tree/cups/testfile'])
                temporary = Path(args[0])
                self.assertEqual(temporary.parent, Path('/tmp'))
                self.assertEqual((temporary / 'testfile.txt').read_bytes(), fixture.read_bytes())
                if fail:
                    raise RuntimeError('simulated test execution failure')
                return subprocess.CompletedProcess(command, 0)

            namespace = dict(w=work, Path=lambda p: fixture if str(p) == '/src/cups/testfile.txt' else Path(p),
                             subprocess=SimpleNamespace(run=run, STDOUT=subprocess.STDOUT),
                             tempfile=tempfile, shutil=shutil, shlex=shlex)
            exec(compile(ast.Module(body=[function], type_ignores=[]), '<CUPS-fixture-runner>', 'exec'), namespace)
            if fail:
                with self.assertRaises(RuntimeError):
                    namespace['run_local_unit']('testfile', {}, None)
            else:
                self.assertEqual(namespace['run_local_unit']('testfile', {}, None).returncode, 0)
            self.assertEqual(makefile.read_text(), original)
            self.assertEqual(fixture.read_bytes(), b'exact original fixture\n')

    def test_only_cwd_changes_with_exact_fixture_and_linker(self):
        self.exercise(False)

    def test_original_makefile_restored_after_execution_error(self):
        self.exercise(True)
