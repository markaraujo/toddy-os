import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('live_accounts', ROOT / 'scripts/build/h10/live_accounts.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class LiveAccounts(unittest.TestCase):
    def setUp(self):
        self.baseline = json.loads((ROOT / 'config/live-account-baseline.json').read_text())

    def test_fresh_identity_preserves_service_ids_and_has_no_credentials(self):
        files, users, groups = module.account_data(self.baseline)
        self.assertEqual((users, groups), (14, 34))
        passwd = {row.split(':')[0]: row.split(':') for row in files['etc/passwd'][0].splitlines()}
        for name, uid in [('root', '0'), ('messagebus', '18'), ('systemd-network', '76'),
                          ('systemd-resolve', '77'), ('systemd-timesync', '78')]:
            self.assertEqual(passwd[name][2:4], [uid, uid])
        self.assertNotIn('tester', passwd)
        for name in ('shadow', 'gshadow'):
            self.assertEqual(files['etc/' + name][1], 0o600)
            self.assertTrue(all(row.split(':')[1] == '!' for row in files['etc/' + name][0].splitlines()))
        for name in ('subuid', 'subgid', 'machine-id'):
            self.assertEqual(files['etc/' + name][0], '')

    def test_builder_account_and_embedded_password_are_rejected(self):
        for addition in ('tester:x:101:101::/home/tester:/bin/bash\n',
                         'service:nonsecret-sentinel:101:101::/:/usr/bin/false\n'):
            data = copy.deepcopy(self.baseline)
            data['passwd'] += addition
            with self.assertRaises(ValueError):
                module.account_data(data)

    def test_duplicate_or_unresolved_numeric_identity_is_rejected(self):
        for field, old, new in [('passwd', 'bin:x:1:1:', 'bin:x:0:1:'),
                                ('group', 'audio:x:11:', 'audio:x:word:'),
                                ('passwd', 'bin:x:1:1:', 'bin:x:1:1234:')]:
            data = copy.deepcopy(self.baseline)
            data[field] = data[field].replace(old, new)
            with self.assertRaises(ValueError):
                module.account_data(data)

    def test_interactive_service_and_unknown_membership_are_rejected(self):
        for field, old, new in [('passwd', ':/dev/null:/usr/bin/false', ':/dev/null:/bin/bash'),
                                ('group', 'bin:x:1:daemon', 'bin:x:1:unknown'),
                                ('group', 'root:x:0:', 'renamed:x:0:')]:
            data = copy.deepcopy(self.baseline)
            data[field] = data[field].replace(old, new)
            with self.assertRaises(ValueError):
                module.account_data(data)


if __name__ == '__main__':
    unittest.main()
