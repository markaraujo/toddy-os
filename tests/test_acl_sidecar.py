import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('acl_sidecar', ROOT / 'scripts/build/h10/acl_sidecar.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class AclNames(unittest.TestCase):
    def test_native_control_char_and_literal_backslash_names(self):
        encoded = './payload ação'.encode() + b'\\012carriage\\015slash\\\\012'
        self.assertEqual(module.decode_name(encoded), 'payload ação\ncarriage\rslash\\012')
        self.assertEqual(module.decode_name(b'.'), '.')
        self.assertEqual(module.decode_name(b'./directory/file with spaces'), 'directory/file with spaces')

    def test_non_native_escapes_and_noncanonical_paths_are_rejected(self):
        for name in (b'/etc/shadow', b'../escape', b'./../escape', b'a//b',
                     b'\\057escape', b'bad\\q', b'', b'././file', b'null\0name'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                module.decode_name(name)


if __name__ == '__main__':
    unittest.main()
