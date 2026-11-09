import io,importlib.util
from pathlib import Path
import stat,tempfile,unittest,zipfile
MODULE=Path(__file__).resolve().parents[1]/'scripts/build/phase2/unicode_source.py'
spec=importlib.util.spec_from_file_location('unicode_source',MODULE);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
class UnicodeSource(unittest.TestCase):
    def archive(self,extra=None):
        stream=io.BytesIO()
        with zipfile.ZipFile(stream,'w') as z:
            for name,data in [('ReadMe.txt','Version 17.0.0'),('UnicodeData.txt','data'),('NamesList.txt','names'),('Blocks.txt','blocks')]:z.writestr(name,data)
            if extra:extra(z)
        stream.seek(0);return stream
    def test_valid_data_and_manifest(self):
        with tempfile.TemporaryDirectory() as temporary:
            target=Path(temporary)/'input';result=module.extract_ucd(self.archive(),target)
            self.assertEqual(len(result),4);self.assertEqual((target/'ucd/Blocks.txt').read_text(),'blocks')
            with self.assertRaises(AssertionError):module.extract_ucd(self.archive(),target)
    def test_escape_is_rejected_before_any_input_write(self):
        with tempfile.TemporaryDirectory() as temporary:
            target=Path(temporary)/'input'
            with self.assertRaises(ValueError):module.extract_ucd(self.archive(lambda z:z.writestr('../escape','bad')),target)
            self.assertFalse(target.exists());self.assertFalse((Path(temporary)/'escape').exists())
    def test_symlink_is_rejected_before_any_input_write(self):
        def add(z):
            info=zipfile.ZipInfo('link');info.create_system=3;info.external_attr=(stat.S_IFLNK|0o777)<<16;z.writestr(info,'../outside')
        with tempfile.TemporaryDirectory() as temporary:
            target=Path(temporary)/'input'
            with self.assertRaises(ValueError):module.extract_ucd(self.archive(add),target)
            self.assertFalse(target.exists())
