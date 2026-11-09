"""Verify only the original signal case with foreground signal dispositions."""
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    assert os.getuid() == 101
    work = Path('/build')
    previous = json.loads((work / 'security-tests-1/result.json').read_text())
    assert set(previous['novel_failure_diagnostics']) == {'shell/os.js'}
    assert not previous['changed_artifacts'] and not previous['changed_stage_files']
    out = work / 'signal-check-2'
    out.mkdir()
    environment = {**os.environ, 'MOZ_UPLOAD_DIR': str(out), 'PYTHONDONTWRITEBYTECODE': '1'}
    (out / 'selected-tests.txt').write_text('shell/os.js\n')
    driver = ['python3', '-B', '/src/project/js/src/tests/jstests.py', '--no-progress',
              '--format=automation', '--timeout=90', '--wpt=disabled', '-j', '1',
              '-f', str(out / 'selected-tests.txt'), '/build/compile/dist/bin/js']
    wrapper = """import os,signal,json,sys,runpy
from pathlib import Path
sys.path.insert(0,'/src/project/js/src/tests')
driver=%r
sys.argv=driver[2:]
program=runpy.run_path(driver[2],run_name='toddy_selection_probe')
options,prefix,requested,excluded=program['parse_args']()
count,tests=program['load_tests'](options,requested,excluded)
selected=[test.path for test in tests]
Path('/build/signal-check-2/selection.json').write_text(json.dumps({'count':count,'selected':selected}))
assert count==1 and selected==['shell/os.js'],'Refuse broad selection BEFORE executing tests'
Path('/build/signal-check-2/child-signals.json').write_text(json.dumps({'int_ignored':signal.getsignal(signal.SIGINT)==signal.SIG_IGN,'quit_ignored':signal.getsignal(signal.SIGQUIT)==signal.SIG_IGN}))
os.execvp(driver[0],driver)
""".replace('\n+', '\n') % driver
    def foreground_signals():
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        signal.signal(signal.SIGQUIT, signal.SIG_DFL)
    with (out / 'stdout').open('xb') as stdout, (out / 'stderr').open('xb') as stderr:
        try:
            result = subprocess.run(['python3', '-B', '-c', wrapper], cwd='/build/compile', env=environment,
                                    stdout=stdout, stderr=stderr, start_new_session=True,
                                    preexec_fn=foreground_signals, timeout=100)
            status = result.returncode
        except subprocess.TimeoutExpired:
            status = None
    text = (out / 'stdout').read_text()
    passed = re.findall(r'^TEST-PASS \| ([^|]+) \|', text, re.M)
    before = json.loads((work / 'security-tests-1/compiled-before.json').read_text())
    changed = [name for name, expected in before.items() if digest(work / name) != expected]
    observed = json.loads((out / 'child-signals.json').read_text())
    proof = {'scope': 'Original one-case SIGINT test with foreground child signal dispositions only; all original failures retained, no engine/source/assertion rebuild or full suite replay',
             'exit': status, 'passed': [x.strip() for x in passed], 'child_signals': observed,
             'parent_int_ignored': signal.getsignal(signal.SIGINT) == signal.SIG_IGN,
             'parent_quit_ignored': signal.getsignal(signal.SIGQUIT) == signal.SIG_IGN,
             'changed_artifacts': changed, 'compiled_artifacts': len(before),
             'stdout_sha256': digest(out / 'stdout'), 'stderr_sha256': digest(out / 'stderr'),
             'selection': json.loads((out / 'selection.json').read_text()),
             'original_suite_failure': previous['novel_failure_diagnostics']}
    (out / 'result.json').write_text(json.dumps(proof, indent=2) + '\n')
    assert status == 0 and proof['passed'] == ['shell/os.js']
    assert not observed['int_ignored'] and not observed['quit_ignored'] and not changed


if __name__ == '__main__':
    main()
