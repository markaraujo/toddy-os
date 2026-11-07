#!/usr/bin/env python3
"""Nominate a complete native result, then consume it under the recipe dispatcher."""
import argparse
from contextlib import redirect_stdout
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

from db_standard_result import digest, protected, verify_completed

BUILD = Path('/var/log/toddy/build')
SOURCES = Path('/mnt/lfs/sources')
HERE = Path(__file__).resolve().parent
CANDIDATE = BUILD / 'h07-berkeley-db.standard-candidate.json'
RECIPE = HERE / 'h07/berkeley-db-verified-production.sh'
OLD_START = '2026-11-06T17:09:04.423666+00:00'
OLD_RECIPE = 'cc31735563a41bcc8498e2afbd69214204892e76531e0eadae1dfe919f9f7dbd'
# Exact terminal reports independently rechecked with native check_output.
# They contain two real failures plus the ADR-0083 diagnostics. Archiving this
# failed attempt never substitutes for corrected-suite acceptance.
OLD_ALL_OUT_SHA256 = '2f75c918ba8d713db23435355e62af25c3b4b623f1c5a802d09d41b1e2ccab7c'
OLD_STANDARD_SHA256 = '2d0441963aad69dda37ee0f26fd4814ea35541bec2e5008390eb6a8779c38283'
FAILURES = [
    'FAIL: run_subsystem: other_repmgr repmgr007:  FAIL:00:42:16 (00:00:00) errchk: expected 1, got 0',
    'FAIL: run_subsystem: multi_repmgr repmgr100:  Skipping: db_repsite executable not found.  Is it built?']
ORIGINAL = {
    'failed.json': BUILD / 'h07-berkeley-db.failed.json',
    'manifest.json': BUILD / 'h07-berkeley-db.manifest.json',
    'recipe.log': BUILD / 'h07-berkeley-db.log',
    'driver.exit': BUILD.parent / 'h07-bdb-corrected-standard-driver.exit',
    'driver.log': BUILD.parent / 'h07-bdb-corrected-standard-driver.log',
    'ALL.OUT': SOURCES / 'db-5.3.28/build-test/ALL.OUT',
    'standard.log': SOURCES / 'evidence/h07-berkeley-db/standard.log',
}


def validate_original(paths):
    record = json.loads(paths['failed.json'].read_text())
    if (record.get('started') != OLD_START or record.get('recipe_sha256') != OLD_RECIPE or
            type(record.get('recipe_exit')) is not int or record['recipe_exit'] != 1 or
            record.get('postcheck_exit') is not None or record.get('changed_paths') != 0):
        raise ValueError('Original attempt has an unknown terminal result')
    if json.loads(paths['manifest.json'].read_text()) != {}:
        raise ValueError('Original attempt changed installed paths')
    if paths['driver.exit'].read_text().strip() != '1':
        raise ValueError('Original driver is not terminal with failure')
    if digest(paths['recipe.log']) != record.get('log_sha256'):
        raise ValueError('Original terminal recipe log changed')
    lines = paths['ALL.OUT'].read_text().splitlines()
    if ([line for line in lines if line.startswith('FAIL')] != FAILURES or
            lines.count('Regression Tests Failed') != 1 or len(lines) < 2 or
            lines[-2] != 'Regression Tests Failed' or
            not re.fullmatch(r'Test suite run completed at: \d{2}:\d{2} \d{2}/\d{2}/(?:\d{2}|\d{4})', lines[-1])):
        raise ValueError('Original suite has additional failures or is incomplete')
    if (digest(paths['ALL.OUT']) != OLD_ALL_OUT_SHA256
            or digest(paths['standard.log']) != OLD_STANDARD_SHA256):
        raise ValueError('Original reports differ from the independently diagnosed terminal evidence')


