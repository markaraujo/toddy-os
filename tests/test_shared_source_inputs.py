import importlib.util
from pathlib import Path
import sys,tempfile,unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts/build/phase2'))
import shared_source_inputs as shared

class SharedSourceInputs(unittest.TestCase):
    def test_other_package_or_version_is_not_authorized(self):
        base=Path('/mnt/lfs/sources/phase2/work/doxygen-1')
        for values in [('glib','2.88.3','glib-2.88.3'),('libqmi','HEAD','libqmi-HEAD'),('libqmi','1.38.1','libqmi-1.38.1')]:
            with self.subTest(values=values),self.assertRaises(AssertionError):shared.layout(base,*values)

    def test_source_alias_cannot_escape_or_replace_another_input(self):
        base=Path('/mnt/lfs/sources/phase2/work/doxygen-1')
        for name in ['../libqmi-1.38.0','/etc','libmbim-1.34.0','sub/libqmi-1.38.0']:
            with self.subTest(name=name),self.assertRaises(AssertionError):shared.layout(base,'libqmi','1.38.0',name)
        physical,alias=shared.layout(base,'libqmi','1.38.0','libqmi-1.38.0')
        self.assertEqual(alias.parent,Path('/mnt/lfs/sources/phase2/inputs'))
        self.assertNotEqual(physical.parent,alias.parent)

    def test_fingerprint_checks_contents_modes_and_link_targets(self):
        with tempfile.TemporaryDirectory() as directory:
            base=Path(directory);p=base/'source';p.write_text('one');before=shared.fingerprint(base)
            p.write_text('two');self.assertNotEqual(shared.fingerprint(base),before)
            before=shared.fingerprint(base);p.chmod(0o444);self.assertNotEqual(shared.fingerprint(base),before)
            link=base/'link';link.symlink_to('source');before=shared.fingerprint(base)
            link.unlink();link.symlink_to('/unavailable-target');self.assertNotEqual(shared.fingerprint(base),before)

if __name__=='__main__':unittest.main()
