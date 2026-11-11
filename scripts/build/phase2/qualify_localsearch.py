"""Bind the unchanged stage to real native functional and denial evidence."""
from pathlib import Path
import hashlib
import json

REPORT_SHA='99a4845d8fe077955db8f39e775a1153f93a661642142b08cf233ba10a9e7e08'
SOURCE_SHA='7b39a6c28a8acf2b172f15b2fb5ee7c7a3764c447c2f4a14caa239b7ebe61942'
RECIPE_SHA='f25eb13e03a5b1fde6763e0bea50e923bec82ebae12cbc596d0cbb2e060d2499'


def digest(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def qualify(root):
    work=Path('/mnt/lfs/sources/phase2/work/localsearch-1')
    source=Path('/mnt/lfs/sources/phase2/inputs/localsearch-3.11.1')
    log=Path('/var/log/toddy/phase2')
    prepared=json.loads((source/'toddy-prepared.json').read_text())
    assert prepared['source_sha256']==SOURCE_SHA and not prepared['source_patches']
    assert digest(source/'toddy-build.sh')==RECIPE_SHA
    assert (log/'localsearch-1.exit').read_text().strip()=='1'
    assert (log/'localsearch-collect-2.exit').read_text().strip()=='0'
    stage=json.loads((work/'stage-results.json').read_text())
    assert stage['compile_exit']==stage['stage_exit']==0
    assert len(stage['artifacts'])==186 and len(stage['stage_sha256'])==133
    assert len(stage['original_tests'])==13 and all(r['returncode']==0 and r['result']=='OK' for r in stage['original_tests'])
    fixture=json.loads((log/'localsearch-native-fixture-1.json').read_text())
    for base,key in [(source,'source_files'),(work/'compile','compile_files'),(work/'stage','stage_files')]:
        actual={str(p.relative_to(base)):digest(p) for p in base.rglob('*') if p.is_file() and not p.is_symlink()}
        assert actual==fixture[key]
    assert fixture['stage_files']==stage['stage_sha256']
    for name,sha in stage['artifacts'].items():assert digest(work/'compile'/name)==sha
    report_file=log/'native-localsearch-functional-report-4.json'
    assert report_file.stat().st_uid==0 and not report_file.is_symlink()
    report=json.loads(report_file.read_text())
    assert hashlib.sha256(json.dumps(report,sort_keys=True).encode()).hexdigest()==REPORT_SHA
    assert report['kernel']=='7.1.8-toddy' and report['pid1']=='systemd'
    assert report['input_manifests_unchanged']
    details=report['details'];assert details['all_selected_passed'] and details['programs']==9 and details['cases']==20
    expected=fixture['expected_cases']
    assert {r['name']:r['cases'] for r in details['runs']}==expected
    assert all(r['exit']==0 and r['passed'] and not r['timed_out'] for r in details['runs'])
    assert details['positive_control']['exit']==0 and not details['positive_control']['timed_out']
    macros=(work/'compile/config-miners.h').read_text().splitlines()
    assert '#define HAVE_LANDLOCK' in macros and '#define HAVE_LIBSECCOMP' in macros
    return stage
