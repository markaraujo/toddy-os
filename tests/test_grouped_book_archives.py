import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts/host'))
from phase2_fetch_book_source import grouped_archive_source


class GroupedBookArchives(unittest.TestCase):
    def test_exact_frozen_leaf_only(self):
        text='aa not a checksum\n'+'a'*32+'  libX11-1.8.13.tar.xz\n'+'b'*32+'  other-1.tar.xz\n'
        self.assertEqual(grouped_archive_source('https://www.x.org/pub/individual/lib/',text,'libX11-1.8.13.tar.xz'),
                         ('https://www.x.org/pub/individual/lib/libX11-1.8.13.tar.xz','a'*32))
        with self.assertRaises(AssertionError):grouped_archive_source('https://www.x.org/pub/individual/lib/',text,'unlisted-2.tar.xz')

    def test_duplicate_or_escaping_leaf_rejected(self):
        row='a'*32+'  libX11-1.8.13.tar.xz\n'
        with self.assertRaises(AssertionError):grouped_archive_source('https://www.x.org/pub/individual/lib/',row*2,'libX11-1.8.13.tar.xz')
        with self.assertRaises(AssertionError):grouped_archive_source('https://www.x.org/pub/individual/lib/',row,'../libX11-1.8.13.tar.xz')


if __name__=='__main__':unittest.main()
