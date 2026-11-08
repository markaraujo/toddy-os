from pathlib import Path
import sys
import unittest
import xml.etree.ElementTree as ET

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts/host'))
from phase2_fetch_book_source import reference_scope


class ReferenceScopeTests(unittest.TestCase):
    def test_anchor_selects_own_package_not_first_download(self):
        tree=ET.fromstring('<html xmlns="http://www.w3.org/1999/xhtml"><div class="sect2"><h2><a id="first"/></h2><p>wrong</p></div><div class="sect2"><h2><a id="psutil"/></h2><p>correct</p></div></html>')
        scope=reference_scope(tree,'psutil')
        self.assertEqual(''.join(scope.itertext()),'correct')
        self.assertIs(reference_scope(tree,''),tree)

    def test_missing_anchor_refused(self):
        with self.assertRaises(AssertionError):reference_scope(ET.fromstring('<html/>'),'missing')
