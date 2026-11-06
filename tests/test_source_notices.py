import importlib.util
import io
from pathlib import Path
import sys
import tarfile
import tempfile
import unittest
import zipfile
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts/build'))
import source_notices

class NoticeTests(unittest.TestCase):
    def test_numeric_gnu_and_nested_spdx_notices(self):
        self.assertTrue(source_notices.is_notice(Path('gcc/COPYING3')))
        self.assertTrue(source_notices.is_notice(Path('glibc/COPYINGv2')))
        self.assertTrue(source_notices.is_notice(Path('glibc/LICENSES')))
        self.assertTrue(source_notices.is_notice(Path('perl/Artistic')))
        self.assertTrue(source_notices.is_notice(Path('libxcrypt/LICENSING')))
        self.assertTrue(source_notices.is_notice(Path('util-linux/README.licensing')))
        self.assertTrue(source_notices.is_notice(Path('libksba/AUTHOR')))
        self.assertTrue(source_notices.is_notice(Path('glibc/LICENSES/GPL-2.0-or-later.txt')))
        self.assertFalse(source_notices.is_notice(Path('gcc/main.c')))
    def test_archive_traversal_cannot_become_notice_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'sources').mkdir();(root/'config').mkdir();(root/'config/component-licenses.json').write_text('{"components": []}');archive=root/'sources/source.tar'
            with tarfile.open(archive,'w') as stream:
                member=tarfile.TarInfo('../COPYING');member.size=4;stream.addfile(member,io.BytesIO(b'test'))
            import hashlib
            sha=hashlib.sha256(archive.read_bytes()).hexdigest()
            with patch.object(source_notices,'locked_source',return_value={'sha256':sha,'url':'https://example.invalid/source.tar'}):
                with self.assertRaises(ValueError):
                    source_notices.retain_source_notices(root,root,root/'stage','probe',['source.tar'])
            self.assertFalse((root/'COPYING').exists())

    def test_embedded_wheel_terms_retained(self):
        stream=io.BytesIO()
        with zipfile.ZipFile(stream,'w') as archive:
            archive.writestr('pip/_vendor/dependency/LICENSE.txt','Original dependency terms')
            archive.writestr('pip/_vendor/packaging/licenses/__init__.py','code, not legal text')
        rows=source_notices.embedded_zip_notices(stream.getvalue(),'Python/pip.whl')
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0][0]['path'],'Python/pip.whl!pip/_vendor/dependency/LICENSE.txt')
        self.assertEqual(rows[0][1],b'Original dependency terms')
    def test_embedded_wheel_escape_rejected(self):
        stream=io.BytesIO()
        with zipfile.ZipFile(stream,'w') as archive:archive.writestr('../LICENSE','terms')
        with self.assertRaises(ValueError):source_notices.embedded_zip_notices(stream.getvalue(),'pip.whl')

    def test_original_vendor_comment_retained_without_code(self):
        data=b'/* Description */\n/* Copyright Example. Permission is granted. */\nint executable_code;'
        notice=source_notices.leading_c_notice(data)
        self.assertIn(b'Copyright Example',notice)
        self.assertNotIn(b'executable_code',notice)
