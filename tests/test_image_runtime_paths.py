"""Runtime inputs distinguish target-root build trees from packaged namesakes."""
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest

BUILD = Path(__file__).resolve().parents[1] / 'scripts/build'
for directory in (BUILD, BUILD / 'h10'):
    sys.path.insert(0, str(directory))
import image_runtime


class RuntimePaths(unittest.TestCase):
    def test_packaged_nested_tools_and_sources_are_owned_inputs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ('usr/share/vim/vim92/tools/ref',
                         'usr/lib/python3.14/test/data/sources/example.py'):
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b'packaged input\n')
                info = path.stat()
                row = dict(mode=info.st_mode, uid=info.st_uid, gid=info.st_gid,
                           sha256=hashlib.sha256(path.read_bytes()).hexdigest())
                self.assertEqual(image_runtime.owned_file(root, '/' + name,
                                 {'/' + name: row}), (path, '/' + name))

    def test_build_roots_and_noncanonical_paths_remain_rejected(self):
        for name in ('/tools', '/tools/bin/sh', '/sources', '/sources/file',
                     '/mnt/lfs', '/mnt/lfs/usr/bin/sh', 'usr/bin/sh',
                     '//usr/bin/sh', '/usr//bin/sh', '/usr/./bin/sh',
                     '/usr/../tools/bin/sh'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                image_runtime.runtime_path(name)

    def test_alias_into_build_tree_is_rejected_before_ownership(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'usr/bin').mkdir(parents=True)
            (root / 'usr/bin/sh').symlink_to('/tools/bin/sh')
            with self.assertRaisesRegex(ValueError, 'build-only'):
                image_runtime.owned_file(root, '/usr/bin/sh', {})
