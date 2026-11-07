from pathlib import Path
import sys
import unittest

BUILD = Path(__file__).resolve().parents[1] / 'scripts/build'
for directory in (BUILD, BUILD / 'h11'):
    sys.path.insert(0, str(directory))
from remove_image_qa import removable_document


class QaLegalCopies(unittest.TestCase):
    def test_exact_regular_legal_copies_are_recognized(self):
        row = dict(mode=0o100644, uid=0, gid=0, sha256='a'*64)
        for suffix in ('copyright', 'source-notices/index.json', 'source-notices/'+'a'*64):
            core = {'payload': {'/usr/share/doc/python/'+suffix: row}}
            self.assertTrue(removable_document('/usr/share/doc/python-test-support/'+suffix, row, core))
            changed = dict(row, sha256='b'*64)
            self.assertFalse(removable_document('/usr/share/doc/python-test-support/'+suffix, changed, core))

    def test_unrelated_data_alias_and_unrecorded_legal_files_are_rejected(self):
        row = dict(mode=0o100644, uid=0, gid=0, sha256='a'*64)
        for suffix in ('program.py', 'source-notices/subdir/file', '../runtime-file'):
            core = {'payload': {'/usr/share/doc/python/'+suffix: row}}
            self.assertFalse(removable_document('/usr/share/doc/python-test-support/'+suffix,row,core))
        self.assertFalse(removable_document('/usr/share/doc/python-test-support/source-notices/index.json',row,{'payload':{}}))
        link = {'symlink':'/usr/bin/python3'}
        self.assertFalse(removable_document('/usr/share/doc/python-test-support/copyright',link,
                         {'payload':{'/usr/share/doc/python/copyright':link}}))
