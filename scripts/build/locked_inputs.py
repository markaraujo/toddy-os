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
    return None
