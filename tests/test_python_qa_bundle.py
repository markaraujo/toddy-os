import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts/build'))
from python_qa_bundle import validate
from python_qa_handoff import plan


class PythonQABundle(unittest.TestCase):
    def setUp(self):
        entry = {'mode': 0o100644, 'uid': 0, 'gid': 0, 'sha256': 'a' * 64}
        self.qa_path = '/usr/lib/python3.14/test/test_example.py'
        self.runtime_path = '/usr/lib/python3.14/ssl.py'
        directory = {'mode': 0o40755, 'uid': 0, 'gid': 0, 'directory': True}
        self.donor = {'name': 'python', 'version': '3.14.10-1', 'installed': True,
                      'archive_sha256': 'b' * 64, 'sources': [{'filename': 'Python-3.14.10.tar.xz'}],
                      'payload': {self.qa_path: entry, self.runtime_path: entry,
                                  '/usr/lib/python3.14/test': directory}}
        self.core = copy.deepcopy(self.donor)
        self.core.update(version='3.14.10-1+toddy1', installed=False)
        self.core['payload'] = {self.runtime_path: entry}
        self.qa = copy.deepcopy(self.core)
        self.qa.update(name='python-test-support', payload={self.qa_path: entry, '/usr/lib/python3.14/test': directory})
        deps = 'python (= 3.14.10-1+toddy1), bash, coreutils'
        self.qa['prepared_ownership_handoff'] = plan(self.qa['payload'], {self.qa_path: {'python'}}, self.donor,
            name='python-test-support', version=self.core['version'], architecture='amd64', donor_architecture='amd64',
            depends=deps, sources=['Python-3.14.10.tar.xz'], install=False, native=True)
        self.qa['prepared_ownership_handoff']['predecessor_record_sha256'] = 'c' * 64
        self.controls = [{'Package': item['name'], 'Version': item['version'], 'Architecture': 'amd64',
                          'Depends': deps if item is self.qa else 'glibc, openssl'}
                         for item in (self.donor, self.core, self.qa)]

    def check(self):
        return validate(self.donor, self.core, self.qa, donor_record_sha256='c' * 64, controls=self.controls)

    def test_exact_transfer_is_only_a_preflight(self):
        result = self.check()
        self.assertEqual(result['transferred_files'], 1)
        self.assertEqual(result['retained_runtime_files'], 1)
        self.assertFalse(result['installation_authorized'])

    def test_retained_runtime_change_or_loss_is_rejected(self):
        self.core['payload'][self.runtime_path] = dict(self.core['payload'][self.runtime_path], sha256='d' * 64)
        with self.assertRaisesRegex(ValueError, 'exactly its predecessor'):
            self.check()
        del self.core['payload'][self.runtime_path]
        with self.assertRaises(ValueError):
            self.check()

    def test_partial_or_unrelated_qa_is_rejected(self):
        self.qa['payload']['/usr/bin/unrelated'] = self.qa['payload'][self.qa_path]
        with self.assertRaisesRegex(ValueError, 'unrelated payload'):
            self.check()
        del self.qa['payload']['/usr/bin/unrelated']
        del self.qa['payload'][self.qa_path]
        with self.assertRaisesRegex(ValueError, 'complete original'):
            self.check()

    def test_changed_record_source_or_native_control_is_rejected(self):
        pristine = copy.deepcopy((self.qa, self.controls))
        for mutate in (
            lambda: self.qa['prepared_ownership_handoff'].update(predecessor_record_sha256='d' * 64),
            lambda: self.qa['sources'].append({'filename': 'other'}),
            lambda: self.controls[1].update(Depends='glibc'),
            lambda: self.controls[2].update(Architecture='all'),
            lambda: self.controls[2].update(Depends='python'),
        ):
            self.qa, self.controls = copy.deepcopy(pristine)
            mutate()
            with self.assertRaises(ValueError):
                self.check()


if __name__ == '__main__':
    unittest.main()
