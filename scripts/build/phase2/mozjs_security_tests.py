"""Critical original engine coverage for ADR0147, with exact retained failures."""
import collections
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def failure_details(text):
    headers = list(re.finditer(r'^## (.+): rc = (-?\d+), run time = [^\n]+$', text, re.M))
    records = {}
    for i, match in enumerate(headers):
        block = text[match.end():headers[i + 1].start() if i + 1 < len(headers) else len(text)]
        errors = [line.replace('/src/project/js/src/tests/', '') for line in block.splitlines()
                  if 'Error:' in line or 'Test262Error:' in line]
        records[match[1]] = {'exit': int(match[2]), 'primary_diagnostics': errors}
    return records


def main():
    assert os.getuid() == 101
    root = Path('/build')
    stage = json.loads((root / 'stage-results.json').read_text())
    assert stage['version'] == 'JavaScript-C140.17.0' and stage['native_build_exit'] == stage['stage_exit'] == 0
    version = subprocess.check_output(['/stage/usr/bin/js140', '--version'], env={**os.environ, 'LD_LIBRARY_PATH': '/stage/usr/lib'}, text=True).strip()
    assert version == 'JavaScript-C140.17.0'
    stage_before = {str(p.relative_to('/stage')): digest(p) for p in Path('/stage').rglob('*') if p.is_file() and not p.is_symlink()}
    out = root / 'security-tests-1'
    out.mkdir()
    baseline = json.loads(sys.argv[2])
    assert len(baseline) == 103 and all(x['exit'] == 3 for x in baseline.values())
    before = {}
    for path in (root / 'compile').rglob('*'):
        if not path.is_file() or path.is_symlink():
            continue
        with path.open('rb') as stream:
            elf = stream.read(4) == b'\x7fELF'
        if elf:
            before[str(path.relative_to(root))] = digest(path)
    (out / 'compiled-before.json').write_text(json.dumps(before, sort_keys=True) + '\n')
    (out / 'baseline-failures.json').write_text(json.dumps(baseline, indent=2) + '\n')
    probe = out / 'consumer.cpp'
    probe.write_text(sys.argv[1])
    encoding = []
    for path in sorted(Path('/src/project').rglob('*.msg')):
        name = str(path.relative_to('/src/project'))
        if name in ['dom/base/domerr.msg', 'js/xpconnect/src/xpc.msg']:
            continue  # Exact original checker's explicitly non-JSErrorFormatString exclusions.
        data = path.read_bytes()
        try:
            data.decode('ascii')
            valid = True
        except UnicodeDecodeError:
            valid = False
        encoding.append({'path': name, 'ascii': valid, 'sha256': hashlib.sha256(data).hexdigest()})
    (out / 'encoding-property.json').write_text(json.dumps(encoding, indent=2) + '\n')
    env = {**os.environ, 'PYTHONDONTWRITEBYTECODE': '1', 'MOZ_UPLOAD_DIR': str(out)}
    shell = '/build/compile/dist/bin/js'
    commands = [
        ('api', ['/build/compile/dist/bin/jsapi-tests']),
        ('main', ['python3', '-B', '/src/project/js/src/tests/jstests.py',
                  '--no-progress', '--format=automation', '--timeout=300',
                  '--wpt=disabled', '-j', '2', shell]),
        ('jit', ['python3', '-B', '/src/project/js/src/jit-test/jit_test.py',
                 '--no-slow', '--no-progress', '--format=automation',
                 '--jitflags=all', '-j', '1', '--write-failures',
                 str(out / 'jit-failures.txt'), shell]),
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
        records.append({'name': name, 'exit': result.returncode, 'seconds': time.time() - started,
                        'stdout_sha256': digest(out / (name + '.stdout')),
                        'stderr_sha256': digest(out / (name + '.stderr'))})
        (out / 'progress.json').write_text(json.dumps(records, indent=2) + '\n')
    text = (out / 'main.stdout').read_text()
    counts = collections.Counter(line.split(' | ')[0] for line in text.splitlines() if line.startswith('TEST-'))
    failures = failure_details(text)
    novel = {name: value for name, value in failures.items() if baseline.get(name) != value}
    suite_ended = False
    with (out / 'main_raw.log').open() as stream:
        for line in stream:
            if json.loads(line).get('action') == 'suite_end':
                suite_ended = True
    changed = [name for name, expected in before.items() if digest(root / name) != expected]
    proof = {'scope': 'Original critical suites for security candidate, real staged C++ consumer and strict ASCII property; retained main failures are NOT passes or full Intl qualification',
             'version': version,
             'drivers': records, 'main_automation_counts': counts,
             'main_failures': failures, 'novel_failure_diagnostics': novel,
             'baseline_failures_no_longer_present': sorted(baseline.keys() - failures.keys()),
             'main_suite_end_observed': suite_ended,
             'compiled_artifacts': len(before), 'changed_artifacts': changed,
             'changed_stage_files': [name for name, expected in stage_before.items() if digest(Path('/stage') / name) != expected],
             'strict_ascii_property': {'files': len(encoding), 'failed': [x for x in encoding if not x['ascii']],
                                       'original_vcs_checker': 'Known source-archive metadata failure retained; not replayed or claimed passed'}}
    (out / 'result.json').write_text(json.dumps(proof, indent=2) + '\n')
    assert not proof['changed_stage_files']
    assert not changed and encoding and all(x['ascii'] for x in encoding)
    assert not novel and suite_ended and sum(counts.values()) == 52627
    assert counts['TEST-KNOWN-FAIL'] == 1932
    assert len(failures) == counts['TEST-UNEXPECTED-FAIL']
    assert all(row.get('exit') == 0 for row in records if row['name'] != 'main')
    assert records[1]['exit'] == (1 if failures else 0)


if __name__ == '__main__':
    main()
