"""Native QMP input encodes fixture URLs/uppercase without exposing passwords."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts/host'))
from phase2_gdm_owner_control import text_keys

class NativeInputTextTests(unittest.TestCase):
    def test_url_and_fixture_text(self):
        self.assertEqual(text_keys(':'),['shift','semicolon'])
        self.assertEqual(text_keys('/'),['slash'])
        self.assertEqual(text_keys('T'),['shift','t'])
        self.assertEqual(text_keys(' '),['spc'])
        for c in 'http://127.0.0.1:8765/?phase=1&Toddy+OK':self.assertTrue(text_keys(c))
    def test_control_characters_refused(self):
        for c in ['\n','\r','\x1b','\x00']:
            with self.assertRaises(ValueError):text_keys(c)
