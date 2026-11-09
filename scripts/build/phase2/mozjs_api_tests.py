"""Run the original compiled JSAPI suite, preserving results and ELF identity."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time


def main():
    assert os.getuid() == 101
    root = Path('/build')
    out = root / 'api-tests-1'
    out.mkdir()
    before = json.loads((root / 'test-inventory/compiled-artifacts-before.json').read_text())
    started = time.time()
    with (out / 'stdout').open('xb') as stdout, (out / 'stderr').open('xb') as stderr:
        result = subprocess.run(['/build/compile/dist/bin/jsapi-tests'],
                                cwd='/build/compile', stdout=stdout, stderr=stderr)
    changed = []
    for name, expected in before.items():
        with (root / name).open('rb') as stream:
            actual = hashlib.file_digest(stream, 'sha256').hexdigest()
        if actual != expected:
            changed.append(name)
    proof = {'scope': 'Original complete compiled JSAPI suite only; main/JIT, dynamic consumer and security qualification pending',
             'exit': result.returncode, 'seconds': time.time() - started,
             'compiled_artifacts': len(before), 'changed_artifacts': changed,
             'stdout_sha256': hashlib.sha256((out / 'stdout').read_bytes()).hexdigest(),
             'stderr_sha256': hashlib.sha256((out / 'stderr').read_bytes()).hexdigest()}
    (out / 'result.json').write_text(json.dumps(proof, indent=2) + '\n')
    assert not changed
    raise SystemExit(result.returncode)


if __name__ == '__main__':
    main()
