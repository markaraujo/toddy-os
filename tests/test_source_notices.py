import importlib.util
import io
from pathlib import Path
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts/build'))
import source_notices

class NoticeTests(unittest.TestCase):
    def test_numeric_gnu_and_nested_spdx_notices(self):
        self.assertTrue(source_notices.is_notice(Path('gcc/COPYING3')))
        self.assertTrue(source_notices.is_notice(Path('glibc/LICENSES/GPL-2.0-or-later.txt')))
        self.assertFalse(source_notices.is_notice(Path('gcc/main.c')))
    def test_archive_traversal_cannot_become_notice_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'sources').mkdir();archive=root/'sources/source.tar'
            with tarfile.open(archive,'w') as stream:
                member=tarfile.TarInfo('../COPYING');member.size=4;stream.addfile(member,io.BytesIO(b'test'))
            import hashlib
            sha=hashlib.sha256(archive.read_bytes()).hexdigest()
            with patch.object(source_notices,'locked_source',return_value={'sha256':sha,'url':'https://example.invalid/source.tar'}):
                with self.assertRaises(ValueError):
                    source_notices.retain_source_notices(root,root,root/'stage','probe',['source.tar'])
            self.assertFalse((root/'COPYING').exists())
