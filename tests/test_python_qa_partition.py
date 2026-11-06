import importlib.util
from pathlib import Path
import tempfile
import unittest

spec=importlib.util.spec_from_file_location('python_qa',Path(__file__).resolve().parents[1]/'scripts/build/h11/python_qa.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


class PythonQAPartition(unittest.TestCase):
    def fixture(self,root):
        runtime=root/'runtime';runtime.mkdir()
        tests=runtime/'usr/lib/python3.14/test/certdata';tests.mkdir(parents=True)
        (tests/'fixture.txt').write_text('Harmless QA fixture')
        (runtime/'usr/lib/python3.14/ssl.py').write_text('Runtime SSL sentinel')
        return runtime,root/'qa'

    def test_qa_moves_without_runtime_or_test_byte_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime,qa=self.fixture(Path(directory))
            before=(runtime/'usr/lib/python3.14/ssl.py').read_bytes()
            result=module.partition(runtime,qa)
            self.assertEqual((runtime/'usr/lib/python3.14/ssl.py').read_bytes(),before)
            self.assertFalse((runtime/'usr/lib/python3.14/test').exists())
            self.assertEqual((qa/'usr/lib/python3.14/test/certdata/fixture.txt').read_text(),'Harmless QA fixture')
            self.assertEqual(result['regular_files'],1)
            self.assertFalse(result['native_package_transfer_validated'])

    def test_existing_qa_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime,qa=self.fixture(Path(directory));qa.mkdir();(qa/'keep').write_text('keep')
            with self.assertRaises(ValueError):module.partition(runtime,qa)
            self.assertEqual((qa/'keep').read_text(),'keep')
            self.assertTrue((runtime/'usr/lib/python3.14/test').is_dir())

    def test_nested_destination_is_rejected_before_move(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime,_=self.fixture(Path(directory))
            with self.assertRaises(ValueError):module.partition(runtime,runtime/'nested')
            self.assertTrue((runtime/'usr/lib/python3.14/test').is_dir())

    def test_redirected_test_root_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);runtime,qa=self.fixture(root)
            tests=runtime/'usr/lib/python3.14/test';tests.rename(root/'outside');tests.symlink_to(root/'outside',target_is_directory=True)
            with self.assertRaises(ValueError):module.partition(runtime,qa)
            self.assertFalse(qa.exists())
