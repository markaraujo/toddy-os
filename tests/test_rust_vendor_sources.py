import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts/host'))
from phase2_rust_vendor import REGISTRY,registry_packages,verify_vendor


class RustVendorSources(unittest.TestCase):
    def lock(self,source=REGISTRY,name='example',sha='a'*64):
        return ('[[package]]\nname="local"\nversion="1.0.0"\n\n[[package]]\n'
                'name='+json.dumps(name)+'\nversion="1.0.0"\nsource='+json.dumps(source)+
                '\nchecksum='+json.dumps(sha)+'\n').encode()

    def test_only_frozen_registry_checksum_becomes_acquisition_input(self):
        self.assertEqual(registry_packages(self.lock()),[{'name':'example','version':'1.0.0','sha256':'a'*64}])
        for source in ['git+https://example.invalid/private','registry+https://example.invalid/index']:
            with self.assertRaises(ValueError):registry_packages(self.lock(source=source))

    def test_untrusted_lock_cannot_authorize_escaping_paths_or_bad_hash(self):
        for name,sha in [('../escape','a'*64),('example','not-a-checksum')]:
            with self.assertRaises(ValueError):registry_packages(self.lock(name=name,sha=sha))

    def test_cached_vendor_rejects_mutated_extra_or_linked_payload(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);crate=root/'example-1.0.0';crate.mkdir()
            manifest=crate/'Cargo.toml';manifest.write_text('[package]\nname="example"\nversion="1.0.0"\nlicense="MIT"\n')
            source=crate/'lib.rs';source.write_bytes(b'pub fn answer()->u8{42}\n')
            files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [manifest,source]}
            (crate/'.cargo-checksum.json').write_text(json.dumps({'package':'a'*64,'files':files}))
            packages=[{'name':'example','version':'1.0.0','sha256':'a'*64}]
            self.assertEqual(verify_vendor(root,packages)[0]['files'],2)
            source.write_bytes(b'tampered')
            with self.assertRaises(AssertionError):verify_vendor(root,packages)
            source.write_bytes(b'pub fn answer()->u8{42}\n')
            extra=crate/'extra';extra.write_text('unexpected')
            with self.assertRaises(AssertionError):verify_vendor(root,packages)
            extra.unlink();source.unlink();source.symlink_to(manifest)
            with self.assertRaises(AssertionError):verify_vendor(root,packages)


if __name__=='__main__':unittest.main()
