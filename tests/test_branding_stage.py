"""Deterministic native asset staging only, never B11 guest visual acceptance."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('branding_stage', ROOT / 'scripts/build/phase2/branding_stage.py')
branding = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(branding)


class BrandingStageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_desktop_exact_approved_bytes_no_concepts_locks_or_fake_launcher(self):
        output = self.root / 'desktop'
        result = branding.stage_desktop(output, ROOT)
        self.assertEqual(result['package'], 'toddy-branding')
        self.assertEqual(result['icon_mode'], 'protected-master-pixmaps-fallback')
        original = (ROOT / 'assets/brand/toddy-os-system-icon.png').read_bytes()
        self.assertEqual((output / 'usr/share/pixmaps/io.github.markaraujo.Toddy.png').read_bytes(), original)
        self.assertFalse(any('preview.png' in name or '/web/' in name or '/applications/' in name or '/locks/' in name for name in result['files']))
        self.assertFalse((output / 'usr/share/glib-2.0/schemas/90-toddy-branding.gschema.override').exists())
        self.assertFalse(result['native_schema_cache_rebuild_required'])
        for relative, digest in result['files'].items():
            self.assertEqual(hashlib.sha256((output / relative.lstrip('/')).read_bytes()).hexdigest(), digest)

    def test_staging_is_deterministic_and_never_overwrites_existing_output(self):
        first = branding.stage_desktop(self.root / 'one', ROOT)
        second = branding.stage_desktop(self.root / 'two', ROOT)
        self.assertEqual(first, second)
        with self.assertRaisesRegex(branding.BrandingError, 'output_exists'):
            branding.stage_desktop(self.root / 'one', ROOT)

    def test_schema_override_requires_explicit_exact_native_schema_receipt(self):
        destination = self.root / 'bad-schema'
        with self.assertRaisesRegex(branding.BrandingError, 'exact_guest_schema'):
            branding.stage_desktop(destination, ROOT, validate_schemas=lambda _: {'verified': False})
        self.assertFalse(destination.exists())
        seen = []
        receipt = {'verified': True, 'schema_sha256': 'a' * 64}
        def validator(data):
            seen.append(data)
            return receipt
        result = branding.stage_desktop(self.root / 'valid-schema', ROOT, validate_schemas=validator)
        self.assertEqual(len(seen), 1)
        self.assertEqual(result['schema_validation'], receipt)
        self.assertTrue(result['native_schema_cache_rebuild_required'])
        self.assertTrue((self.root / 'valid-schema/usr/share/glib-2.0/schemas/90-toddy-branding.gschema.override').is_file())

    def test_static_installer_needs_no_qml_and_never_displays_an_unlabeled_concept(self):
        output = self.root / 'installer'
        result = branding.stage_installer(output, ROOT)
        self.assertTrue(result['live_only'])
        self.assertEqual(result['slideshow'], 'static-actual-B02-capture')
        prefix = output / 'usr/share/calamares/branding/toddy'
        descriptor = (prefix / 'branding.desc').read_text()
        self.assertIn('slideshow: ["desktop.png"]', descriptor)
        self.assertNotIn('slideshow: "show.qml"', descriptor)
        self.assertIn('type: "none"', descriptor)
        self.assertFalse((prefix / 'show.qml').exists())
        scenes = json.loads((prefix / 'scenes.json').read_text())['scenes']
        self.assertEqual([row['kind'] for row in scenes], ['native-guest-capture'] * 2 + ['design-preview'] * 2)
        for row in scenes:
            self.assertEqual(hashlib.sha256((prefix / row['image']).read_bytes()).hexdigest(), row['sha256'])
            self.assertEqual(set(row['notice']), {'en', 'pt_BR'})
            if row['kind'] == 'design-preview':
                self.assertEqual(row['notice']['en'], 'Design preview — not a running build.')

    def test_qualified_qml_carries_visible_provenance_and_static_reduced_motion_default(self):
        output = self.root / 'qml'
        result = branding.stage_installer(output, ROOT, qml_enabled=True)
        self.assertEqual(result['slideshow'], 'qml-source-runtime-qualification-pending')
        prefix = output / 'usr/share/calamares/branding/toddy'
        descriptor = (prefix / 'branding.desc').read_text()
        qml = (prefix / 'show.qml').read_text()
        self.assertIn('slideshowAPI: 2', descriptor)
        self.assertIn('property bool reducedMotion: true', qml)
        self.assertIn('property bool paused: true', qml)
        self.assertIn('root.scene.notice[root.language]', qml)
        self.assertIn('function onActivate()', qml)
        self.assertIn('function onLeave()', qml)
        self.assertNotIn('@SCENES@', qml)
        self.assertNotIn('XMLHttpRequest', qml)
        self.assertNotIn('Qt.openUrlExternally', qml)

    def test_sources_and_output_cannot_follow_symlinks_or_escape(self):
        with self.assertRaisesRegex(branding.BrandingError, 'source_path'):
            branding.source(ROOT, '../LICENSE')
        linked = self.root / 'linked'
        linked.symlink_to(self.root / 'new-target')
        with self.assertRaises(branding.BrandingError):
            branding.stage_desktop(linked, ROOT)

    def test_existing_default_package_renderer_preserves_unrelated_settings(self):
        original = """# Existing canonical B02 package input, not a user file.
[org/gnome/desktop/background]
picture-uri=''
picture-uri-dark=''
picture-options='none'
primary-color='#081b33'

[org/gnome/desktop/interface]
color-scheme='prefer-dark'
[org/gnome/shell]
favorite-apps=['firefox.desktop']
"""
        rendered = branding.render_desktop_defaults(original)
        self.assertIn("picture-options='zoom'", rendered)
        self.assertIn('toddy-os-wallpaper-light-logo.png', rendered)
        self.assertIn('toddy-os-wallpaper-dark-logo.png', rendered)
        self.assertEqual(rendered.split('[org/gnome/desktop/interface]')[1], original.split('[org/gnome/desktop/interface]')[1])
        self.assertIn("primary-color='#081b33'", rendered)
        with self.assertRaisesRegex(branding.BrandingError, 'baseline_changed'):
            branding.render_desktop_defaults(original.replace("picture-uri=''", "picture-uri='file:///owner-choice.png'"))


if __name__ == '__main__':
    unittest.main()
