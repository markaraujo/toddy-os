"""Static custody guards only: these fixtures never load Qt or connect a display."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from scripts.build.phase2.qt_wayland_inspect import inspect, FILES, PUBLIC, PRIVATE, VERSION


class QtWaylandPreparationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for relative in FILES:
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'\x7fELF\x02\x01' + b'\0' * 12 + b'\x3e\x00')
            path.chmod(0o644)
        self.headers = self.root / 'usr/include/QtGui'
        self.headers.mkdir(parents=True)
        self.public = self.headers / 'qtgui-config.h'
        self.public.write_text(''.join('#define QT_FEATURE_' + feature + ' 1\n' for feature in PUBLIC))
        private = self.headers / VERSION / 'QtGui/private/qtgui-config_p.h'
        private.parent.mkdir(parents=True)
        private.write_text(''.join('#define QT_FEATURE_' + feature + ' 1\n' for feature in PRIVATE))

    def test_complete_static_custody_is_not_native_gui_acceptance(self):
        before = {path.relative_to(self.root).as_posix(): path.read_bytes()
                  for path in self.root.rglob('*') if path.is_file()}
        result = inspect(self.root, stage=True)
        self.assertFalse(result['qtbase_rebuild_required'])
        self.assertEqual(result['native_plugin_load'], 'not-run')
        self.assertEqual(result['root_gui_launch'], 'not-run')
        self.assertEqual(len(result['stage_manifest_sha256']), 64)
        self.assertEqual(before, {path.relative_to(self.root).as_posix(): path.read_bytes()
                  for path in self.root.rglob('*') if path.is_file()})

    def test_missing_plugin_or_disabled_keyboard_requires_rebuild(self):
        (self.root / FILES[-1]).unlink()
        self.public.write_text(self.public.read_text().replace('QT_FEATURE_xkbcommon 1', 'QT_FEATURE_xkbcommon -1'))
        result = inspect(self.root)
        self.assertTrue(result['qtbase_rebuild_required'])
        self.assertIn(FILES[-1], result['missing'])
        self.assertIn('QT_FEATURE_xkbcommon', result['missing'])

    def test_escaping_or_wrong_architecture_artifact_is_denied(self):
        artifact = self.root / FILES[-1]
        artifact.write_text('not an ELF plugin')
        with self.assertRaisesRegex(ValueError, 'x86_64 ELF'):
            inspect(self.root)
        artifact.unlink(); artifact.symlink_to('/bin/true')
        with self.assertRaisesRegex(ValueError, 'escapes'):
            inspect(self.root)

    def test_fixed_recipe_keeps_exact_version_and_raster_only(self):
        root = Path(__file__).resolve().parents[1]
        recipe = root / 'scripts/build/phase2/qtbase-wayland-raster-build.sh'
        subprocess.run(['bash', '-n', str(recipe)], check=True)
        source = recipe.read_text()
        self.assertIn('== 6.11.2', source)
        self.assertIn('-DFEATURE_wayland_client=ON', source)
        self.assertIn('-DFEATURE_xkbcommon=ON', source)
        self.assertIn('-DINPUT_opengl=no', source)
        self.assertIn('DESTDIR=/stage', source)
        self.assertNotIn(' --install\n', source)
        lock = json.loads((root / 'config/phase2/qt-wayland.lock.json').read_text())
        frozen = json.loads((root / 'config/phase2/sources.lock.json').read_text())
        base = next(row for row in frozen['components'] if row['name'] == 'qtbase')
        self.assertEqual(lock['existing_qtbase_sha256'], base['sha256'])
        self.assertEqual(lock['qt_version'], base['version'])
        self.assertFalse(lock['extra_archive']['selected_for_minimal_client'])
