import importlib.util
from pathlib import Path
import tempfile
import unittest

spec=importlib.util.spec_from_file_location('perl_packlists',Path(__file__).resolve().parents[1]/'scripts/build/perl_packlists.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


class PacklistSafety(unittest.TestCase):
    def fixture(self,root):
        payload=root/'usr/lib/module.pm';payload.parent.mkdir(parents=True);payload.write_text('module')
        pack=root/'usr/lib/.packlist';return payload,pack

    def test_staging_prefix_removed_and_retry_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);_,pack=self.fixture(root)
            pack.write_text('/sources/stage/perl-fixture/usr/lib/module.pm\n')
            self.assertEqual(module.normalize_packlists(root,'perl-fixture'),['/usr/lib/.packlist'])
            self.assertEqual(pack.read_text(),'/usr/lib/module.pm\n')
            self.assertEqual(module.normalize_packlists(root,'perl-fixture'),[])

    def test_other_package_prefix_refused_without_write(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);_,pack=self.fixture(root)
            before='/sources/stage/perl-other/usr/lib/module.pm\n';pack.write_text(before)
            with self.assertRaises(ValueError):module.normalize_packlists(root,'perl-fixture')
            self.assertEqual(pack.read_text(),before)

    def test_unowned_or_missing_payload_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);payload,pack=self.fixture(root)
            pack.write_text('/sources/stage/perl-fixture/usr/lib/module.pm\n')
            with self.assertRaises(ValueError):module.normalize_packlists(root,'perl-fixture',allowed=set())
            payload.unlink()
            with self.assertRaises(ValueError):module.normalize_packlists(root,'perl-fixture')

    def test_escape_or_unreviewed_record_format_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);_,pack=self.fixture(root)
            for entry in ['/usr/lib/../../outside','/usr/lib/module.pm type=file']:
                pack.write_text(entry+'\n')
                with self.assertRaises(ValueError):module.normalize_packlists(root,'perl-fixture')

