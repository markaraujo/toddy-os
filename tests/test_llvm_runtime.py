from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts/build/phase2'))
from llvm_runtime import split_runtime


class RuntimePartitionTests(unittest.TestCase):
    def prepare(self, root):
        stage=root/'compiler';lib=stage/'usr/lib';lib.mkdir(parents=True)
        (lib/'libLLVM.so.22.1').write_bytes(b'qualified-library-fixture')
        (lib/'libLLVM.so').symlink_to('libLLVM.so.22.1')
        sdk=stage/'usr/bin/clang';sdk.parent.mkdir();sdk.write_bytes(b'compiler-fixture')
        return stage

    def test_runtime_resolves_without_sdk_and_preserves_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);stage=self.prepare(root);runtime=root/'runtime'
            split_runtime(stage,runtime)
            self.assertEqual((runtime/'usr/lib/libLLVM.so').read_bytes(),b'qualified-library-fixture')
            self.assertFalse((runtime/'usr/bin').exists())
            self.assertEqual((stage/'usr/bin/clang').read_bytes(),b'compiler-fixture')
            self.assertFalse((stage/'usr/lib/libLLVM.so').is_symlink())

    def test_escaping_alias_refused_before_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);stage=self.prepare(root);link=stage/'usr/lib/libLLVM.so'
            link.unlink();link.symlink_to('../../../outside')
            with self.assertRaises(AssertionError):split_runtime(stage,root/'runtime')
            self.assertFalse((root/'runtime').exists())
            self.assertEqual((stage/'usr/lib/libLLVM.so.22.1').read_bytes(),b'qualified-library-fixture')

    def test_existing_runtime_refused_without_replacing_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);stage=self.prepare(root);runtime=root/'runtime';runtime.mkdir()
            (runtime/'receipt').write_text('preserved')
            with self.assertRaises(AssertionError):split_runtime(stage,runtime)
            self.assertEqual((runtime/'receipt').read_text(),'preserved')
            self.assertTrue((stage/'usr/lib/libLLVM.so.22.1').is_file())
