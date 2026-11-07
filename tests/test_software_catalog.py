"""Integrity of public preparation inputs; no package installation/runtime claims."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class SoftwareCatalog(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((ROOT / 'config/phase2/software-catalog.json').read_text())

    def test_candidates_cannot_masquerade_as_qualified_releases(self):
        self.assertEqual(self.data['qualified_releases'], [])
        for row in self.data['candidates']:
            self.assertEqual(row['qualification'], 'pending')
            for key in ('artifact', 'origin_identity', 'license_review', 'permission_review'):
                self.assertIsNone(row[key])
            self.assertEqual(row['evidence'], [])

    def test_stable_ids_locales_and_base_policy(self):
        rows = self.data['candidates']
        by_id = {r['id']: r for r in rows}
        self.assertEqual(len(rows), len(by_id))
        self.assertNotIn('mise', by_id)
        categories = {c['id'] for c in self.data['categories']}
        for row in rows:
            self.assertIn(row['category'], categories)
            self.assertEqual(set(row['description']), {'en', 'pt-BR'})
            self.assertTrue(all(row['description'].values()))
            self.assertTrue(row['project_url'].startswith('https://'))
            self.assertEqual(row['default'], 'required' if row['id'] == 'git' else 'off')
            self.assertIn(row['backend_candidate'], {'native', 'flatpak-user'})
        self.assertEqual(by_id['docker']['backend_candidate'], 'native')
        self.assertEqual(by_id['localsend']['backend_candidate'], 'flatpak-user')

    def test_handoff_reuses_catalog_and_has_no_live_acquisition(self):
        options = json.loads((ROOT / 'config/phase2/install-options.json').read_text())
        self.assertTrue((ROOT / options['software_catalog']).is_file())
        known = {r['id'] for r in self.data['candidates']}
        for option in options['options']:
            if 'catalog_id' in option:
                self.assertIn(option['catalog_id'], known)
                self.assertEqual(option['default'], 'off')
                self.assertEqual(option['acquisition'], 'installed-user-session-after-review')
        self.assertEqual(self.data['policy']['recommendations'], 'on-request-only')
        self.assertEqual(self.data['policy']['flatpak_scope'], 'user')
