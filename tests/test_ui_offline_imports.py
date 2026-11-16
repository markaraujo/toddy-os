"""Lightweight UI helpers import under installed namespace without an agent tree."""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]


class OfflineImports(unittest.TestCase):
    def test_installed_namespace_does_not_depend_on_broker_model_or_root_executor(self):
        with tempfile.TemporaryDirectory() as directory:
            package=Path(directory)/'toddy'
            package.mkdir()
            (package/'__init__.py').write_text('')
            for name in ['ui','setup','shared','connections']:
                shutil.copytree(ROOT/'runtime'/name,package/name,
                                ignore=shutil.ignore_patterns('__pycache__'))
            code='''
import sys
sys.path.insert(0,sys.argv[1])
from toddy.ui.model import SetupModel
from toddy.ui.task_state import TaskText
from toddy.connections.secret_store import ProtectedStore
from toddy.shared.json import strict_json
assert strict_json(b'{"version":1}') == {'version':1}
assert 'toddy.broker' not in sys.modules
assert 'toddy.engine' not in sys.modules
assert 'toddy.executor' not in sys.modules
assert 'gi.repository.Secret' not in sys.modules
print('OFFLINE_NAMESPACE_IMPORT_PASS')
'''
            result=subprocess.run([sys.executable,'-I','-c',code,directory],
                                  cwd=directory,capture_output=True,text=True,timeout=10)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertEqual(result.stdout.strip(),'OFFLINE_NAMESPACE_IMPORT_PASS')


if __name__=='__main__':unittest.main()
