import copy
import importlib.util
from pathlib import Path
import stat
import subprocess
import sys
import unittest

spec = importlib.util.spec_from_file_location('python_qa_handoff', Path(__file__).resolve().parents[1] / 'scripts/build/python_qa_handoff.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class PythonQAHandoff(unittest.TestCase):
    def test_unrelated_h11_package_cannot_shadow_project_layout(self):
        code = ('import sys,types,runpy; p=types.ModuleType("h11"); p.__path__=[]; '
                'sys.modules["h11"]=p; data=runpy.run_path(sys.argv[1]); '
                'assert data["QA_ROOTS"][0]=="/usr/lib/python3.14/test"')
        subprocess.run([sys.executable, '-c', code, str(Path(module.__file__))], check=True)

    def fixture(self):
        directory = {'directory': True, 'mode': stat.S_IFDIR | 0o755, 'uid': 0, 'gid': 0}
        file = {'sha256': '0' * 64, 'mode': stat.S_IFREG | 0o644, 'uid': 0, 'gid': 0}
        root = '/usr/lib/python3.14/test'
        entries = {root: directory.copy(), root + '/fixture.py': file.copy(),
                   '/usr': directory.copy(), '/usr/lib': directory.copy(), '/usr/lib/python3.14': directory.copy()}
        owners = {root + '/fixture.py': {'python'}}
        donor = {'name': 'python', 'version': '3.14.10-1+toddy1', 'installed': True,
                 'archive_sha256': '1' * 64, 'sources': [{'filename': 'Python-3.14.10.tar.xz'}],
                 'payload': {root: directory.copy(), root + '/fixture.py': file.copy()}}
        options = dict(name='python-test-support', version='3.14.10-1+toddy2', architecture='amd64',
                       donor_architecture='amd64', depends='python (= 3.14.10-1+toddy2), bash, coreutils',
                       sources=['Python-3.14.10.tar.xz'], install=False, native=True)
        return entries, owners, donor, options

    def test_only_complete_unchanged_archive_plan_is_allowed(self):
        entries, owners, donor, options = self.fixture()
        before = copy.deepcopy((entries, owners, donor))
        result = module.plan(entries, owners, donor, **options)
        self.assertEqual(result['transferred_path_count'], 1)
        self.assertFalse(result['installation_authorized'])
        self.assertEqual(before, (entries, owners, donor))

    def test_install_bootstrap_and_unrelated_recipient_are_rejected(self):
        for key, value in [('install', True), ('native', False), ('name', 'another-package'),
                           ('architecture', 'all'), ('depends', 'python'),
                           ('depends', 'python (= 3.14.10-1+toddy2)'), ('sources', [])]:
            entries, owners, donor, options = self.fixture()
            options[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                module.plan(entries, owners, donor, **options)

    def test_partial_changed_or_extra_payload_is_rejected(self):
        for change in ('missing', 'bytes', 'mode', 'extra', 'parent'):
            entries, owners, donor, options = self.fixture()
            path = '/usr/lib/python3.14/test/fixture.py'
            if change == 'missing': del entries[path]
            elif change == 'bytes': entries[path]['sha256'] = '2' * 64
            elif change == 'mode': entries[path]['mode'] |= stat.S_ISUID
            elif change == 'extra': entries['/etc/unauthorized'] = entries[path].copy()
            else: entries['/usr']['mode'] = stat.S_IFDIR | 0o700
            with self.subTest(change=change), self.assertRaises(ValueError):
                module.plan(entries, owners, donor, **options)

    def test_missing_wrong_or_duplicate_ownership_is_rejected(self):
        for actual in (set(), {'other'}, {'python', 'other'}, {'python-test-support'}):
            entries, owners, donor, options = self.fixture()
            owners['/usr/lib/python3.14/test/fixture.py'] = actual
            with self.subTest(owners=actual), self.assertRaises(ValueError):
                module.plan(entries, owners, donor, **options)


if __name__ == '__main__':
    unittest.main()
