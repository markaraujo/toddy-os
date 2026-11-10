"""Bind corrected CUPS layout to exact retained source/jobs/compiler/stage results."""
from pathlib import Path
import ast
import hashlib
import json
import stat


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def canonical_digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def qualify(root):
    source = Path('/mnt/lfs/sources/phase2/inputs/cups-2.4.19')
    work = Path('/mnt/lfs/sources/phase2/work/cups-layout-1')
    log = Path('/var/log/toddy/phase2')
    prepared = json.loads((source / 'toddy-prepared.json').read_text())
    assert canonical_digest(prepared) == 'f9c20e95af66cea87e3f0d6bdbb0fab2d659786adde229fb673ba610f1e7ed99'
    locked = next(row for row in json.loads((root / 'config/phase2/sources.lock.json').read_text())['components'] if row['name'] == 'cups')
    assert prepared['source_sha256'] == locked['sha256'] and not prepared['source_patches']
    assert digest(source / 'toddy-build.sh') == prepared['recipe_sha256']
    assert digest(source / 'toddy-probe.c') == prepared['probe_sha256'] == digest(root / 'scripts/build/phase2/cups-probe.c')
    from shared_source_inputs import fingerprint, check_alias
    shared = json.loads((log / 'cups-input-scratch-1.json').read_text())
    assert shared['state'] == 'complete'
    check_alias(Path(shared['source']), source)
    assert fingerprint(Path(shared['source'])) == shared['source_fingerprint']
    worker = json.loads((log / 'cups-layout-shared-scratch-1.json').read_text())
    assert worker['state'] == 'mounted' and work.stat().st_ino == worker['source_inode'] == 4675
    commands = {}
    for name, code, expected in [
        ('cups-layout-1', 1, '819d5976e36fe966b8450e1c8daa2c56b19bd600cb57dd659dd3504bf1f80bbe'),
        ('cups-layout-finish-2', 0, '9e3eada3c222812b2ceed781cf00acd3966f702aa7330c75a2931de0e7c4e50d')]:
        assert int((log / (name + '.exit')).read_text()) == code
        command = json.loads((log / (name + '.job.json')).read_text())['command']
        assert hashlib.sha256(json.dumps(command, separators=(',', ':')).encode()).hexdigest() == expected
        commands[name] = command
    recipe = (root / 'scripts/build/phase2/cups-build.sh').read_text()
    call = ast.parse(commands['cups-layout-1'][-1]).body[-1].value
    assert isinstance(call, ast.Call) and isinstance(call.func, ast.Name) and call.func.id == 'main'
    initial_recipe = ast.literal_eval(call.args[0])
    assert initial_recipe.split("python3 - <<'PYTEST'", 1)[0] == recipe.split("python3 - <<'PYTEST'", 1)[0]
    marker = '# Preserve compiled lp/lpadmin policy'
    assert initial_recipe.split(marker, 1)[1] == recipe.split(marker, 1)[1]
    expected_resume = (root / 'scripts/build/phase2/cups_layout_finish.py').read_text() + '\nmain(' + repr(recipe) + ')\n'
    assert commands['cups-layout-finish-2'][-1] == expected_resume
    old = json.loads((work / 'resource-observation.json').read_text())
    assert old['resource_interrupted'] and old['recipe_exit'] == -15 and old['minimum_polled_free_bytes'] < 512 * 1024**2
    observation = json.loads((work / 'resource-observation-2.json').read_text())
    assert not observation['resource_interrupted'] and observation['recipe_exit'] == 0 and observation['minimum_polled_free_bytes'] >= 512 * 1024**2
    layout = json.loads((work / 'layout-configured.json').read_text())
    assert layout == {'prefix': '/', 'exec_prefix': '/usr', 'sysconfdir': '/etc', 'localstatedir': '/var', 'SERVERROOT': '$(BUILDROOT)/etc/cups', 'REQUESTS': '$(BUILDROOT)/var/spool/cups', 'STATEDIR': '$(BUILDROOT)/run/cups'}
    result = json.loads((work / 'stage-results.json').read_text())
    assert result['compile_exit'] == result['stage_exit'] == 0 and result['version'] == '2.4.19'
    assert [row['name'] for row in result['original_tests']] == ['testarray', 'testfile', 'testi18n', 'testipp', 'testhttp', 'testoptions', 'testpwg', 'testraster', 'testppd']
    assert all(row['exit'] == 0 for row in result['original_tests'])
    assert result['original_tests'] == result['raw_original_results']
    assert result['full_original_printing_suite_pending'] and not result['SNMP_remote_diagnostic']['qualified']
    retained = json.loads((work / 'layout-finish-2-retained.json').read_text())
    assert retained['main_compiler_and_array_not_replayed'] and retained['original_Makefile_restored']
    assert all(digest(work / name) == sha for name, sha in retained['original_logs_unchanged'].items())
    before = json.loads((work / 'before-layout-finish-2.json').read_text())
    assert digest(work / 'tree/cups/Makefile') == before['Makefile_sha256']
    for base, key in [('tree', 'artifacts'), ('stage', 'stage_sha256')]:
        actual = {str(p.relative_to(work / base)): digest(p) for p in (work / base).rglob('*')
                  if p.is_file() and not p.is_symlink() and (key != 'artifacts' or p.open('rb').read(4) == b'\x7fELF')}
        assert actual and actual == result[key]
    assert all(result['artifacts'][name] == sha for name, sha in before['artifacts'].items())
    assert (work / 'local-probe.log').read_text() == result['consumer']
    assert not (work / 'stage/usr/etc').exists() and not (work / 'stage/usr/var').exists()
    assert (work / 'stage/etc/cups/cupsd.conf').is_file() and (work / 'stage/var/spool/cups').is_dir()
    for path in (work / 'stage').rglob('*'):
        assert not path.lstat().st_mode & (stat.S_ISUID | stat.S_ISGID)
    return result
