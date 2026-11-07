#!/usr/bin/env python3
"""Verify fresh native DB compilation provenance without historical binary pins.

This proves compilation/preparation only. It never accepts a standard suite,
production package or installed operating system.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess

from db_standard_prepare import inventory
from db_standard_result import digest, protected
from locked_inputs import locked_source
from verify_db_tcl_tests import verify as verify_tcl

ROOT = Path(__file__).resolve().parents[2]
STAGES = ('source', 'prepare', 'configure', 'build', 'helper')
REQUIRED_CODE = {
    'scripts/build/' + name for name in (
        'db_native_compile.py', 'db_standard_prepare.py', 'verify_db_tcl_tests.py',
        'apply_db_test_fixture.py', 'locked_inputs.py', 'source_filter.py', 'target.sh', 'h06/common.sh')}
REQUIRED_CODE |= {'scripts/build/h07/' + name for name in (
    'berkeley-db-inner.sh', 'berkeley-db-private-build.sh', 'berkeley-db-test-helper.sh',
    'db_repsite.c', 'berkeley-db-isolated-tests.sh', 'berkeley-db-isolation-probe.py',
    'berkeley-db-standard-regression.tcl', 'berkeley-db-isolated-driver.py')}
REQUIRED_CODE |= {'config/' + name for name in (
    'sources.lock.json', 'security-overlay.lock.json', 'supplemental-sources.lock.json')}


def record(path):
    protected(path, private=True)
    return json.loads(path.read_text())


def verify(base, *, reviewed_root=ROOT):
    if (os.geteuid() != 0 or base.resolve() != base or
            base.parent != Path('/mnt/lfs/sources/recovery') or not base.name.startswith('db-native-')):
        raise ValueError('Designated physical native build required')
    protected(base, private=True, directory=True)
    spec = record(base / 'inputs.json')
    provenance = record(base / 'native-build.json')
    result = record(base / 'result.json')
    pid_path = base / 'driver.pid'
    protected(pid_path)
    pid = int(pid_path.read_text())
    proc = Path('/proc') / str(pid)
    if proc.exists() and (proc / 'stat').read_text().rsplit(')', 1)[1].split()[0] != 'Z':
        raise ValueError('Native build producer is still live')
    attempts = sorted((base / 'attempts').glob('*'))
    terminal = record(attempts[-1] / 'driver.exit.json') if attempts else {}
    if type(terminal.get('exit')) is not int or terminal['exit'] != 0:
        raise ValueError('Actual terminal native build exit missing or nonzero')
    for value in (provenance, result):
        if (value.get('native_test_build_complete') is not True or
                any(value.get(key) is not False for key in ('standard_suite_started', 'package_accepted', 'installed')) or
                value.get('inputs_sha256') != digest(base / 'inputs.json')):
            raise ValueError('Incomplete or misleading native build receipt')
    if result.get('native_build_sha256') != digest(base / 'native-build.json'):
        raise ValueError('Native compilation receipt changed')
    if set(spec['code_files']) != REQUIRED_CODE:
        raise ValueError('Native compile code inventory incomplete')
    for name, expected in spec['code_files'].items():
        if (base / 'code' / name).resolve() != base / 'code' / name:
            raise ValueError('Redirected private build recipe')
        protected(base / 'code' / name)
        if digest(base / 'code' / name) != expected or digest(reviewed_root / name) != expected:
            raise ValueError('Executed recipe differs from reviewed code: ' + name)
    if set(provenance['stage_evidence']) != {name + '.json' for name in STAGES}:
        raise ValueError('Missing native stage evidence')
    for name in STAGES:
        marker = base / 'completed' / (name + '.json')
        stage = record(marker)
        if digest(marker) != provenance['stage_evidence'][marker.name]:
            raise ValueError('Native stage receipt changed')
        command = (['python3', '-B', str(base / 'code/scripts/build/db_native_compile.py'), str(base), '--extract']
                   if name == 'source' else ['bash', str(base / 'code/scripts/build/h07/berkeley-db-private-build.sh'), str(base), name])
        if (stage.get('command') != command or type(stage.get('exit')) is not int or stage['exit'] != 0 or
                stage.get('timed_out') is not False or stage.get('inputs_sha256') != digest(base / 'inputs.json')):
            raise ValueError('Unexpected native stage outcome or invocation: ' + name)
        log = base / stage['log']
        if log.resolve() != log or not log.is_relative_to(base / 'attempts'):
            raise ValueError('Redirected native stage log')
        protected(log)
        if record(log.with_suffix('.exit.json')) != stage:
            raise ValueError('Actual stage exit differs from completion marker')
        if digest(log) != stage['log_sha256']:
            raise ValueError('Native stage log changed: ' + name)
    names = {'db5.3_5.3.28+dfsg2.orig.tar.xz', 'db5.3_5.3.28+dfsg2-12.debian.tar.xz',
             'db-5.3.28-test142-environment-1.patch', 'db-5.3.28-repmgr007-async-diagnostic-1.patch'}
    if set(provenance['source_sha256']) != names:
        raise ValueError('Incomplete frozen source inventory')
    for name in names:
        expected = locked_source(reviewed_root, name)['sha256']
        if provenance['source_sha256'][name] != expected or digest(base / 'archives' / name) != expected:
            raise ValueError('Frozen build source changed')
    protected(base / 'build-context-status', private=True)
    if (provenance['native_status_sha256'] != spec['native_status_sha256'] or
            digest(base / 'build-context-status') != spec['native_status_sha256'] or
            result.get('native_status_unchanged') is not True):
        raise ValueError('Captured native package context differs from actual build receipt')
    source = base / 'db-5.3.28'
    if provenance['source'] != str(source) or inventory(source) != provenance['source_inputs']:
        raise ValueError('Fresh compiled input changed')
    if digest(base / 'evidence/cutest.log') != provenance['cutest_log_sha256']:
        raise ValueError('Actual native C test log changed')
    tcl = verify_tcl(reviewed_root, base / 'archives', source)
    if len(tcl) != provenance['verified_tcl_files']:
        raise ValueError('Frozen Tcl comparison differs')
    prepared = Path(result['preparation']['fixture'])
    if (prepared.resolve() != prepared or prepared.parent != base.parent or
            not prepared.name.startswith('db-standard-')):
        raise ValueError('Redirected prepared standard generation')
    protected(prepared, directory=True)
    if record(prepared / 'preparation.json') != result['preparation']:
        raise ValueError('Prepared generation differs from native result')
    inputs = record(prepared / 'inputs.json')
    intent = record(prepared / 'preparation.intent.json')
    if (digest(prepared / 'inputs.json') != result['preparation']['input_manifest_sha256'] or
            digest(prepared / 'preparation.intent.json') != inputs['preparation_intent_sha256'] or
            intent['source'] != str(source) or intent['source_inputs'] != provenance['source_inputs']):
        raise ValueError('Prepared inputs are not bound to this actual native compilation')
    expected_files = {name: {key: value for key, value in row.items() if key != 'mode'}
                      for name, row in provenance['source_inputs'].items()}
    expected_files['build-test/standard-regression.tcl'] = {
        'sha256': digest(reviewed_root / 'scripts/build/h07/berkeley-db-standard-regression.tcl')}
    if inputs['source_files'] != expected_files:
        raise ValueError('Prepared manifest differs from native compiled inputs')
    for name, expected in expected_files.items():
        path = prepared / 'source' / name
        if not path.resolve().is_relative_to(prepared / 'source'):
            raise ValueError('Prepared native input escapes its generation')
        actual = {'sha256': digest(path)}
        if path.is_symlink():
            actual['symlink'] = os.readlink(path)
        if actual != expected:
            raise ValueError('Prepared native input changed: ' + name)
    return {'native_test_build_verified': True, 'standard_suite_verified': False,
            'prepared_input_binding_verified': True,
            'prepared_input_manifest_sha256': digest(prepared / 'inputs.json'),
            'package_accepted': False, 'fixture': str(base),
            'native_build_sha256': digest(base / 'native-build.json'),
            'inputs_sha256': digest(base / 'inputs.json'),
            'result_sha256': digest(base / 'result.json'),
            'native_input_files': len(provenance['source_inputs']), 'verified_tcl_files': len(tcl),
            'cutest_log_sha256': provenance['cutest_log_sha256'],
            'prepared_standard_fixture': result['preparation']['fixture']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('fixture', type=Path)
    args = parser.parse_args()
    subprocess.run(['bash', '-c', 'source /opt/toddy-build/scripts/build/target.sh; guard_target'], check=True)
    print(json.dumps(verify(args.fixture), indent=2))


if __name__ == '__main__':
    main()
