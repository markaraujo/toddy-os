import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'scripts/build/phase2')]
import package_sources_reviewed as reviewed


class ReviewedSourceAdmissionTests(unittest.TestCase):
    def inputs(self):
        decision = json.loads((ROOT / 'docs/evidence/mvp-source-coordinator-review-1.json').read_bytes())
        artifacts = []
        for asset in decision['assets']:
            role = 'inventory' if asset['name'] == 'source-review-inventory.json' else 'project-source' if asset['name'] == 'toddy-project-source.tar' else 'licenses' if asset['name'].startswith('source-licenses-') else 'source'
            artifacts.append(dict(asset, role=role))
        pins = {'archive_export_sha256': decision['archive_export_sha256'],
            'packages': [reviewed.identity(row) for row in decision['packages']]}
        return decision, artifacts, pins

    def test_actual_committed_per_package_review_is_accepted_without_generic_flag(self):
        decision, assets, pins = self.inputs()
        report = reviewed.validate_acceptance(ROOT, decision, assets, pins, decision['source_commit'])
        self.assertEqual(len(report['packages']), 329)
        self.assertNotIn('reviewed', decision)

    def test_one_missing_or_held_package_decision_is_refused(self):
        decision, assets, pins = self.inputs()
        held = copy.deepcopy(decision)
        held['packages'][0]['license_decision'] = 'hold'
        with self.assertRaisesRegex(ValueError, 'package-specific'):
            reviewed.validate_acceptance(ROOT, held, assets, pins, held['source_commit'])
        decision['packages'].pop()
        with self.assertRaisesRegex(ValueError, 'Every exact native package'):
            reviewed.validate_acceptance(ROOT, decision, assets, pins, decision['source_commit'])

    def test_new_archive_or_missing_publication_condition_cannot_reuse_old_review(self):
        decision, assets, pins = self.inputs()
        changed = copy.deepcopy(pins)
        changed['packages'][-1]['archive_sha256'] = 'a' * 64
        with self.assertRaisesRegex(ValueError, 'package identity'):
            reviewed.validate_acceptance(ROOT, decision, assets, changed, decision['source_commit'])
        decision['packages'][0]['conditions'].pop()
        with self.assertRaisesRegex(ValueError, 'package-specific'):
            reviewed.validate_acceptance(ROOT, decision, assets, pins, decision['source_commit'])

    def test_generic_boolean_or_reproduction_claim_does_not_authorize(self):
        decision, assets, pins = self.inputs()
        decision['reviewed'] = True
        with self.assertRaisesRegex(ValueError, 'typed coordinator'):
            reviewed.validate_acceptance(ROOT, decision, assets, pins, decision['source_commit'])
        del decision['reviewed']
        decision['historical_fingerprint_complete'] = True
        with self.assertRaisesRegex(ValueError, 'truthful historical'):
            reviewed.validate_acceptance(ROOT, decision, assets, pins, decision['source_commit'])
