"""Verify Enchant stage and original tests without replaying a build or test."""
from pathlib import Path
import hashlib
import json
import re


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def qualify(root):
    source = Path('/mnt/lfs/sources/phase2/inputs/enchant-2.8.19')
    work = Path('/mnt/lfs/sources/phase2/work/enchant-1')
    logs = Path('/var/log/toddy/phase2')
    prepared = json.loads((source / 'toddy-prepared.json').read_text())
    assert prepared['source_sha256'] == 'c8d70991d544ee39274b96bd01d2858a009fe732ff43f2aaf605fd61ecd06f60'
    assert prepared['extra_source']['sha256'] == '328feff910901baa11b4b28b57da1bae273eb26539969c501d77d814c60247fa'
    assert prepared['source_patches'] == []
    assert digest(source / 'toddy-build.sh') == prepared['recipe_sha256'] == 'c2c74aba728c71cffe61a1ce11a5e0facf827b75417dd88593fd7a9cbec4aeab'
    assert digest(source / 'toddy-probe.py') == prepared['probe_sha256']
    assert (source / 'toddy-probe.py').read_bytes() == (root / 'scripts/build/phase2/enchant-probe.py').read_bytes()
    for job, code, payload in [
        ('enchant-1', '1', None),
        ('enchant-sdk-metadata-2', '126', 'enchant-resume-sdk-metadata.sh'),
        ('enchant-script-interpreter-3', '1', 'enchant-resume-script-interpreter.sh'),
        ('enchant-private-sdk-include-4', '1', 'enchant-resume-private-sdk-include.sh'),
        ('enchant-provider-explicit-5', '0', 'enchant-provider-explicit-and-collect.sh'),
    ]:
        assert (logs / (job + '.exit')).read_text().strip() == code
        if payload:
            command = json.loads((logs / (job + '.job.json')).read_text())['command']
            assert command[-1] == (root / 'scripts/build/phase2' / payload).read_text()
    result = json.loads((work / 'stage-results.json').read_text())
    assert result['compile_exit'] == result['stage_exit'] == 0
    assert result['private_sdk_original_cases'] == 267
    assert result['private_sdk_installed_to_system'] is False
    assert [(r['name'], r['cases']) for r in result['original_tests']] == [('main', 432), ('providers', 0), ('providers-explicit-aspell', 25)]
    assert result['original_tests'][1]['zero_case_not_a_test_pass'] is True
    for log, count in [('sdk-original-build-tests.log', 267), ('compile/tests/main.log', 432), ('original-provider-explicit.log', 25)]:
        assert re.findall(r'Success: ([0-9]+) tests passed[.]', (work / log).read_text()) == [str(count)]
    for resource in result['resources'].values():
        assert resource['exit'] == 0 and not resource['interrupted']
        assert resource['minimum_free'] >= 16 * 1024**3
    for base, key in [('compile', 'artifacts'), ('stage', 'stage_sha256')]:
        actual = {str(p.relative_to(work / base)): digest(p) for p in (work / base).rglob('*') if p.is_file() and not p.is_symlink() and (key != 'artifacts' or p.open('rb').read(4) == b'\x7fELF')}
        assert actual and actual == result[key]
    for relative, sha in json.loads((work / 'sdk-resume-2-before.json').read_text()).items():
        assert digest(work / relative) == sha
    assert result['consumer'] == json.loads((work / 'native-consumer.json').read_text())
    assert result['consumer']['provider'] == 'aspell'
    assert result['consumer']['editor_or_GUI_tested'] is False
    assert len(result['original_program_scripts_not_executed']) == 4
    return result
