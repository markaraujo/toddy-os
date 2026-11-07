#!/usr/bin/env python3
"""Qualify only the complete ADR-0083 diagnostic profile; preserve raw exit 1.

This prepares a separate evidence decision. Production nomination still uses
its strict gate until this path has an actual complete positive validation.
"""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess

from db_source_custody import seal_verified_source, snapshot, verify_receipt
from db_standard_diagnostics import require_diagnostic_profile
from db_standard_result import digest, open_terminal, protected
from db_standard_review import BUILD, review_under_lock

DECISION = 'Complete native suite qualified for exact ADR-0083 diagnostic defects'


def stable_proof(review):
    if (review.get('review_complete') is not True
            or type(review.get('raw_driver_exit')) is not int or review['raw_driver_exit'] != 1
            or type(review.get('raw_test_exit')) is not int or review['raw_test_exit'] != 1
            or review.get('suite_accepted') is not False or review.get('package_accepted') is not False
            or review.get('custody_sealed') is not False):
        raise ValueError('Qualification requires the actual complete failed-summary review')
    diagnostics = review['diagnostics']
    require_diagnostic_profile(diagnostics)
    if (type(diagnostics.get('native_exit')) is not int or diagnostics['native_exit'] != 0
            or diagnostics.get('original_reports_unchanged') is not True
            or review['coverage'].get('custody_sealed') is not True
            or review['coverage'].get('coverage_witness_verified') is not True
            or review['execution'].get('execution_evidence_verified') is not True):
        raise ValueError('Native diagnostics, execution or protected coverage are unverified')
    # Temporary checker paths change on an independent recheck. Retain the
    # original full review separately; compare its stable bytes and decisions.
    classified = {key: value for key, value in diagnostics.items()
                  if key not in ('native_command', 'checker_sha256')}
    return {'execution': review['execution'], 'coverage': review['coverage'],
            'diagnostics': classified, 'raw_driver_exit': 1, 'raw_test_exit': 1}


def validate_qualification(record, proof, source_custody_sha256):
    if (record.get('decision') != DECISION or record.get('standard_suite_qualified') is not True
            or record.get('package_accepted') is not False
            or record.get('raw_driver_exit') != 1 or type(record['raw_driver_exit']) is not int
            or record.get('raw_test_exit') != 1 or type(record['raw_test_exit']) is not int
            or record.get('raw_upstream_summary') != 'Regression Tests Failed'
            or record.get('coverage_fixture') != proof['coverage']['fixture']
            or record.get('source_custody_sha256') != source_custody_sha256
            or stable_proof(record['review']) != proof or record.get('proof') != proof):
        raise ValueError('Qualification differs from complete native execution or custody')
    output = record.get('native_checker_stdout')
    if (not isinstance(output, str) or hashlib.sha256(output.encode()).hexdigest()
            != proof['diagnostics']['checker_stdout_sha256']):
        raise ValueError('Original native checker output was not preserved')


def verify_qualified(base, review=None):
    """Recheck real bytes/diagnostics and custody; never create acceptance files."""
    base, _, _ = open_terminal(base, expected_exit=1)
    path = base / 'standard-qualification.json'
    protected(path, private=True)
    record = json.loads(path.read_text())
    coverage = Path(record['coverage_fixture'])
    current = review if review is not None else review_under_lock(base, coverage)
    proof = stable_proof(current)
    verify_receipt(base, proof, snapshot(base / 'source'))
    validate_qualification(record, proof, digest(base / 'source-custody.json'))
    return {'standard_suite_qualified': True, 'package_accepted': False,
            'raw_driver_exit': 1, 'raw_test_exit': 1, 'fixture': str(base),
            'qualification_sha256': digest(path), 'proof': proof,
            'source_custody_sha256': digest(base / 'source-custody.json')}


def qualify(base, coverage):
    if os.geteuid() != 0:
        raise ValueError('Disposable guest root required')
    with (BUILD / 'build.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if list(BUILD.glob('*.running.json')) or (BUILD / 'input-sync.running').exists():
            raise ValueError('Preserve active dispatcher/input synchronization')
        # This refuses a live suite or any actual/unknown failure before any
        # source metadata change, custody intent or qualification is written.
        reviewed = review_under_lock(base, coverage)
        proof = stable_proof(reviewed)
        base = Path(proof['execution']['fixture'])
        path = base / 'standard-qualification.json'
        if path.exists():
            return verify_qualified(base, reviewed)
        seal_verified_source(base, proof,
                             lambda: stable_proof(review_under_lock(base, coverage)))
        record = {'decision': DECISION, 'standard_suite_qualified': True,
                  'package_accepted': False, 'raw_driver_exit': 1, 'raw_test_exit': 1,
                  'raw_upstream_summary': 'Regression Tests Failed',
                  'coverage_fixture': str(coverage), 'proof': proof, 'review': reviewed,
                  'source_custody_sha256': digest(base / 'source-custody.json'),
                  'native_checker_stdout': (Path(reviewed['work']) / 'checker/checker.stdout').read_text()}
        validate_qualification(record, proof, digest(base / 'source-custody.json'))
        from db_source_custody import save
        save(path, record)
        return verify_qualified(base, reviewed)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('qualify', 'verify'))
    parser.add_argument('fixture', type=Path)
    parser.add_argument('--coverage', type=Path)
    args = parser.parse_args()
    subprocess.run(['bash', '-c', 'source /opt/toddy-build/scripts/build/target.sh; guard_target'], check=True)
    if args.action == 'qualify':
        if args.coverage is None:
            parser.error('Qualification requires the actual protected coverage fixture')
        result = qualify(args.fixture, args.coverage)
    else:
        result = verify_qualified(args.fixture)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
