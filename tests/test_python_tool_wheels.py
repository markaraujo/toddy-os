import sys
from pathlib import Path
import tempfile
import unittest
import zipfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts/build/phase2'))
from python_tools_build import wheel_identity


class PythonToolWheels(unittest.TestCase):
    def wheel(self,path,name='trove-classifiers',version='2026.6.1.19',extra=False):
        with zipfile.ZipFile(path,'w') as wheel:
            wheel.writestr('trove_classifiers.dist-info/METADATA',
                           'Metadata-Version: 2.1\nName: '+name+'\nVersion: '+version+'\n')
            if extra:wheel.writestr('other.dist-info/METADATA','Name: other\nVersion: 1\n')

    def test_normalized_package_name(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'test.whl';self.wheel(path,name='trove_classifiers')
            self.assertEqual(wheel_identity(path,'trove-classifiers','2026.6.1.19')['version'],'2026.6.1.19')

    def test_current_date_version_or_wrong_package_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'test.whl'
            for name,version in [('trove-classifiers','2026.11.8.12'),('other','2026.6.1.19')]:
                self.wheel(path,name,version)
                with self.assertRaises(AssertionError):wheel_identity(path,'trove-classifiers','2026.6.1.19')

    def test_ambiguous_metadata_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'test.whl';self.wheel(path,extra=True)
            with self.assertRaises(AssertionError):wheel_identity(path,'trove-classifiers','2026.6.1.19')


if __name__=='__main__':unittest.main()
