"""Retry only unexecuted original drivers with documented output configuration."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def main():
    assert os.getuid() == 101
    root = Path('/build')
    out = root / 'main-probe-2'
    out.mkdir()
    probe = out / 'consumer.cpp'
    probe.write_text(sys.argv[1])
    env = {**os.environ, 'PYTHONDONTWRITEBYTECODE': '1',
           'MOZ_UPLOAD_DIR': str(out), 'MOZBUILD_STATE_PATH': '/build/mozbuild'}
    commands = [
        ('messages', ['make', '-C', '/build/compile/js/src', 'check-js-msg']),
        ('main', ['python3', '-B', '/src/project/js/src/tests/jstests.py',
                  '--no-progress', '--format=automation', '--timeout=300',
                  '--wpt=disabled', '-j', '2', '--failure-file',
                  str(out / 'main-failures.txt'), '/build/compile/dist/bin/js']),
        ('consumer-compile', ['c++', '-std=c++17', '-Wall', '-Wextra', '-Werror',
                              '-isystem', '/stage/usr/include/mozjs-140', str(probe),
                              '-L/stage/usr/lib', '-Wl,-rpath,/stage/usr/lib',
                              '-lmozjs-140', '-o', str(out / 'consumer')]),
        ('consumer-run', [str(out / 'consumer')]),
    ]
    records = []
    for name, args in commands:
        if name == 'consumer-run' and records[-1]['exit'] != 0:
            records.append({'name': name, 'unrun': 'Compilation failed'})
            break
        started = time.time()
        with (out / (name + '.stdout')).open('xb') as stdout, (out / (name + '.stderr')).open('xb') as stderr:
            result = subprocess.run(args, cwd='/build/compile', env=env,
                                    stdout=stdout, stderr=stderr)
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
    proof = {'scope': 'Original main/message drivers and staged dynamic C++ consumer; no ICU failure waiver, JIT replay, installation, security or GNOME acceptance',
             'drivers': records, 'consumer_source_sha256': hashlib.sha256(probe.read_bytes()).hexdigest(),
             'compiled_artifacts': len(before), 'changed_artifacts': changed}
    (out / 'result.json').write_text(json.dumps(proof, indent=2) + '\n')
    assert not changed
    raise SystemExit(0 if all(x.get('exit') == 0 for x in records) else 1)


if __name__ == '__main__':
    main()
