"""Bind the exact Nautilus stage to its focused native Wayland evidence."""
import hashlib
import json
from pathlib import Path
import subprocess

REPORT_SHA = '6532603e8188fbd48afbb2268db128c0219e5a8fbe3feb24a8d3520d04edfd24'
FIXTURE_SHA = 'ac5c890e5cceaee2b196400e343ce4490e2a2b6fb32ad7b5f8324aa78506e492'
SOURCE_SHA = 'e1e285efddf42ed30dda5b29f7f8d242dab4bc1409a9054863b367bad4b34d5a'
RECIPE_SHA = '350eca26d451f25c8ba65fc1992603ff94e83ba6f8536dbeb90fd1e033f61cfd'


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def qualify(root):
    work = Path('/mnt/lfs/sources/phase2/work/nautilus-1')
    source = Path('/mnt/lfs/sources/phase2/inputs/nautilus-50.2.2')
    log = Path('/var/log/toddy/phase2')
    prepared = json.loads((source/'toddy-prepared.json').read_text())
    assert prepared['source_sha256'] == SOURCE_SHA and not prepared['source_patches']
    assert digest(source/'toddy-build.sh') == RECIPE_SHA
    assert digest(root/'scripts/build/phase2/nautilus-build.sh') == RECIPE_SHA
    assert (log/'nautilus-1.exit').read_text().strip() == '0'
    fixture_file = log/'nautilus-native-fixture-1.json'
    assert digest(fixture_file) == FIXTURE_SHA
    fixture = json.loads(fixture_file.read_text())
    for base, key in [(source, 'source_files'), (work/'compile', 'compile_files'),
                      (work/'stage', 'stage_files')]:
        actual = {str(p.relative_to(base)): digest(p) for p in base.rglob('*')
                  if p.is_file() and not p.is_symlink()}
        assert actual == fixture[key], key
    stage = json.loads((work/'stage-results.json').read_text())
    assert stage['compile_exit'] == stage['stage_exit'] == 0
    assert len(stage['artifacts']) == 277 and len(stage['stage_sha256']) == 154
    assert stage['registered_test_count'] == 24
    assert stage['stage_sha256'] == fixture['stage_files']
    for name, sha in stage['artifacts'].items():
        assert digest(work/'compile'/name) == sha
    for section, sha in stage['installed_code_sections_unchanged'].items():
        for path in [work/'compile/src/nautilus', work/'stage/usr/bin/nautilus']:
            data = subprocess.check_output(['readelf', '-x', section, str(path)])
            assert hashlib.sha256(data).hexdigest() == sha
    report_file = log/'native-nautilus-focused-report-3.json'
    assert report_file.stat().st_uid == 0 and not report_file.is_symlink()
    report = json.loads(report_file.read_text())
    assert hashlib.sha256(json.dumps(report, sort_keys=True).encode()).hexdigest() == REPORT_SHA
    assert report['kernel'] == '7.1.8-toddy' and report['pid1'] == 'systemd'
    assert report['all_selected_exits_zero'] and report['schema_unchanged']
    assert report['input_transport']['exact_source_compile_stage_restored']
    tests = report['original_tests']
    assert tests['all_selected_passed'] and tests['readonly_inputs_unchanged']
    assert tests['programs_total'] == tests['expected_programs'] == 12
    assert tests['programs_executed'] == 1 and tests['programs_reused'] == 11
    assert tests['new_passed_GLib_cases'] == 9 and tests['reused_passed_GLib_cases'] == 64
    assert tests['skipped_cases'] == 0 and tests['positive_control']['exit'] == 0
    assert tests['qualified_prefix']['input_fixture_sha256'] == FIXTURE_SHA
    assert tests['qualified_prefix']['all_original_inputs_unchanged']
    assert len(tests['runs']) == 1 and tests['runs'][0]['passed']
    assert tests['runs'][0]['exit'] == 0 and not tests['runs'][0].get('timed_out', False)
    return stage