def write_new(path, record):
    # Exclusive creation preserves a prior nomination after interruption.
    with path.open('x') as stream:
        os.fchmod(stream.fileno(), 0o600)
        json.dump(record, stream, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


def prepare(fixture):
    with (BUILD / 'build.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if list(BUILD.glob('*.running.json')) or (BUILD / 'input-sync.running').exists():
            raise ValueError('An original recipe or input sync is still unfinished')
        if CANDIDATE.exists() or CANDIDATE.is_symlink():
            raise ValueError('Preserve the existing nomination before retry')
        if (BUILD / 'h07-berkeley-db.success.json').exists() or (SOURCES / 'stage/berkeley-db').exists():
            raise ValueError('Existing production state needs diagnosis')
        validate_original(ORIGINAL)
        with redirect_stdout(sys.stderr):
            verified = verify_completed(fixture)
        archive = BUILD / 'history' / ('berkeley-db-handoff-' +
                    datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
        archive.mkdir(mode=0o700)
        hashes = {}
        for name, source in ORIGINAL.items():
            destination = archive / name
            shutil.copyfile(source, destination)
            destination.chmod(0o600)
            hashes[name] = digest(destination)
        validate_original({name: archive / name for name in ORIGINAL})
        write_new(CANDIDATE, {'fixture': str(fixture), 'verified_result': verified,
                             'original_archive': str(archive), 'original_sha256': hashes,
                             'production_recipe_sha256': digest(RECIPE),
                             'package_accepted': False})
        return {'candidate': str(CANDIDATE), 'sha256': digest(CANDIDATE),
                'package_accepted': False}


def require_dispatcher():
    path = BUILD / 'h07-berkeley-db.running.json'
    protected(path)
    record = json.loads(path.read_text())
    if record.get('recipe_sha256') != digest(RECIPE) or record.get('user') != 'root':
        raise ValueError('Handoff requires the normal production recipe dispatcher')
    # Confirm this process actually descends from that recorded recipe; a stale
    # running marker alone must never authorize installation.
    current, ancestors = os.getpid(), set()
    while current > 1 and current not in ancestors:
        ancestors.add(current)
        status = Path('/proc', str(current), 'status').read_text().splitlines()
        current = int(next(line.split()[1] for line in status if line.startswith('PPid:')))
    if record.get('recipe_pid') not in ancestors:
        raise ValueError('Current process is not a child of the recorded recipe')
    with (BUILD / 'build.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return
        raise ValueError('Exclusive dispatcher lock is not held')


def consume():
    require_dispatcher()
    protected(CANDIDATE, private=True)
    record = json.loads(CANDIDATE.read_text())
    if record.get('package_accepted') is not False or record.get('production_recipe_sha256') != digest(RECIPE):
        raise ValueError('Nomination refers to a different production recipe')
    archive = Path(record['original_archive'])
    if (archive.resolve() != archive or archive.parent != BUILD / 'history' or
            not archive.name.startswith('berkeley-db-handoff-')):
        raise ValueError('Unsafe original-result archive')
    protected(archive, private=True, directory=True)
    if set(record['original_sha256']) != set(ORIGINAL):
        raise ValueError('Incomplete original-result archive')
    for name, expected in record['original_sha256'].items():
        protected(archive / name, private=True)
        if digest(archive / name) != expected:
            raise ValueError('Original terminal evidence changed: ' + name)
    validate_original({name: archive / name for name in ORIGINAL})
    with redirect_stdout(sys.stderr):
        verified = verify_completed(Path(record['fixture']))
    if verified != record['verified_result']:
        raise ValueError('The complete corrected result changed after nomination')
    return record['fixture']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    sub.add_parser('prepare').add_argument('fixture', type=Path)
    sub.add_parser('consume')
    args = parser.parse_args()
    subprocess.run(['bash', '-c',
                    'source /opt/toddy-build/scripts/build/target.sh; guard_target'], check=True)
    if os.geteuid() != 0:
        raise SystemExit('Disposable guest root required')
    if args.action == 'prepare':
        print(json.dumps(prepare(args.fixture), indent=2))
    else:
        print(consume())


if __name__ == '__main__':
    main()
