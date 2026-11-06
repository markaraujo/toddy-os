import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

MODULE=Path(__file__).resolve().parents[1]/'scripts/build/h08/prepare_config_install.py'
spec=importlib.util.spec_from_file_location('h08_prepare',MODULE)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

class BootstrapConfigurationTests(unittest.TestCase):
    def fixture(self,root):
        (root/'etc').mkdir()
        expected={}
        for name in ('hosts','fstab'):
            data=('known-'+name).encode();(root/'etc'/name).write_bytes(data)
            expected['/etc/'+name]=hashlib.sha256(data).hexdigest()
        return expected

    def test_backup_preserves_every_byte_before_bootstrap_removal(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);expected=self.fixture(root)
            backup=module.preserve_bootstrap(root,expected,set(expected),{})
            self.assertEqual(json.loads((backup/'manifest.json').read_text())['files'],expected)
            for virtual,sha in expected.items():
                self.assertFalse((root/virtual.lstrip('/')).exists())
                self.assertEqual(hashlib.sha256((backup/virtual.lstrip('/')).read_bytes()).hexdigest(),sha)

    def test_changed_second_file_does_not_remove_first(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);expected=self.fixture(root);(root/'etc/fstab').write_text('owner customization')
            with self.assertRaises(ValueError):module.preserve_bootstrap(root,expected,set(expected),{})
            self.assertEqual((root/'etc/hosts').read_text(),'known-hosts')
            self.assertEqual((root/'etc/fstab').read_text(),'owner customization')
            self.assertFalse((root/'sources/recovery').exists())

    def test_owned_configuration_is_not_unlinked(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);expected=self.fixture(root)
            with self.assertRaises(ValueError):module.preserve_bootstrap(root,expected,set(expected),{'/etc/hosts':{'existing-package'}})
            self.assertTrue((root/'etc/hosts').exists())
            self.assertTrue((root/'etc/fstab').exists())

    def test_parent_link_cannot_redirect_removal_outside_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp);outside=base/'outside';outside.mkdir();expected=self.fixture(outside)
            root=base/'target';root.mkdir();(root/'etc').symlink_to(outside/'etc',target_is_directory=True)
            with self.assertRaises(ValueError):module.preserve_bootstrap(root,expected,set(expected),{})
            self.assertTrue((outside/'etc/hosts').exists())
            self.assertTrue((outside/'etc/fstab').exists())
