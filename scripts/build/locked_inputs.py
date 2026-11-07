"""Resolve explicitly frozen baseline and security inputs; no network access."""
import json


def locked_source(root, filename):
    baseline = json.loads((root/'config/sources.lock.json').read_text())
    if baseline['status'] != 'verified':
        raise ValueError('Baseline source lock is not verified')
    for row in baseline['packages']:
        if row['filename'] == filename:
            return row
    overlay_path = root/'config/security-overlay.lock.json'
    if overlay_path.exists():
        overlay = json.loads(overlay_path.read_text())
        if overlay['status'] == 'frozen_for_final_build':
            for row in overlay['components']:
                if row['filename'] == filename:
                    return dict(row)
    supplemental_path = root/'config/supplemental-sources.lock.json'
    if supplemental_path.exists():
        supplemental = json.loads(supplemental_path.read_text())
        if supplemental['status'] == 'frozen_for_native_build':
            for row in supplemental['components']:
                if row['filename'] == filename:
                    return dict(row)
    phase2_path = root/'config/phase2/sources.lock.json'
    if phase2_path.exists():
        phase2 = json.loads(phase2_path.read_text())
        if phase2['status'] == 'frozen_for_phase2_build':
            for row in phase2['components']:
                if row['filename'] == filename:
                    return dict(row)
    return None
