"""Read-only verification of the measured recovery-coverage witness.

This recovery profile names ADR-0083's actual completed result. It does not
accept the still-running standard suite, seal source custody or install anything.
"""
from datetime import datetime
import json
import os
from pathlib import Path
import re

from db_standard_diagnostics import COVERAGE_TYPES, digest
from db_standard_result import protected

RECOVERY = Path('/mnt/lfs/sources/recovery')
RESULT_SHA256 = '25346654d8a206d28fe1a239247a0a730a119b2ef6493299ce0a017960119edf'
INPUT_SHA256 = '042c63826149c3b1bf647152b7c2140ab0c7e730327fb36ff0491cae74df59e7'
ORIGIN_SHA256 = '336abd7ca1442e5102249da2f774b30326e06d268cd2b16b65fc81e8c333e6f9'
DRIVER_SHA256 = '9b780466c8dc3b2175fb5e85c100d47dce273f1fc04fb780edd91b25bbb9988e'
ENTRY_SHA256 = '8e7fe113e00e113c9537705df36ca46af7a6dc5955af5354b6302ffead0879f0'
SENTINEL = 'Diagnostic native coverage cases completed; full suite and package remain unaccepted'
REPORTS = {'cutest.log', 'standard.log', 'isolation-standard.json',
           'source/build-test/coverage-records.txt'}


def validate_record(record, base):
    if (record.get('fixture') != str(base) or record.get('driver_sha256') != DRIVER_SHA256
            or record.get('input_sha256') != INPUT_SHA256):
        raise ValueError('Different native coverage producer or input profile')
    if any(type(record.get(name)) is not int or record[name] != 0 for name in ('driver_exit', 'test_exit')):
        raise ValueError('Coverage witness must have actual zero process exits')
    if (record.get('inputs_unchanged') is not True or record.get('diagnostic_cases_passed') is not True
            or record.get('suite_accepted') is not False or record.get('package_accepted') is not False
            or 'error' in record or set(record.get('reports', {})) != REPORTS):
        raise ValueError('Incomplete or misrepresented native coverage witness')
    if record.get('command') != ['timeout', '--kill-after=60', '1800', 'bash',
                                 str(base / 'isolate.sh'), str(base), 'standard']:
        raise ValueError('Different coverage command or timeout profile')
    if any(type(record.get('records', {}).get(name)) is not int or record['records'][name] <= 0
           for name in COVERAGE_TYPES):
        raise ValueError('At least one required native record type was not observed')
    started, finished = (datetime.fromisoformat(record[name]) for name in ('started', 'finished'))
    if started.tzinfo is None or finished.tzinfo is None or finished < started:
        raise ValueError('Incomplete coverage execution timestamps')


