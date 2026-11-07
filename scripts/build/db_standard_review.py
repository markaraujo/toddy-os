#!/usr/bin/env python3
"""Prepare a complete failed-summary review; never nominate or install Berkeley.

Both actual exits stay 1. A completed review is not an accepted standard suite.
The production handoff continues to require its existing strict success profile.
"""
import argparse
import fcntl
import json
import os
from pathlib import Path
import subprocess
import tempfile

import db_coverage_result
import db_standard_diagnostics
from db_standard_result import open_terminal, verify_execution_evidence

BUILD = Path('/var/log/toddy/build')


def validate_failure_record(record):
    if any(type(record.get(name)) is not int or record[name] != 1 for name in ('driver_exit', 'test_exit')):
        raise ValueError('Review requires both actual terminal exits to remain 1')
    if (record.get('error') != 'Complete native suite failed with exit 1'
            or record.get('test_inputs_unchanged') is not True
            or record.get('package_accepted') is not False
            or 'standard_suite_passed' in record or 'source_protected_from_test_user' in record):
        raise ValueError('Unexpected failed-result producer state; do not reinterpret it')


def review(base, coverage):
    with (BUILD / 'build.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if list(BUILD.glob('*.running.json')) or (BUILD / 'input-sync.running').exists():
            raise ValueError('Preserve active build/synchronization before terminal review')
        base, record, inputs = open_terminal(base, expected_exit=1)
        validate_failure_record(record)
        execution = verify_execution_evidence(base, record, inputs, private_source=False)
        witness = db_coverage_result.verify(coverage, base)
        work = Path(tempfile.mkdtemp(prefix='bdb-complete-review-', dir='/mnt/lfs/tmp'))
        native = work / 'checker'
        native.mkdir(mode=0o700)
        evidence = base / 'result-evidence'
        diagnostics = db_standard_diagnostics.native_review(
            base / 'source', evidence / 'ALL.OUT', evidence / 'standard.log', native)
        # Preserve the complete classification even if actual assertions fail.
        with (work / 'diagnostics.json').open('x') as stream:
            os.fchmod(stream.fileno(), 0o600)
            json.dump(diagnostics, stream, indent=2)
            stream.write('\n')
        db_standard_diagnostics.require_diagnostic_profile(diagnostics)
        if verify_execution_evidence(base, record, inputs, private_source=False) != execution:
            raise ValueError('Complete execution evidence changed during review')
        if db_coverage_result.verify(coverage, base) != witness:
            raise ValueError('Coverage evidence changed during review')
        result = {'review_complete': True, 'raw_driver_exit': 1, 'raw_test_exit': 1,
                  'suite_accepted': False, 'package_accepted': False, 'custody_sealed': False,
                  'work': str(work), 'execution': execution, 'coverage': witness,
                  'diagnostics': diagnostics,
                  'pending': 'Protected custody and explicit terminal qualification before production nomination'}
        with (work / 'review.json').open('x') as stream:
            os.fchmod(stream.fileno(), 0o600)
            json.dump(result, stream, indent=2)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('fixture', type=Path)
    parser.add_argument('--coverage', required=True, type=Path)
    args = parser.parse_args()
    subprocess.run(['bash', '-c',
                    'source /opt/toddy-build/scripts/build/target.sh; guard_target'], check=True)
    if os.geteuid() != 0:
        raise SystemExit('Disposable guest root required for protected evidence review')
    print(json.dumps(review(args.fixture, args.coverage), indent=2))


if __name__ == '__main__':
    main()
