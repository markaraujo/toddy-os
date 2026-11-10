"""Resume corrected CUPS after relocating only the large testfile transient data."""
from pathlib import Path
import ast
import hashlib
import json
import os
import shlex
import shutil
import signal
import subprocess
import tempfile
import time
import traceback


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def elfs(base):
    return {str(p.relative_to(base)): digest(p) for p in base.rglob('*')
            if p.is_file() and not p.is_symlink() and p.open('rb').read(4) == b'\x7fELF'}


def steps(recipe):
    work = Path('/build')
    receipt = work / 'before-layout-finish-2.json'
    assert not receipt.exists() and not list((work / 'stage').iterdir())
    assert not (work / 'original-stage.log').exists()
    observation = json.loads((work / 'resource-observation.json').read_text())
    assert observation['resource_interrupted'] and observation['recipe_exit'] == -15
    original = json.loads((work / 'original-local-tests.json').read_text())
    assert len(original) == 1 and original[0]['name'] == 'testarray' and original[0]['exit'] == 0
    assert not (work / 'tree/cups/testfile').exists(), 'GNU make deleted interrupted target; inspect any changed outcome'
    assert (work / 'tree/cups/testfile.o').is_file()
    layout = json.loads((work / 'layout-configured.json').read_text())
    assert layout['prefix'] == '/' and layout['SERVERROOT'] == '$(BUILDROOT)/etc/cups'
    before = elfs(work / 'tree')
    logs = {name: digest(work / name) for name in ['original-build.log', 'testarray.log', 'testfile.log', 'original-local-tests.json', 'configure.log']}
    makefile = work / 'tree/cups/Makefile'
    original_make = makefile.read_bytes()
    receipt.write_text(json.dumps({'artifacts': before, 'retained_logs': logs,
                                  'Makefile_sha256': digest(makefile)}, indent=2) + '\n')
    program = recipe.split("python3 - <<'PYTEST'\n", 1)[1].split('\nPYTEST', 1)[0]
    function = next(n for n in ast.parse(program).body if isinstance(n, ast.FunctionDef) and n.name == 'run_local_unit')
    namespace = dict(w=work, Path=Path, subprocess=subprocess, tempfile=tempfile, shutil=shutil, shlex=shlex)
    exec(compile(ast.Module(body=[function], type_ignores=[]), '<CUPS-original-unit-runner>', 'exec'), namespace)
    env = dict(os.environ, LC_ALL='C', LD_LIBRARY_PATH='/build/tree/cups')
    results = [dict(original[0], reused_original_result=True)]
    for name in ['testfile', 'testi18n', 'testipp', 'testhttp', 'testoptions', 'testpwg', 'testraster', 'testppd']:
        with (work / ('layout-2-' + name + '.log')).open('xb') as log:
            result = namespace['run_local_unit'](name, env, log)
        results.append({'name': name, 'exit': result.returncode})
        (work / 'layout-2-local-tests.json').write_text(json.dumps(results, indent=2) + '\n')
        assert result.returncode == 0, name
    assert makefile.read_bytes() == original_make
    assert all(elfs(work / 'tree')[name] == sha for name, sha in before.items())
    space = os.statvfs(work)
    assert space.f_bavail * space.f_frsize >= 512 * 1024**2 + 17 * 1024**2 + 8 * 1024**2
    marker = '# Preserve compiled lp/lpadmin policy'
    assert recipe.count(marker) == 1
    suffix = recipe[recipe.index(marker):]
    assert suffix.count("(w/'original-local-tests.json')") == 1
    suffix = suffix.replace("(w/'original-local-tests.json')", "(w/'layout-2-local-tests.json')")
    subprocess.run(['bash', '-euo', 'pipefail', '-c', 'cd /build/tree\n' + suffix], check=True)
    assert all(elfs(work / 'tree')[name] == sha for name, sha in before.items())
    assert all(digest(work / name) == sha for name, sha in logs.items())
    (work / 'layout-finish-2-retained.json').write_text(json.dumps({
        'original_ELFs_unchanged': len(before), 'original_logs_unchanged': logs,
        'original_Makefile_restored': True, 'main_compiler_and_array_not_replayed': True,
        'testfile_transients': 'existing private tmpfs; same code/arguments/static fixture/linker',
    }, indent=2) + '\n')


def main(recipe):
    assert os.getuid() == os.getgid() == 101
    receipt = Path('/build/resource-observation-2.json')
    assert not receipt.exists()
    child = os.fork()
    if child == 0:
        os.setsid()
        try:
            steps(recipe)
        except BaseException:
            traceback.print_exc()
            os._exit(1)
        os._exit(0)
    minimum = None
    interrupted = False
    while True:
        space = os.statvfs('/build')
        available = space.f_bavail * space.f_frsize
        minimum = available if minimum is None else min(minimum, available)
        pid, status = os.waitpid(child, os.WNOHANG)
        if pid:
            break
        if available < 512 * 1024**2 + 8 * 1024**2:
            interrupted = True
            os.killpg(child, signal.SIGTERM)
            _, status = os.waitpid(child, 0)
            break
        time.sleep(0.02)
    result = os.waitstatus_to_exitcode(status)
    observation = {'minimum_polled_free_bytes': minimum, 'resource_interrupted': interrupted,
                   'recipe_exit': result, 'reserve_bytes': 512 * 1024**2,
                   'interrupt_margin_bytes': 8 * 1024**2, 'poll_interval_seconds': 0.02}
    receipt.write_text(json.dumps(observation, indent=2) + '\n')
    assert not interrupted and result == 0, observation
