import importlib.util
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest import mock

spec = importlib.util.spec_from_file_location('source_filter', Path(__file__).resolve().parents[1]/'scripts/build/source_filter.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class SourceFilterTests(unittest.TestCase):
    def autoar_member(self):
        member = tarfile.TarInfo(module.AUTOAR_REFERENCE)
        member.type = tarfile.SYMTYPE
        member.linkname = '/tmp'
        return member

    def test_autoar_reference_is_exact_and_never_followed(self):
        with tempfile.TemporaryDirectory() as directory:
            member = self.autoar_member()
            module.validate_source_members(module.AUTOAR_ARCHIVE, [member])
            safe = module.source_filter(module.AUTOAR_ARCHIVE)(member, directory)
            self.assertTrue(safe.issym())
            self.assertEqual(safe.linkname, '/tmp')
            self.assertEqual(safe.name, module.AUTOAR_REFERENCE)

    def test_autoar_other_archive_path_target_kind_and_size_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            for archive, path, target, kind, size in [
                ('other.tar.xz', module.AUTOAR_REFERENCE, '/tmp', tarfile.SYMTYPE, 0),
                (module.AUTOAR_ARCHIVE, module.AUTOAR_REFERENCE+'-other', '/tmp', tarfile.SYMTYPE, 0),
                (module.AUTOAR_ARCHIVE, module.AUTOAR_REFERENCE, '/etc', tarfile.SYMTYPE, 0),
                (module.AUTOAR_ARCHIVE, module.AUTOAR_REFERENCE, '/tmp', tarfile.LNKTYPE, 0),
                (module.AUTOAR_ARCHIVE, module.AUTOAR_REFERENCE, '/tmp', tarfile.SYMTYPE, 1),
            ]:
                with self.subTest(archive=archive, path=path, target=target, kind=kind, size=size):
                    member = self.autoar_member()
                    member.name, member.linkname, member.type, member.size = path, target, kind, size
                    with self.assertRaises(tarfile.FilterError):
                        module.source_filter(archive)(member, directory)

    def test_autoar_descendant_refused_before_any_source_is_created(self):
        for name in [module.AUTOAR_REFERENCE+'/child',
                     './'+module.AUTOAR_REFERENCE+'/child',
                     '/'+module.AUTOAR_REFERENCE+'/child',
                     module.AUTOAR_REFERENCE.replace('/reference/', '/other/../reference/')+'/child']:
            with tempfile.TemporaryDirectory() as directory:
                descendant = tarfile.TarInfo(name)
                with self.assertRaises(tarfile.FilterError):
                    module.validate_source_members(module.AUTOAR_ARCHIVE, [self.autoar_member(), descendant])
                self.assertEqual(list(Path(directory).iterdir()), [])

    def test_autoar_missing_or_duplicate_reference_refused(self):
        for members in [[], [self.autoar_member(), self.autoar_member()]]:
            with self.assertRaises(tarfile.FilterError):
                module.validate_source_members(module.AUTOAR_ARCHIVE, members)

    def appstream_member(self):
        member = tarfile.TarInfo('./AppStream-1.1.6/tests/samples/compose/usr/share/metainfo/org.example.nonexistent-badlink.metainfo.xml')
        member.type = tarfile.SYMTYPE
        member.linkname = '/nonexistent'
        return member

    def test_exact_appstream_negative_link_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory, mock.patch.object(module.os.path, 'lexists', return_value=False):
            member = module.source_filter('AppStream-1.1.6.tar.xz')(self.appstream_member(), directory)
            self.assertTrue(member.issym())
            self.assertEqual(member.linkname, '/nonexistent')

    def test_appstream_exception_does_not_allow_other_absolute_links(self):
        with tempfile.TemporaryDirectory() as directory:
            for archive, name, target, kind in [
                ('other.tar.xz', self.appstream_member().name, '/nonexistent', tarfile.SYMTYPE),
                ('AppStream-1.1.6.tar.xz', self.appstream_member().name+'-other', '/nonexistent', tarfile.SYMTYPE),
                ('AppStream-1.1.6.tar.xz', self.appstream_member().name, '/etc/passwd', tarfile.SYMTYPE),
                ('AppStream-1.1.6.tar.xz', self.appstream_member().name, '/nonexistent', tarfile.LNKTYPE),
            ]:
                with self.subTest(archive=archive, name=name, target=target, kind=kind):
                    member = self.appstream_member()
                    member.name, member.linkname, member.type = name, target, kind
                    with self.assertRaises(tarfile.FilterError):
                        module.source_filter(archive)(member, directory)

    def test_appstream_negative_referent_must_be_absent(self):
        with tempfile.TemporaryDirectory() as directory, mock.patch.object(module.os.path, 'lexists', return_value=True):
            with self.assertRaises(tarfile.FilterError):
                module.source_filter('AppStream-1.1.6.tar.xz')(self.appstream_member(), directory)

    def test_appstream_alias_cannot_extract_into_an_external_referent(self):
        with tempfile.TemporaryDirectory() as directory:
            link = Path(directory)/'alias'
            link.symlink_to('/nonexistent')
            member = tarfile.TarInfo('alias/child')
            with self.assertRaises(tarfile.OutsideDestinationError):
                module.source_filter('AppStream-1.1.6.tar.xz')(member, directory)

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
