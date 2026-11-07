#!/usr/bin/env python3
"""Read-only verification of the complete isolated BDB result, never installation."""
import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess

ROOT = Path(__file__).resolve().parents[2]
RECOVERY = Path('/mnt/lfs/sources/recovery')
DRIVER_SHA256 = 'e606c595c43fb024f44a0af2610990d04b0a0f3cc7d0d85488ddd2cbebb5b981'
ISOLATION_SHA256 = 'cb90e3143b3ae49dbf9f5274cada9ee7b8f9ecc79ba9ae8034203efe80d1c103'
PROBE_SHA256 = '1db63b29fee0fb87b7efb0770a78797e13eafbccfeedcbfc9bdcf90b82fb7185'
ENTRY_SHA256 = 'e535fb4c61c812b21b9e66596a90d221daba90fea8169a4182cd47c75747ef91'
SEED_SHA256 = '75d8c0e77db2c0b42af7de2ff813e908ee4f2d5cc470dcb62bb5082013937e63'
CUTEST_SHA256 = '51763da1955dcca28f53b8bc863cec7f834179ddd994beda4b55f1cc4ab025d2'
HELPER_SHA256 = '827f84ea724f12d6c91c5b215026e0e771a896423b67654690bd85ffaf08735c'
HELPER_BINARY_SHA256 = '4649eda06c59a36dff11bf0a4002ef2721e4b69afebd4a79cfefc03cf0afab2d'
REPORTS = {'cutest.log', 'standard.log', 'ALL.OUT', 'isolation-standard.json'}
SENTINEL = 'Complete native DB standard regression suite accepted'


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def protected(path, private=False, directory=False):
    info = path.lstat()
    kind = stat.S_ISDIR if directory else stat.S_ISREG
    if (not kind(info.st_mode) or info.st_uid != 0 or
            info.st_mode & (0o077 if private else 0o022)):
        raise ValueError('Evidence is redirected, writable or not root protected: ' + str(path))


def validate_record(record, inputs, base):
    if any(type(record.get(key)) is not int or record[key] != 0
           for key in ('driver_exit', 'test_exit')):
        raise ValueError('Both actual process exits must be zero')
    for key in ('standard_suite_passed', 'source_protected_from_test_user', 'test_inputs_unchanged'):
        if record.get(key) is not True:
            raise ValueError('Incomplete result: ' + key)
    if record.get('package_accepted') is not False or 'error' in record:
        raise ValueError('Unexpected package claim or diagnosed error')
    validate_execution(record, inputs, base)


def validate_execution(record, inputs, base):
    """Validate the execution profile independently of its actual success/failure."""
    if record.get('driver_sha256') != DRIVER_SHA256:
        raise ValueError('Unreviewed result producer')
    if record.get('fixture') != str(base) or inputs.get('fixture') != str(base):
        raise ValueError('Result belongs to a different fixture')
    command = ['timeout', '--kill-after=60', '172800', 'bash',
               str(base / 'isolate.sh'), str(base), 'standard']
    if record.get('command') != command:
        raise ValueError('The complete standard command was not captured')
    if set(record.get('reports', {})) != REPORTS:
        raise ValueError('Missing complete native reports')
    if record['reports']['cutest.log'] != CUTEST_SHA256:
        raise ValueError('C suite differs from the exercised frozen profile')
    if (inputs.get('native_build_seed_sha256') != SEED_SHA256 or
            inputs.get('verified_seed_files') != 460 or inputs.get('verified_tcl_files') != 483):
        raise ValueError('Unexpected native checkpoint or Tcl input profile')
    if (inputs.get('isolation_script_sha256') != ISOLATION_SHA256 or
            inputs.get('isolation_probe_sha256') != PROBE_SHA256):
        raise ValueError('Input manifest names a different test environment')
    if (record.get('verified_input_files') != len(inputs.get('source_files', {})) or
            record['verified_input_files'] < 943):
        raise ValueError('Incomplete input manifest')
    started, finished = (datetime.fromisoformat(record[key]) for key in ('started', 'finished'))
    if started.tzinfo is None or finished.tzinfo is None or finished < started:
        raise ValueError('Incomplete execution timestamps')


def validate_summary(report, output):
    lines, summary = report.splitlines(), output.splitlines()
    if (lines.count('Regression Tests Succeeded') != 1 or len(lines) < 2 or
            lines[-2] != 'Regression Tests Succeeded' or
            not re.fullmatch(r'Test suite run completed at: \d{2}:\d{2} \d{2}/\d{2}/(?:\d{2}|\d{4})', lines[-1])):
        raise ValueError('Missing or truncated complete upstream summary')
    if any(line.startswith('FAIL') or line == 'Regression Tests Failed' for line in lines):
        raise ValueError('Native standard report contains failure')
    if (not summary or summary[-1] != SENTINEL or summary.count(SENTINEL) != 1 or
            any(line.startswith('UNEXPECTED OUTPUT:') for line in summary)):
        raise ValueError('Strict standard acceptance missing or unexpected output present')


def open_terminal(base, expected_exit=0):
    base = Path(base)
    if (base.resolve() != base or base.parent != RECOVERY or
            not re.fullmatch(r'db-standard-[A-Za-z0-9_-]+', base.name)):
        raise ValueError('Unsafe result fixture')
    protected(base, directory=True)
    if (base / 'running.json').exists() or not (base / 'driver.exit').is_file():
        raise ValueError('The isolated standard run is still unfinished')
    for name in ('driver.exit', 'test.exit'):
        protected(base / name)
        if (base / name).read_text().strip() != str(expected_exit):
            raise ValueError('The isolated standard run has a different terminal exit: ' + name)
    for name in ('result.json', 'inputs.json'):
        protected(base / name, private=True)
    record = json.loads((base / 'result.json').read_text())
    inputs = json.loads((base / 'inputs.json').read_text())
    if digest(base / 'inputs.json') != record.get('input_manifest_sha256'):
        raise ValueError('Input manifest changed after execution')
    return base, record, inputs


