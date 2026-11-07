#!/usr/bin/env python3
"""H12-only native retests in a guarded writable overlay of the H09 cold disk."""
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import runpy
import signal
import subprocess
import tempfile
import time
import zlib


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    # Reuse actual root/firmware/disk-serial, C and Kmod guards before any writes.
    common = Path(os.environ['CREDENTIALS_DIRECTORY']) / 'toddy.boot-common'
    runpy.run_path(str(common))['main']()
    build = Path('/sources/glibc-2.44/build')
    original = (build / 'tests.sum').read_bytes()
    selected = []
    for line in original.decode().splitlines():
        if not line.startswith('UNSUPPORTED: '):
            continue
        name = line.split(': ', 1)[1]
        if not re.fullmatch(r'[a-z0-9_-]+/[A-Za-z0-9_.-]+', name):
            raise ValueError('Unexpected frozen test name')
        output = build / (name + '.out')
        text = output.read_text(errors='replace') if output.exists() else ''
        if any(reason in text for reason in ('CLONE_NEWUSER', 'apparmor_restrict_unprivileged_userns', 'unshare', 'ptrace')):
            selected.append(name)
    if len(selected) != 48 or len(set(selected)) != 48:
        raise ValueError('Original native namespace retest selection changed')
    selected.append('io/tst-lchmod')
    work = Path(tempfile.mkdtemp(prefix='toddy-native-regressions-', dir='/var/tmp'))
    report = {'complete': False, 'kernel': os.uname().release,
              'original_glibc_summary_sha256': hashlib.sha256(original).hexdigest(),
              'selected_glibc_tests': selected, 'results': [],
              'global_security_controls_changed': False,
              'core_binary_sha256': {name: digest(Path(name)) for name in
                  ('/usr/lib/libc.so.6', '/usr/lib/systemd/systemd')}}
    raw = {}
    print('TODDY_NATIVE_REGRESSIONS_WORKSPACE ' + str(work), flush=True)
    def save():
        temporary = work / 'progress.json.part'
        temporary.write_text(json.dumps(report, indent=2) + '\n')
        temporary.replace(work / 'progress.json')
    save()
    def run(name, argv, cwd, timeout):
        start = time.monotonic()
        with (work / (name.replace('/', '_') + '.log')).open('xb') as log:
            process = subprocess.Popen(argv, cwd=cwd, stdout=log, stderr=subprocess.STDOUT,
                env={'PATH': '/usr/bin:/usr/sbin', 'HOME': '/root', 'LC_ALL': 'en_US.UTF-8',
                     'PYTHONDONTWRITEBYTECODE': '1'}, start_new_session=True)
            timed_out = False
            try:
                process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                timed_out = True
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
        data = (work / (name.replace('/', '_') + '.log')).read_bytes()
        raw[name] = {'command_log': base64.b64encode(data).decode()}
        row = {'test': name, 'argv': argv, 'exit': process.returncode, 'timeout': timed_out,
               'seconds': time.monotonic() - start, 'log_sha256': hashlib.sha256(data).hexdigest()}
        report['results'].append(row)
        save()
        print('TODDY_NATIVE_REGRESSION_STEP ' + json.dumps(row), flush=True)
        return row
    systemd = run('systemd-test-namespace', ['/sources/systemd-261.2/build/test-namespace'], '/', 120)
    systemd['passed'] = systemd['exit'] == 0 and not systemd['timeout']
    for name in selected:
        prior = {}
        for suffix in ('.out', '.test-result'):
            p = build / (name + suffix)
            if p.is_file():
                data = p.read_bytes()
                prior[suffix] = base64.b64encode(data).decode()
                (work / (name.replace('/', '_') + suffix + '.original')).write_bytes(data)
        row = run(name, ['make', '-j2', 'test', 't=' + name], build, 120)
        raw[name]['original'] = prior
        for suffix in ('.out', '.test-result'):
            p = build / (name + suffix)
            if p.is_file():
                data = p.read_bytes(); raw[name][suffix] = base64.b64encode(data).decode()
                row[suffix + '_sha256'] = hashlib.sha256(data).hexdigest()
        result = build / (name + '.test-result')
        row['test_result'] = result.read_text().strip() if result.is_file() else None
        row['passed'] = row['exit'] == 0 and not row['timeout'] and row['test_result'] == 'PASS: ' + name
        save()
    report['complete'] = all(row['passed'] for row in report['results'])
    report['raw_evidence'] = raw
    data = json.dumps(report, sort_keys=True).encode()
    (work / 'result.json').write_bytes(data)
    encoded = base64.b64encode(zlib.compress(data, 9)).decode()
    chunks = [encoded[i:i+2048] for i in range(0, len(encoded), 2048)]
    for index, chunk in enumerate(chunks):
        print(f'TODDY_NATIVE_REGRESSIONS_DATA {index} {chunk}', flush=True)
    summary = {'complete': report['complete'], 'tests': len(report['results']),
               'passed': sum(row['passed'] for row in report['results']), 'chunks': len(chunks),
               'report_sha256': hashlib.sha256(data).hexdigest(), 'workspace': str(work)}
    print('TODDY_NATIVE_REGRESSIONS_RESULT ' + json.dumps(summary), flush=True)
    if not report['complete']:
        raise RuntimeError('Native regression failures retained; inspect exact per-test evidence')


if __name__ == '__main__':
    try:
        main()
    except BaseException as error:
        print('TODDY_NATIVE_REGRESSIONS_FAIL ' + str(error), flush=True)
        raise
