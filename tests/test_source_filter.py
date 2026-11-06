import importlib.util
from pathlib import Path
import tarfile
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('source_filter', Path(__file__).resolve().parents[1]/'scripts/build/source_filter.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class SourceFilterTests(unittest.TestCase):
    def test_only_frozen_dpkg_fifos(self):
        with tempfile.TemporaryDirectory() as directory:
            for name in module.DPKG_FIFOS:
                member = tarfile.TarInfo(name)
                member.type = tarfile.FIFOTYPE
                self.assertTrue(module.source_filter('dpkg_1.22.22.tar.xz')(member, directory).isfifo())
                with self.assertRaises(tarfile.SpecialFileError):
                    module.source_filter('other.tar.xz')(member, directory)
            member.name = 'dpkg-1.22.22/unexpected'
            with self.assertRaises(tarfile.SpecialFileError):
                module.source_filter('dpkg_1.22.22.tar.xz')(member, directory)
            member.name = next(iter(module.DPKG_FIFOS))
            member.type = tarfile.CHRTYPE
            with self.assertRaises(tarfile.SpecialFileError):
                module.source_filter('dpkg_1.22.22.tar.xz')(member, directory)
    def test_path_escape_rejected(self):
        member = tarfile.TarInfo('../../escape')
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(tarfile.OutsideDestinationError):
                module.source_filter('dpkg_1.22.22.tar.xz')(member, directory)