def verify_execution_evidence(base, record, inputs, private_source=True):
    """Verify bytes, provenance and isolation; never assert suite acceptance."""
    validate_execution(record, inputs, base)
    pid = record.get('driver_pid')
    if type(pid) is not int or pid <= 0:
        raise ValueError('Missing actual driver PID')
    command = Path('/proc', str(pid), 'cmdline')
    if command.exists() and str(base / 'driver.py').encode() in command.read_bytes().split(b'\0'):
        raise ValueError('Result-producing driver is still live')
    source = base / 'source'
    if private_source:
        protected(source, private=True, directory=True)
    elif source.resolve() != source or not source.is_dir() or source.stat().st_mode & 0o022:
        raise ValueError('Failed-run source is redirected or writable by other users')
    for name, expected in [('driver.py', DRIVER_SHA256), ('isolate.sh', ISOLATION_SHA256),
                           ('isolation-probe.py', PROBE_SHA256)]:
        protected(base / name)
        if digest(base / name) != expected:
            raise ValueError('Reviewed execution input changed: ' + name)
    for relative, expected in inputs['source_files'].items():
        path = source / relative
        if not path.resolve().is_relative_to(source) or not path.is_file():
            raise ValueError('Missing or redirected tested source: ' + relative)
        actual = {'sha256': digest(path)}
        if path.is_symlink():
            actual['symlink'] = os.readlink(path)
        if actual != expected:
            raise ValueError('Tested source changed: ' + relative)
    for name, expected in [('standard-regression.tcl', ENTRY_SHA256),
                           ('db_repsite.c', HELPER_SHA256), ('db_repsite', HELPER_BINARY_SHA256)]:
        if (inputs['source_files'].get('build-test/' + name) != {'sha256': expected} or
                digest(source / 'build-test' / name) != expected):
            raise ValueError('Test entry or helper changed: ' + name)
    evidence = base / 'result-evidence'
    protected(evidence, private=True, directory=True)
    for name, expected in record['reports'].items():
        protected(evidence / name, private=True)
        if digest(evidence / name) != expected:
            raise ValueError('Preserved report changed: ' + name)
    protected(base / 'outer-namespaces.json')
    if digest(base / 'outer-namespaces.json') != inputs['outer_namespace_file_sha256']:
        raise ValueError('Outer namespace reference changed')
    outer = json.loads((base / 'outer-namespaces.json').read_text())
    isolation = json.loads((evidence / 'isolation-standard.json').read_text())
    for key in ('private_pid_namespace', 'canonical_source_is_private', 'tmp_var_tmp_shm_private'):
        if isolation.get(key) is not True:
            raise ValueError('Isolation was not demonstrated: ' + key)
    if isolation.get('mode') != 'standard' or isolation.get('shm_filesystem') != 'tmpfs':
        raise ValueError('Wrong standard test environment')
    if set(outer) != {'pid', 'ipc', 'net', 'mnt'} or set(isolation.get('namespaces', {})) != set(outer):
        raise ValueError('Incomplete namespace evidence')
    if any(not isinstance(value, str) or not re.fullmatch(name + r':\[\d+\]', value)
           for group in (outer, isolation['namespaces']) for name, value in group.items()):
        raise ValueError('Malformed namespace identity')
    if any(isolation['namespaces'][name] == outer[name] for name in outer):
        raise ValueError('A required namespace was shared')
    seed_path = Path('/var/log/toddy/build/h07-berkeley-db.recovery-seed.json')
    protected(seed_path, private=True)
    if digest(seed_path) != SEED_SHA256:
        raise ValueError('Native build checkpoint changed')
    seed = json.loads(seed_path.read_text())
    for relative, expected in seed['files'].items():
        if (inputs['source_files'].get(relative, {}).get('sha256') != expected or
                digest(source / relative) != expected):
            raise ValueError('Native compiled checkpoint differs: ' + relative)
    from verify_db_tcl_tests import verify
    for relative, expected in verify(ROOT, Path('/mnt/lfs/sources'), source).items():
        if inputs['source_files'].get(relative) != {'sha256': expected}:
            raise ValueError('Frozen Tcl input was not in the execution manifest: ' + relative)
    return {'execution_evidence_verified': True, 'package_accepted': False,
            'fixture': str(base), 'source': str(source),
            'result_sha256': digest(base / 'result.json'),
            'input_manifest_sha256': digest(base / 'inputs.json'),
            'report_sha256': record['reports'], 'verified_input_files': len(inputs['source_files'])}


def verify_completed(base):
    base, record, inputs = open_terminal(base)
    validate_record(record, inputs, base)
    result = verify_execution_evidence(base, record, inputs)
    evidence = base / 'result-evidence'
    validate_summary((evidence / 'ALL.OUT').read_text(), (evidence / 'standard.log').read_text())
    # Preserve the existing strict success interface only after every old gate.
    result.pop('execution_evidence_verified')
    return dict(result, standard_suite_verified=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('fixture', type=Path)
    args = parser.parse_args()
    subprocess.run(['bash', '-c',
                    'source /opt/toddy-build/scripts/build/target.sh; guard_target'], check=True)
    if os.geteuid() != 0:
        raise SystemExit('Disposable guest root required for protected evidence')
    print(json.dumps(verify_completed(args.fixture), indent=2))


if __name__ == '__main__':
    main()
