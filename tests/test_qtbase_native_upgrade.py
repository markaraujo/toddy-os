"""Qt upgrade ownership/dependency/capacity guards; no Qt or guest execution."""
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

BUILD = Path(__file__).resolve().parents[1]/'scripts/build'
sys.path.insert(0, str(BUILD))
sys.path.insert(0, str(BUILD/'phase2'))
import qtbase_wayland_native as qt


class QtBaseNativeUpgradeTests(unittest.TestCase):
    def test_existing_qtbase_name_is_upgraded_without_upstream_version_change(self):
        self.assertEqual(qt.VERSION, '6.11.2-1+toddy2')
        self.assertEqual(qt.OLD_VERSION, '6.11.2-1+toddy1')
        self.assertEqual(qt.ARCHIVE, 'qtbase-everywhere-src-6.11.2.tar.xz')
        self.assertIn('wayland (= 1.26.0-1+toddy1)', qt.DEPENDS)
        self.assertIn('libxkbcommon (= 1.13.2-1+toddy1)', qt.DEPENDS)
        self.assertEqual(qt.BASE, Path('/mnt/toddy-qt-raster-1'))
        self.assertLessEqual(len('TODDY-QT-RASTER-1'), 20)

    def test_attempt_two_uses_system_freetype_and_preserves_failed_one_namespace(self):
        recipe=(BUILD/'phase2/qtbase-wayland-raster-build.sh').read_text()
        self.assertIn('-DINPUT_freetype=system',recipe)
        self.assertNotIn('-DINPUT_freetype=qt',recipe)
        self.assertIn('-DFEATURE_fontconfig=ON',recipe)
        self.assertIn('freetype (= 2.14.3-1+toddy1)',qt.DEPENDS)
        self.assertEqual(qt.SOURCE.name,'qtbase-wayland-6.11.2-2')
        self.assertEqual(qt.WORK.name,'qtbase-wayland-2')
        self.assertEqual(qt.STAGE.name,'phase2-qtbase-wayland-2')
        self.assertEqual(qt.PREPARED.name,'qtbase-wayland-prepared-2.json')
        self.assertEqual(qt.HOLDER,qt.BASE/'source-2')
        self.assertEqual(qt.SCRATCH_WORK,qt.BASE/'work-2')
        self.assertEqual(qt.PROMOTION,qt.BASE/'promotion-2')
        wrapper=(BUILD/'phase2/qtbase_wayland_native.py').read_text()
        self.assertNotIn('qtbase-wayland-1.exit',wrapper)
        self.assertNotIn('qtbase-wayland-install-1.json',wrapper)
        self.assertNotIn("BASE/'source'",wrapper)

    def test_native_install_requires_matching_owned_dispatcher_receipt(self):
        with tempfile.TemporaryDirectory() as temporary:
            log = Path(temporary)/'phase2'; (log.parent/'build').mkdir()
            marker = log.parent/'build/b12-qtbase-wayland-install-2.running.json'
            record = {'step':'b12-qtbase-wayland-install-2','user':'root',
                'recipe_sha256':'a'*64,'postcheck_sha256':'a'*64,'recipe_pid':os.getppid()}
            marker.write_text(json.dumps(record))
            with patch.object(qt, 'LOG', log), patch.object(qt, 'digest', return_value='a'*64):
                qt.transaction('install')
                record['recipe_pid'] = -1; marker.write_text(json.dumps(record))
                with self.assertRaises(AssertionError):
                    qt.transaction('install')
                record['recipe_exit'] = 0; marker.write_text(json.dumps(record))
                qt.transaction('postcheck')
                record['recipe_sha256'] = 'b'*64; marker.write_text(json.dumps(record))
                with self.assertRaises(AssertionError):
                    qt.transaction('postcheck')

    def test_direct_elf_provider_must_have_single_declared_native_owner(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); target = root/'target'; stage = root/'stage'
            info = target/'var/lib/dpkg/info'; info.mkdir(parents=True)
            library = target/'usr/lib/libc.so.6'; library.parent.mkdir(parents=True); library.write_bytes(b'fixture provider')
            (info/'glibc.list').write_text('/usr/lib/libc.so.6\n')
            for index in range(21):
                path = stage/'usr/lib'/('fixture-%d.so' % index); path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(b'\x7fELF')
            dynamic = ' 0x01 (NEEDED) Shared library: [libc.so.6]\n'
            with patch.object(qt, 'TARGET', target), patch.object(qt.subprocess, 'check_output', return_value=dynamic):
                self.assertEqual(qt.elf_dependencies(stage)['undeclared_direct_providers'], 0)
                (info/'unexpected-package.list').write_text('/usr/lib/libc.so.6\n')
                with self.assertRaisesRegex(AssertionError, 'Undeclared/ambiguous'):
                    qt.elf_dependencies(stage)
                (info/'unexpected-package.list').unlink(); (info/'glibc.list').unlink()
                with self.assertRaisesRegex(AssertionError, 'Undeclared/ambiguous'):
                    qt.elf_dependencies(stage)

    def test_build_search_path_is_refused_before_package_mutation(self):
        with tempfile.TemporaryDirectory() as temporary:
            stage = Path(temporary); (stage/'bad').write_bytes(b'\x7fELF')
            with patch.object(qt.subprocess, 'check_output', return_value=' 0 (RUNPATH) Library runpath: [/build/compile/lib]\n'):
                with self.assertRaisesRegex(AssertionError, 'runtime search path'):
                    qt.elf_dependencies(stage)

    def test_capacity_bound_does_not_assume_compression_or_replaced_file_reclaim(self):
        with tempfile.TemporaryDirectory() as temporary:
            stage = Path(temporary); (stage/'payload').write_bytes(b'a'*4097)
            self.assertEqual(qt.payload_bound(stage), 8192)
            (stage/'directory').mkdir(); self.assertGreaterEqual(qt.payload_bound(stage), 12288)


if __name__ == '__main__':
    unittest.main()
