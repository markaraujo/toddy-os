import copy
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('root_inventory', Path(__file__).resolve().parents[1] / 'scripts/build/h10/root_inventory.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class RootInventory(unittest.TestCase):
    def setUp(self):
        self.directory = {'mode': 0o40755, 'uid': 0, 'gid': 0, 'directory': True}
        self.file = {'mode': 0o100644, 'uid': 0, 'gid': 0, 'sha256': 'a' * 64}
        self.record = {'name': 'sample', 'version': '1-1', 'installed': True, 'archive_sha256': 'b' * 64,
                       'payload': {'/usr': self.directory, '/usr/file': self.file, '/run': self.directory}}

    def test_package_inventory_excludes_mounted_runtime_state(self):
        inventory = module.package_inventory([self.record])
        self.assertEqual(inventory['names'], ['.', 'usr', 'usr/file'])
        self.assertIn('run', inventory['fresh_directories'])
        self.assertEqual(inventory['fresh_directories']['tmp']['mode'], 0o41777)
        self.assertFalse(inventory['complete_image_inventory'])

    def test_account_or_runtime_bytes_cannot_be_imported_from_package_payload(self):
        for path in ('/etc/shadow', '/etc/machine-id', '/run/pid', '/root/private', '/sources/archive',
                     '/var/lib/dpkg/status', '/var/log/session', '/var/cache/history'):
            with self.subTest(path=path):
                record = copy.deepcopy(self.record)
                record['payload'][path] = self.file
                with self.assertRaises(ValueError):
                    module.package_inventory([record])

    def test_canonical_dbus_alias_is_retained_without_identity_bytes(self):
        record = copy.deepcopy(self.record)
        record['name'] = 'dbus'
        for path in ('/var', '/var/lib', '/var/lib/dbus'):
            record['payload'][path] = self.directory
        record['payload']['/var/lib/dbus/machine-id'] = {'mode': 0o120777, 'uid': 0, 'gid': 0, 'symlink': '/etc/machine-id'}
        self.assertIn('var/lib/dbus/machine-id', module.package_inventory([record])['names'])
        record['payload']['/var/lib/dbus/machine-id'] = self.file
        with self.assertRaisesRegex(ValueError, 'canonical machine-ID link'):
            module.package_inventory([record])

    def test_ambiguous_ownership_and_unrecorded_parent_are_rejected(self):
        other = copy.deepcopy(self.record)
        other['name'] = 'other'
        with self.assertRaisesRegex(ValueError, 'Conflicting package ownership'):
            module.package_inventory([self.record, other])
        del other['payload']['/usr']
        with self.assertRaisesRegex(ValueError, 'parent has no native provenance'):
            module.package_inventory([other])

    def test_directory_policy_and_noncanonical_paths_are_rejected(self):
        for path, row in [('/run', dict(self.directory, uid=18)), ('/usr/../other', self.file),
                          ('//usr/file', self.file), ('/usr//file', self.file)]:
            record = copy.deepcopy(self.record)
            record['payload'][path] = row
            with self.subTest(path=path), self.assertRaises(ValueError):
                module.package_inventory([record])


if __name__ == '__main__':
    unittest.main()
