"""Qualify only the source-backed GtkSource duplicate-name build profile."""
import hashlib
import json
from pathlib import Path


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def qualify(root, log):
    work = Path('/mnt/lfs/sources/phase2/work/gtksourceview-patched-1')
    source = Path('/mnt/lfs/sources/phase2/inputs/gtksourceview-5.20.0-duplicate-1')
    prepared = json.loads((source / 'toddy-prepared.json').read_text())
    patch = prepared['source_patches']
    assert len(patch) == 1 and patch[0]['path'] == 'gtksourceview/implregex.c'
    assert patch[0]['patch_sha256'] == 'e11b1044f2f646415d373d0346c95ac69257190fedf9f6d0c5bdc94a951ac0a8'
    assert digest(source / patch[0]['path']) == patch[0]['after_sha256'] == '61e800f3276fda73c5bf238188ffc3e5b6ae5af4230c2a5a4593d850b2e0a877'
    assert prepared['source_sha256'] == 'e38bcd23f52b86eadf0fe4d8bde698e3a8ca102322b8b4cf1a51ac294a448c1b'
    assert prepared['original_input_files_unchanged'] == 765
    assert (source / 'toddy-base-build.sh').read_bytes() == (root / 'scripts/build/phase2/gtksourceview-build.sh').read_bytes()
    assert (source / 'toddy-probe.c').read_bytes() == (root / 'scripts/build/phase2/gtksourceview-probe.c').read_bytes()
    stage = json.loads((work / 'stage-results.json').read_text())
    assert stage['native_build_exit'] == stage['stage_exit'] == stage['c_version_data_exit'] == stage['gi_version_exit'] == 0
    for path, expected in stage['compiled_elf_sha256'].items():
        assert digest(work / path) == expected
    pure = json.loads((work / 'affected-tests-2/result.json').read_text())
    assert pure['compiled_artifacts'] == 230 and not pure['changed_artifacts']
    assert [x['name'] for x in pure['outcomes']] == ['py', 'py3', 'sh', 'json', 'xml']
    assert all(x['exit'] == 0 and not x['skips'] and len(x['tap_pass_lines']) == 1 for x in pure['outcomes'])
    raw = (log / 'native-gtksource-patched-5-report.json').read_bytes()
    assert hashlib.sha256(raw).hexdigest() == '349460bd2c0c544285e35eba0c20773f395b7e553882c3a57b79a2aea17da0f3'
    report = json.loads(raw)
    assert report['kernel'] == '7.1.8-toddy' and report['all_selected_exits_zero'] and report['compositor_exit'] == 0
    assert report['suite']['passed_case_executions'] == 3 and report['suite']['skipped_case_executions'] == 0
    assert len(report['runs']) == 1 and report['runs'][0]['name'] == 'test-regex' and report['runs'][0]['exit'] == 0
    manifest = Path('/mnt/lfs/sources/phase2/native-fixtures/gtksourceview-patched-regex-1/accepted.json')
    assert digest(manifest) == report['manifest_sha256']
    accepted = json.loads(manifest.read_text())
    assert accepted['patched_regex'] and len(accepted['tests']) == 1
    for path, expected in accepted['artifacts'].items():
        assert digest(Path('/mnt/lfs') / path.lstrip('/')) == expected
    assets = {str(p.relative_to(source)): digest(p) for p in (source / 'testsuite').rglob('*')
              if p.is_file() and not p.is_symlink()}
    assert len(assets) == report['source_test_files_unchanged'] == 39
    assert hashlib.sha256(json.dumps(assets, sort_keys=True).encode()).hexdigest() == accepted['source_test_assets_sha256']
    libraries = [p for p in (work / 'compile/gtksourceview').glob('libgtksourceview-5.so.*') if p.is_file() and not p.is_symlink()]
    assert len(libraries) == 1 and digest(libraries[0]) == digest(work / 'stage/usr/lib' / libraries[0].name)
    downstream = Path('/mnt/lfs/sources/gtksourceview-5.20.0-duplicate-capture-1.patch')
    assert digest(downstream) == patch[0]['patch_sha256']
    return work / 'stage'
