"""Qualify the explicit140.17 engine profile without calling Intl failures passes."""
import hashlib
import json
from pathlib import Path


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def qualify(root):
    log = Path('/var/log/toddy/phase2')
    assert (log / 'mozjs-security-1.exit').read_text().strip() == '0'
    assert (log / 'mozjs-security-tests-2.exit').read_text().strip() == '1'
    assert (log / 'mozjs-signal-check-4.exit').read_text().strip() == '0'
    source = Path('/mnt/lfs/sources/phase2/inputs/mozjs-tool-140.17.0')
    work = Path('/mnt/lfs/sources/phase2/work/mozjs-security-1')
    expected = (root / 'scripts/build/phase2/mozjs-build.sh').read_text()
    expected = expected.replace('SpiderMonkey140.14', 'SpiderMonkey140.17 ADR0147 security candidate')
    expected = expected.replace("assert '140.14' in version", "assert '140.17' in version")
    assert (source / 'toddy-build.sh').read_text() == expected
    prepared = json.loads((source / 'toddy-prepared.json').read_text())
    assert prepared['sources'][0]['sha256'] == '4d6ed3b18b2069c55bab12d8ba95da6013ac0b036d8a031df8b9f39a25d05c33'
    assert len(prepared['source_patches']) == 5
    for patch in prepared['source_patches']:
        assert patch['patch_sha256'] == '24183878004982be0d7d87af2daa49a36d327a279b0abcf222c0c99e805e2ed7'
        assert digest(source / 'project' / patch['path']) == patch['after_sha256']
    result = json.loads((work / 'security-tests-1/result.json').read_text())
    assert result['version'] == 'JavaScript-C140.17.0'
    assert not result['changed_artifacts'] and not result['changed_stage_files']
    assert set(result['novel_failure_diagnostics']) == {'shell/os.js'} and result['main_suite_end_observed']
    reconciled = json.loads((work / 'signal-check-2/result.json').read_text())
    assert reconciled['exit'] == 0 and reconciled['passed'] == ['shell/os.js']
    assert reconciled['selection'] == {'count': 1, 'selected': ['shell/os.js']}
    assert reconciled['parent_int_ignored'] and reconciled['parent_quit_ignored']
    assert not reconciled['child_signals']['int_ignored'] and not reconciled['child_signals']['quit_ignored']
    assert not reconciled['changed_artifacts'] and reconciled['compiled_artifacts'] == 501
    assert reconciled['original_suite_failure'] == result['novel_failure_diagnostics']
    assert sum(result['main_automation_counts'].values()) == 52627
    baseline = json.loads((work / 'security-tests-1/baseline-failures.json').read_text())
    assert len(baseline) == 103
    assert all(baseline.get(name) == details for name, details in result['main_failures'].items() if name != 'shell/os.js')
    assert len(result['main_failures']) == result['main_automation_counts']['TEST-UNEXPECTED-FAIL']
    assert result['main_automation_counts']['TEST-KNOWN-FAIL'] == 1932
    assert result['strict_ascii_property']['files'] == 5 and not result['strict_ascii_property']['failed']
    assert [r['name'] for r in result['drivers']] == ['api', 'main', 'jit', 'consumer-compile', 'consumer-run']
    assert all(r['exit'] == 0 for r in result['drivers'] if r['name'] != 'main')
    assert result['drivers'][1]['exit'] == (1 if result['main_failures'] else 0)
    before = json.loads((work / 'security-tests-1/compiled-before.json').read_text())
    assert len(before) == result['compiled_artifacts']
    for name, expected_digest in before.items():
        assert digest(work / name) == expected_digest
    assert 'Passed: ran 901 tests.' in (work / 'security-tests-1/api.stdout').read_text()
    assert digest(work / 'security-tests-1/consumer.cpp') == digest(root / 'scripts/build/phase2/mozjs-probe.cpp')
    assert digest(work / 'stage/usr/lib/libmozjs-140.so') == digest(work / 'compile/dist/bin/libmozjs-140.so')
    assert digest(work / 'stage/usr/bin/js140') == digest(work / 'compile/dist/bin/js')
    return work / 'stage'
