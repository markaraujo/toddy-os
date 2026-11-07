#!/usr/bin/env python3
"""Capture one isolated complete standard suite; never install or accept a package."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def write(path, value):
    temporary = path.with_suffix('.part')
    with temporary.open('w') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    temporary.chmod(0o600)
    temporary.replace(path)


def verify(base, inputs):
    source = base / 'source'
    for relative, expected in inputs['source_files'].items():
        path = source / relative
        if not path.resolve().is_relative_to(source) or not path.is_file():
            raise ValueError('Missing or redirected test input: ' + relative)
        actual = {'sha256': digest(path)}
        if path.is_symlink():
            actual['symlink'] = os.readlink(path)
        if actual != expected:
            raise ValueError('Test input changed: ' + relative)
    if digest(base / 'isolate.sh') != inputs['isolation_script_sha256']:
        raise ValueError('Isolation command changed')
    if digest(base / 'isolation-probe.py') != inputs['isolation_probe_sha256']:
        raise ValueError('Isolation probe changed')
    if digest(base / 'outer-namespaces.json') != inputs['outer_namespace_file_sha256']:
        raise ValueError('Outer namespace reference changed')


def main():
    if os.geteuid() != 0 or len(sys.argv) != 3:
        raise SystemExit('Requires disposable guest root, private fixture and manifest digest')
    subprocess.run(['bash', '-c',
                    'source /opt/toddy-build/scripts/build/target.sh; guard_target'], check=True)
    base = Path(sys.argv[1])
    if (base.resolve() != base or base.parent != Path('/mnt/lfs/sources/recovery') or
            not base.name.startswith('db-standard-') or base.stat().st_uid != 0 or
            base.stat().st_mode & 0o022):
        raise SystemExit('Unsafe private fixture')
    for name in ('driver.pid', 'driver.exit', 'result.json', 'running.json'):
        if (base / name).exists():
            raise SystemExit('Preserve previous run: ' + name)
    record = {'driver_pid': os.getpid(), 'started': datetime.now(timezone.utc).isoformat(),
              'fixture': str(base), 'input_manifest_sha256': sys.argv[2],
              'driver_sha256': digest(Path(__file__)), 'package_accepted': False}
    write(base / 'running.json', record)
    (base / 'driver.pid').write_text(str(os.getpid()) + '\n')
    status = 1
    try:
        manifest = base / 'inputs.json'
        if manifest.is_symlink() or manifest.stat().st_uid != 0 or manifest.stat().st_mode & 0o077:
            raise ValueError('Input manifest must be root protected')
        if digest(manifest) != sys.argv[2]:
            raise ValueError('Input manifest digest changed')
        inputs = json.loads(manifest.read_text())
        verify(base, inputs)
        record['verified_input_files'] = len(inputs['source_files'])
        record['command'] = ['timeout', '--kill-after=60', '172800', 'bash',
                             str(base / 'isolate.sh'), str(base), 'standard']
        process = subprocess.Popen(record['command'])
        record['test_process_pid'] = process.pid
        write(base / 'running.json', record)
        record['test_exit'] = process.wait()
        (base / 'test.exit').write_text(str(record['test_exit']) + '\n')
        verify(base, inputs)
        record['test_inputs_unchanged'] = True
        reports = base / 'result-evidence'
        reports.mkdir(mode=0o700)
        record['reports'] = {}
        for original in (base / 'cutest.log', base / 'standard.log',
                         base / 'source/build-test/ALL.OUT', base / 'isolation-standard.json'):
            if original.is_file():
                destination = reports / original.name
                shutil.copyfile(original, destination)
                destination.chmod(0o600)
                record['reports'][original.name] = digest(destination)
        if record['test_exit'] != 0:
            raise ValueError('Complete native suite failed with exit ' + str(record['test_exit']))
        lines = (reports / 'ALL.OUT').read_text(errors='replace').splitlines()
        if ('Regression Tests Succeeded' not in lines or
                any(line.startswith('FAIL') or line == 'Regression Tests Failed' for line in lines)):
            raise ValueError('Complete native summary is missing or failed')
        summary = (reports / 'standard.log').read_text(errors='replace').splitlines()
        if 'Complete native DB standard regression suite accepted' not in summary:
            raise ValueError('Strict Tcl acceptance sentinel missing')
        source = base / 'source'
        os.chown(source, 0, 0)
        source.chmod(0o700)
        record['standard_suite_passed'] = True
        record['source_protected_from_test_user'] = True
        status = 0
    except Exception as error:
        record['error'] = str(error)
        print('Isolated standard-suite result requires diagnosis:', error, flush=True)
    finally:
        record['finished'] = datetime.now(timezone.utc).isoformat()
        record['driver_exit'] = status
        write(base / 'result.json', record)
        (base / 'driver.exit').write_text(str(status) + '\n')
        (base / 'running.json').unlink()
    raise SystemExit(status)


if __name__ == '__main__':
    main()