def verify(base, standard):
    base, standard = Path(base), Path(standard)
    for path, prefix in ((base, 'db-standard-coverage-'), (standard, 'db-standard-')):
        if (path.resolve() != path or path.parent != RECOVERY
                or not re.fullmatch(re.escape(prefix) + r'[A-Za-z0-9_-]+', path.name)):
            raise ValueError('Coverage witness and standard inputs must be designated physical fixtures')
        protected(path, directory=True)
    if (base / 'running.json').exists():
        raise ValueError('Coverage process is unfinished')
    for name in ('driver.exit', 'test.exit'):
        protected(base / name)
        if (base / name).read_text().strip() != '0':
            raise ValueError('Coverage process did not finish successfully')
    for name, expected in (('result.json', RESULT_SHA256), ('inputs.json', INPUT_SHA256)):
        protected(base / name, private=True)
        if digest(base / name) != expected:
            raise ValueError('The measured coverage result or inputs changed: ' + name)
    protected(standard / 'inputs.json', private=True)
    if digest(standard / 'inputs.json') != ORIGIN_SHA256:
        raise ValueError('Coverage witness belongs to a different standard execution')
    record = json.loads((base / 'result.json').read_text())
    inputs = json.loads((base / 'inputs.json').read_text())
    origin = json.loads((standard / 'inputs.json').read_text())
    validate_record(record, base)
    pid = record.get('driver_pid')
    if type(pid) is not int or pid <= 0 or (base / 'driver.pid').read_text().strip() != str(pid):
        raise ValueError('Missing actual coverage process identity')
    cmd = Path('/proc', str(pid), 'cmdline')
    if cmd.exists() and str(base / 'driver.py').encode() in cmd.read_bytes().split(b'\0'):
        raise ValueError('Coverage producer is still live')
    if (inputs.get('origin_input_sha256') != ORIGIN_SHA256
            or inputs.get('diagnostic_entry_only_change') is not True
            or inputs.get('frozen_test_bodies_unchanged') is not True
            or set(inputs['source_files']) != set(origin['source_files'])):
        raise ValueError('Incomplete native source relationship')
    entry = 'build-test/standard-regression.tcl'
    if inputs['source_files'].get(entry) != {'sha256': ENTRY_SHA256}:
        raise ValueError('Coverage entry differs from the exercised diagnostic')
    source = base / 'source'
    if source.resolve() != source or not source.is_dir():
        raise ValueError('Redirected coverage source')
    for name, expected in inputs['source_files'].items():
        if name != entry and expected != origin['source_files'][name]:
            raise ValueError('Coverage and full-suite compiled/source inputs differ: ' + name)
        path = source / name
        if not path.resolve().is_relative_to(source) or not path.is_file():
            raise ValueError('Coverage input is missing or redirected: ' + name)
        actual = {'sha256': digest(path)}
        if path.is_symlink():
            actual['symlink'] = os.readlink(path)
        if actual != expected:
            raise ValueError('Coverage input changed: ' + name)
    for name, expected in inputs['harness_sha256'].items():
        protected(base / name)
        if digest(base / name) != expected:
            raise ValueError('Coverage execution harness changed: ' + name)
    for name, expected in record['reports'].items():
        path = base / name
        if not path.resolve().is_relative_to(base) or digest(path) != expected:
            raise ValueError('Native coverage evidence changed: ' + name)
    outer = json.loads((base / 'outer-namespaces.json').read_text())
    isolation = json.loads((base / 'isolation-standard.json').read_text())
    if (isolation.get('mode') != 'standard' or isolation.get('shm_filesystem') != 'tmpfs'
            or any(isolation.get(name) is not True for name in
                   ('private_pid_namespace', 'canonical_source_is_private', 'tmp_var_tmp_shm_private'))
            or set(outer) != {'pid', 'ipc', 'net', 'mnt'}
            or set(isolation.get('namespaces', {})) != set(outer)):
        raise ValueError('Coverage environment was not the measured isolated target view')
    for name, value in isolation['namespaces'].items():
        if (not re.fullmatch(re.escape(name) + r':\[\d+\]', value)
                or not re.fullmatch(re.escape(name) + r':\[\d+\]', outer[name]) or value == outer[name]):
            raise ValueError('Coverage environment shared a required namespace')
    output = (base / 'standard.log').read_text().splitlines()
    if (not output or output[-1] != SENTINEL or output.count(SENTINEL) != 1
            or any(line.startswith('FAIL') for line in output)):
        raise ValueError('Missing complete coverage sentinel or real native failure')
    counts = {}
    for line in (source / 'build-test/coverage-records.txt').read_text().splitlines():
        match = re.fullmatch(r'(__[A-Za-z0-9_]+) ([1-9][0-9]*)', line)
        if not match or match[1] in counts:
            raise ValueError('Malformed or duplicate actual coverage record')
        counts[match[1]] = int(match[2])
    if counts != record['records']:
        raise ValueError('Native log type observations differ from the recorded result')
    return {'coverage_witness_verified': True, 'suite_accepted': False,
            'package_accepted': False, 'custody_sealed': False,
            'fixture': str(base), 'standard_fixture': str(standard),
            'result_sha256': RESULT_SHA256, 'input_sha256': INPUT_SHA256,
            'standard_input_sha256': ORIGIN_SHA256, 'verified_source_files': len(inputs['source_files']),
            'target_type_observations': {name: counts[name] for name in COVERAGE_TYPES},
            'reports': record['reports']}
