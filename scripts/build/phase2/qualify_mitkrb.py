"""Bind the frozen patched Kerberos source to retained native stage evidence."""
from pathlib import Path
import hashlib
import json
import stat


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def validate_original_command(command):
    expected = ['/bin/bash', '/opt/toddy-build/scripts/build/phase2/isolated.sh',
                '/mnt/lfs/sources/phase2/inputs/krb5-1.22.2',
                '/mnt/lfs/sources/phase2/work/mitkrb-1', 'bash', '/src/toddy-build.sh']
    assert command == expected, 'Unexpected original Kerberos build command'


def qualify(root):
    source = Path('/mnt/lfs/sources/phase2/inputs/krb5-1.22.2')
    work = Path('/mnt/lfs/sources/phase2/work/mitkrb-1')
    log = Path('/var/log/toddy/phase2')
    prepared = json.loads((source / 'toddy-prepared.json').read_text())
    # Published B02-mitkrb-input.json prepared_input, canonical compact JSON.
    assert hashlib.sha256(json.dumps(prepared,sort_keys=True,separators=(',',':')).encode()).hexdigest() == '6cbcd87f7ecac4e3288f4df6ba45037dc1f798700cfbe04af0534eefd88cdb61'
    locked = json.loads((root / 'config/phase2/sources.lock.json').read_text())['components']
    selected = next(row for row in locked if row['name'] == 'mitkrb')
    assert selected['version'] == '1.22.2'
    assert prepared['source_sha256'] == selected['sha256']
    assert digest(source / 'toddy-build.sh') == prepared['recipe_sha256']
    assert digest(source / 'toddy-probe.c') == prepared['probe_sha256']
    assert (source / 'toddy-probe.c').read_bytes() == (root / 'scripts/build/phase2/mitkrb-probe.c').read_bytes()
    expected_patches = {row['sha256'] for row in locked if row['name'] in
                        ('mitkrb-upstream-fix', 'mitkrb-security-fix', 'mitkrb-openssl4-fixes')}
    assert len(expected_patches) == 3
    assert {row['patch_sha256'] for row in prepared['source_patches'] if 'patch_sha256' in row} == expected_patches
    book_edits = [row for row in prepared['source_patches'] if 'patch_sha256' not in row]
    assert len(book_edits) == 1 and book_edits[0]['path'] == 'src/plugins/kdb/db2/libdb2/test/run.test'
    assert book_edits[0]['after_sha256'] == '425d51d79f40da1b18773bc4a1c96ff005e38b1495db61844cd1104cfcb8166b'
    # Later patches may touch a file again: compare its final authenticated state.
    patched = {row['path']: row['after_sha256'] for row in prepared['source_patches']}
    assert all(digest(source / path) == sha for path, sha in patched.items())
    scratch = json.loads((log / 'mitkrb-shared-scratch-1.json').read_text())
    assert scratch['state'] == 'mounted' and work.stat().st_ino == scratch['source_inode']
    validate_original_command(json.loads((log / 'mitkrb-1.job.json').read_text())['command'])
    for name, code in [('mitkrb-1', 2), ('mitkrb-finish-2', 1), ('mitkrb-collect-3', 1), ('mitkrb-metadata-4', 0)]:
        assert int((log / (name + '.exit')).read_text()) == code
    recipe = (root / 'scripts/build/phase2/mitkrb-build.sh').read_text()
    command = ('from pathlib import Path\n' + (root / 'scripts/build/phase2/mitkrb_metadata.py').read_text()
               + '\nmain(' + repr(recipe) + ')\n')
    assert json.loads((log / 'mitkrb-metadata-4.job.json').read_text())['command'][-1] == command
    before = json.loads((work / 'before-collect-3.json').read_text())
    result = json.loads((work / 'stage-results.json').read_text())
    retained = json.loads((work / 'metadata-4-retained.json').read_text())
    assert result['compile_exit'] == result['stage_exit'] == 0
    assert result['version'] == '1.22.2' and retained['no_compiler_test_stage_or_consumer_execution']
    for base, key in [('compile', 'artifacts'), ('stage', 'stage_sha256')]:
        actual = {str(p.relative_to(work / base)): digest(p) for p in (work / base).rglob('*')
                  if p.is_file() and not p.is_symlink()
                  and (key != 'artifacts' or p.open('rb').read(4) == b'\x7fELF')}
        assert actual and actual == result[key] == before[key]
    assert all(digest(work / name) == sha for name, sha in retained['logs_and_consumer_unchanged'].items())
    assert all(digest(work / name) == sha for name, sha in before['reused_logs'].items())
    assert (work / 'local-probe.log').read_text() == result['consumer']
    assert result['DB2_report_rows'] == 24 and len(result['DB2_unique_case_ids']) == 20
    assert result['DB2_skipped'] == [{'case': 20, 'reason': 'skipped, dictionary too small'}]
    assert result['DB2_book_test12_excluded']
    for path in (work / 'stage').rglob('*'):
        assert not path.lstat().st_mode & (stat.S_ISUID | stat.S_ISGID)
    assert (work / 'stage/usr/bin/ksu').stat().st_mode & 0o7777 == 0o755
    return result
