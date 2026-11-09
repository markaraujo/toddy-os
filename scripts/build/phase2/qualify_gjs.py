"""Require real original GJS C and native Wayland suite evidence before promotion."""
import hashlib
import json
from pathlib import Path


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def qualify(root, log):
    work = Path('/mnt/lfs/sources/phase2/work/gjs-1')
    source = Path('/mnt/lfs/sources/phase2/inputs/gjs-1.88.1')
    for prepared, canonical in [('toddy-build.sh', 'gjs-build.sh'), ('toddy-probe.c', 'gjs-probe.c'), ('toddy-probe.py', 'gjs_probe.py')]:
        assert (source / prepared).read_bytes() == (root / 'scripts/build/phase2' / canonical).read_bytes()
    stage = json.loads((work / 'stage-results.json').read_text())
    assert stage['native_build_exit'] == stage['stage_exit'] == stage['native_c_consumer_exit'] == 0
    assert len(stage['original_api_drivers']) == 2 and all(row['returncode'] == 0 and row['result'] == 'OK' for row in stage['original_api_drivers'])
    assert [row['exit'] for row in stage['cli']['records']] == [0, 0, 1]
    raw = (log / 'native-gjs-6-report.json').read_bytes()
    assert hashlib.sha256(raw).hexdigest() == 'ca60c6fef7c0a2719e5da2c0c85136ab7e207f2703639d6db7522b8ab8865fbf'
    report = json.loads(raw)
    assert report['kernel'] == '7.1.8-toddy' and report['all_selected_exits_zero'] and report['compositor_exit'] == 0
    run, = report['suite']['runs']
    assert run['exit'] == 0 and run['meson_coverage_complete'] and run['meson_all_results_ok']
    assert len(run['meson_original_results']) == 78 and all(row['result'] == 'OK' and row['returncode'] == 0 for row in run['meson_original_results'])
    assert report['suite']['passed_case_executions'] == 2741 and report['suite']['skipped_case_executions'] == 147
    manifest = Path('/mnt/lfs/sources/phase2/native-fixtures/gjs-1/accepted.json')
    assert digest(manifest) == report['manifest_sha256']
    accepted = json.loads(manifest.read_text())
    for path, expected in accepted['artifacts'].items():
        assert digest(Path('/mnt/lfs') / path.lstrip('/')) == expected
    assets = {str(p.relative_to(source)): digest(p) for directory in accepted['asset_dirs']
              for p in (source / directory).rglob('*') if p.is_file() and not p.is_symlink()}
    assert len(assets) == report['source_test_files_unchanged'] == 361
    assert hashlib.sha256(json.dumps(assets, sort_keys=True).encode()).hexdigest() == accepted['source_test_assets_sha256']
    assert digest(work / 'compile/libgjs.so.0.0.0') == digest(work / 'stage/usr/lib/libgjs.so.0.0.0')
    from gjs_stage_binary import validate_transition
    transition=validate_transition((work / 'compile/gjs-console').read_bytes(), (work / 'stage/usr/bin/gjs-console').read_bytes())
    (log / 'gjs-install-runpath-proof.json').write_text(json.dumps(transition,indent=2)+'\n')
