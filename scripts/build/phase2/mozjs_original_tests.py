"""Original book JS/JIT drivers, bounded workers, no assertion/fixture edits."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time


def main():
    assert os.getuid() == 101
    root = Path('/build')
    out = root / 'original-tests-1'
    out.mkdir()
    shell = '/build/compile/dist/bin/js'
    commands = [
        ('messages', ['python3', '-B', '/src/project/config/check_js_msg_encoding.py']),
        ('main', ['python3', '-B', '/src/project/js/src/tests/jstests.py',
                  '--no-progress', '--format=automation', '--timeout=300',
                  '--wpt=disabled', '-j', '2', '--failure-file',
                  str(out / 'main-failures.txt'), shell]),
        ('jit', ['python3', '-B', '/src/project/js/src/jit-test/jit_test.py',
                 '--no-slow', '--no-progress', '--format=automation',
                 '--jitflags=all', '-j', '1', '--write-failures',
                 str(out / 'jit-failures.txt'), shell]),
    ]
    records = []
    env = {**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'}
    for name, args in commands:
        started = time.time()
        cwd = '/src/project' if name == 'messages' else '/build/compile'
        with (out / (name + '.stdout')).open('xb') as stdout, (out / (name + '.stderr')).open('xb') as stderr:
            result = subprocess.run(args, cwd=cwd, env=env, stdout=stdout, stderr=stderr)
        records.append({'name': name, 'command': args, 'exit': result.returncode,
                        'seconds': time.time() - started,
                        'stdout_sha256': hashlib.sha256((out / (name + '.stdout')).read_bytes()).hexdigest(),
                        'stderr_sha256': hashlib.sha256((out / (name + '.stderr')).read_bytes()).hexdigest()})
        (out / 'progress.json').write_text(json.dumps(records, indent=2) + '\n')
    before = json.loads((root / 'test-inventory/compiled-artifacts-before.json').read_text())
    changed = []
    for name, expected in before.items():
        with (root / name).open('rb') as stream:
            if hashlib.file_digest(stream, 'sha256').hexdigest() != expected:
                changed.append(name)
    proof = {'scope': 'Original JS/main and all JIT configurations, bounded 2/1 workers; failures require individual classification, no automatic ICU waiver or security approval',
             'drivers': records, 'compiled_artifacts': len(before), 'changed_artifacts': changed}
    (out / 'result.json').write_text(json.dumps(proof, indent=2) + '\n')
    assert not changed
    raise SystemExit(0 if all(x['exit'] == 0 for x in records) else 1)


if __name__ == '__main__':
    main()
