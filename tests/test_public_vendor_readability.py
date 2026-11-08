import hashlib
from pathlib import Path
import stat
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts/build/phase2'))
from public_vendor_readability import readable_vendor


class PublicVendorReadability(unittest.TestCase):
    def test_only_public_tree_modes_change_and_bytes_are_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);vendor=root/'vendor';vendor.mkdir()
            source=vendor/'public.rs';source.write_bytes(b'pub fn answer()->u8{42}\n');source.chmod(0o640)
            sibling=root/'unrelated-private';sibling.write_bytes(b'private');sibling.chmod(0o600)
            sha=hashlib.sha256(source.read_bytes()).hexdigest()
            result=readable_vendor(vendor)
            self.assertEqual(result,[{'path':'public.rs','before_mode':0o640,'after_mode':0o644,'content_sha256':sha}])
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),sha)
            self.assertEqual(stat.S_IMODE(sibling.stat().st_mode),0o600)
            self.assertEqual(readable_vendor(vendor),[])


if __name__=='__main__':unittest.main()
