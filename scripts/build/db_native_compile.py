#!/usr/bin/env python3
"""Build fresh native DB test inputs privately; never run the standard suite."""
import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tarfile
import traceback

from apply_db_test_fixture import FIXTURES, apply_fixture
from db_standard_prepare import inventory, prepare
from locked_inputs import locked_source
from source_filter import source_filter
from verify_db_tcl_tests import verify as verify_tcl

ROOT = Path(__file__).resolve().parents[2]
TARGET = Path('/mnt/lfs')
NAMES = ['db5.3_5.3.28+dfsg2.orig.tar.xz', 'db5.3_5.3.28+dfsg2-12.debian.tar.xz'] + [n for n, _ in FIXTURES]


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def save(path, data):
    with path.open('x') as stream:
        os.fchmod(stream.fileno(), 0o600)
        json.dump(data, stream, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


def validate(base):
    if (os.geteuid() != 0 or base.resolve() != base or
            base.parent != TARGET / 'sources/recovery' or not base.name.startswith('db-native-') or
            base.stat().st_uid != 0 or base.stat().st_mode & 0o077 or ROOT != base / 'code'):
        raise ValueError('Private disposable native build generation required')
    subprocess.run(['bash', '-c', 'source /opt/toddy-build/scripts/build/target.sh; guard_target'], check=True)
    spec = json.loads((base / 'inputs.json').read_text())
    for name, expected in spec['code_files'].items():
        if (ROOT / name).resolve() != ROOT / name or digest(ROOT / name) != expected:
            raise ValueError('Private compile input changed: ' + name)
    for name in NAMES:
        if digest(base / 'archives' / name) != locked_source(ROOT, name)['sha256']:
            raise ValueError('Frozen archive/patch differs: ' + name)
    if digest(TARGET / 'var/lib/dpkg/status') != spec['native_status_sha256']:
        raise ValueError('Installed native package database changed')
    return spec


def extract(base):
    source = base / 'db-5.3.28'
    if source.exists():
        raise ValueError('Preserve previous extracted source')
    with tarfile.open(base / 'archives' / NAMES[0]) as archive:
        checked = source_filter(NAMES[0])
        for member in archive.getmembers():
            if Path(member.name).parts[0] != 'db-5.3.28':
                raise ValueError('Unexpected archive root')
            checked(member, base)
        archive.extractall(base, filter=checked)
    with tarfile.open(base / 'archives' / NAMES[1]) as archive:
        members = [m for m in archive.getmembers() if m.name in (
            'debian', 'debian/patches', 'debian/copyright', 'debian/changelog') or
            m.name.startswith('debian/patches/')]
        if not members or any(not (m.isfile() or m.isdir()) for m in members):
            raise ValueError('Unexpected maintained patch archive')
        for member in members:
            tarfile.data_filter(member, source)
        archive.extractall(source, members=members, filter='data')
    # apply_fixture expects the source beside the patch. Private links leave
    # the globally deployed patch set and running source unchanged.
    for name, expected_file in FIXTURES:
        (base / name).symlink_to(base / 'archives' / name)
        apply_fixture(ROOT, base, name, expected_file)


def run(base):
    spec = validate(base)
    lock = (base / 'lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    if (base / 'result.json').exists():
        raise ValueError('Complete build exists; collect instead of recompiling')
    attempts = base / 'attempts'
    attempts.mkdir(exist_ok=True)
    # A dead supervisor does not prove its compiler stopped.
    for record in attempts.glob('*/*.pid.json'):
        if record.with_name(record.name.replace('.pid.json', '.exit.json')).exists():
            continue
        pid = json.loads(record.read_text())['pid']
        proc = Path('/proc') / str(pid)
        if proc.exists() and (proc / 'stat').read_text().rsplit(')', 1)[1].split()[0] != 'Z':
            raise ValueError('Prior stage process still exists: ' + str(pid))
    attempt = attempts / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    attempt.mkdir(mode=0o700)
    inputs_sha = digest(base / 'inputs.json')
    save(attempt / 'running.json', {'pid': os.getpid(), 'inputs_sha256': inputs_sha})
    completed = base / 'completed'
    completed.mkdir(exist_ok=True)
    result = {'native_test_build_complete': False, 'standard_suite_started': False,
              'package_accepted': False, 'installed': False, 'inputs_sha256': inputs_sha}
    exit_code = 1

    def stage(name, command, timeout=1800):
        marker = completed / (name + '.json')
        if marker.exists():
            old = json.loads(marker.read_text())
            if (old['command'] != command or old['exit'] != 0 or old['inputs_sha256'] != inputs_sha or
                    digest(base / old['log']) != old['log_sha256']):
                raise ValueError('Completed stage changed: ' + name)
            return
        save(attempt / (name + '.intent.json'), {'command': command, 'timeout': timeout})
        with (attempt / (name + '.log')).open('x') as log:
            child = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=log,
                                     stderr=subprocess.STDOUT, start_new_session=True)
            save(attempt / (name + '.pid.json'), {'pid': child.pid})
            timed_out = False
            try:
                child.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                timed_out = True
                os.killpg(child.pid, signal.SIGKILL)
                child.wait()
            log.flush()
            os.fsync(log.fileno())
        evidence = {'command': command, 'exit': child.returncode, 'timed_out': timed_out,
                    'inputs_sha256': inputs_sha, 'log': str(Path(log.name).relative_to(base)),
                    'log_sha256': digest(Path(log.name))}
        save(attempt / (name + '.exit.json'), evidence)
        if child.returncode or timed_out:
            raise ValueError('Private native DB stage failed: ' + name)
        save(marker, evidence)

    try:
        stage('source', ['python3', '-B', str(Path(__file__)), str(base), '--extract'])
        for name in ('prepare', 'configure', 'build', 'helper'):
            stage(name, ['bash', str(ROOT / 'scripts/build/h07/berkeley-db-private-build.sh'), str(base), name])
        source = base / 'db-5.3.28'
        tcl = verify_tcl(ROOT, base / 'archives', source)
        files = inventory(source)
        validate(base)
        provenance = {'native_test_build_complete': True, 'standard_suite_started': False,
                      'package_accepted': False, 'installed': False, 'inputs_sha256': inputs_sha,
                      'source': str(source), 'verified_tcl_files': len(tcl), 'source_inputs': files,
                      'source_sha256': {name: locked_source(ROOT, name)['sha256'] for name in NAMES},
                      'stage_evidence': {p.name: digest(p) for p in sorted(completed.glob('*.json'))},
                      'cutest_log_sha256': digest(base / 'evidence/cutest.log'),
                      'native_status_sha256': spec['native_status_sha256']}
        receipt = base / 'native-build.json'
        if receipt.exists():
            if json.loads(receipt.read_text()) != provenance:
                raise ValueError('Prior native build receipt changed')
        else:
            save(receipt, provenance)
        # The standard source view is prepared, but run_std is never started.
        preparation = prepare(source, root=ROOT, sources=base / 'archives')
        if inventory(source) != files:
            raise ValueError('Native build changed while preparing the test view')
        result.update(native_test_build_complete=True, native_build_sha256=digest(receipt),
                      preparation=preparation, native_status_unchanged=True)
        validate(base)
        save(base / 'result.json', result)
        exit_code = 0
    except BaseException as error:
        save(attempt / 'error.json', {'error': str(error)})
        traceback.print_exc()
    finally:
        save(attempt / 'driver.exit.json', {'exit': exit_code})
    return exit_code


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('fixture', type=Path)
    parser.add_argument('--extract', action='store_true')
    args = parser.parse_args()
    if args.extract:
        validate(args.fixture)
        extract(args.fixture)
        return 0
    return run(args.fixture)


if __name__ == '__main__':
    sys.exit(main())
