from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts/build/phase2'))
from retire_llvm_stages import verify_package_stage,payload


class RetirementSafetyTests(unittest.TestCase):
    def test_unknown_payload_is_preserved_and_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'usr').mkdir();(root/'usr/owned').write_text('owned')
            expected=payload(root);(root/'usr/unrelated').write_text('preserve')
            with self.assertRaises(AssertionError):verify_package_stage(root,expected)
            self.assertEqual((root/'usr/unrelated').read_text(),'preserve')

    def test_changed_bytes_refused_control_metadata_left_intact(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'usr').mkdir();file=root/'usr/owned';file.write_text('owned')
            expected=payload(root);(root/'DEBIAN').mkdir();(root/'DEBIAN/control').write_text('retained')
            verify_package_stage(root,expected)
            file.write_text('changed')
            with self.assertRaises(AssertionError):verify_package_stage(root,expected)
            self.assertEqual((root/'DEBIAN/control').read_text(),'retained')
