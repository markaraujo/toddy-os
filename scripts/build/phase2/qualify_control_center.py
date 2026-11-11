"""Verify retained Settings sources, compiler output, portable tests and stage."""
import hashlib
import json
from pathlib import Path

from verify_stage import inspect_stage

ROOT = Path('/opt/toddy-build')
WORK = Path('/mnt/lfs/sources/phase2/work/gnome-control-center-1')
INPUT = Path('/mnt/lfs/sources/phase2/inputs/gnome-control-center-50.4')
LOG = Path('/var/log/toddy/phase2')
ARCHIVES = Path('/run/toddy-samba-client-1/gnome-control-center-input-1/archives')


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def qualify():
    rows = json.loads((ROOT / 'config/phase2/sources.lock.json').read_text())['components']
    prepared = json.loads((INPUT / 'toddy-prepared.json').read_text())
    selected = [next(row for row in rows if row['name'] == name) for name in ('gnome-control-center', 'tecla')]
    assert prepared['source_sha256'] == selected[0]['sha256'] and prepared['additional_sources'] == selected[1:]
    assert prepared['recipe_sha256'] == digest(INPUT / 'toddy-build.sh') == digest(ROOT / 'scripts/build/phase2/gnome-control-center-build.sh')
    assert not prepared['source_patches']
    for row in selected:
        assert digest(ARCHIVES / row['filename']) == row['sha256']
    for name in ('gnome-control-center-1','gnome-control-center-tests-collect-2','gnome-control-center-stage-1'):
        assert (LOG / (name + '.exit')).read_text().strip() == '0'
    original = json.loads((WORK / 'compile-results.json').read_text())
    assert original['compile_exit'] == 0 and len(original['artifacts']) == 391
    for relative, sha in original['artifacts'].items():
        assert digest(WORK / 'compile' / relative) == sha
    tests = json.loads((WORK / 'portable-tests-results.json').read_text())
    assert len(tests['rows']) == 4 and tests['unchanged_elf_count'] == 391
    assert all(row['returncode'] == 0 and row['result'] == 'OK' for row in tests['rows'])
    current = inspect_stage(WORK / 'stage')
    assert current['manifest_sha256'] == '47e546ea880ffa5beb3d2bdeb8e6a3f4cad85adad0192b03e052752df965c275'
    return current['entries'], selected
