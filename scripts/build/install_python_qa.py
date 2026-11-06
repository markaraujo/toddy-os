#!/usr/bin/env python3
"""Install or resume the H11 Python QA transfer from a verified prepared pair."""
import json
from pathlib import Path
import re
import subprocess
import sys

from package_backend import PackageBackend
from python_qa_transaction import atomic_json, execute
from stage_package import digest

HERE = Path(__file__).resolve().parent
TARGET = Path('/mnt/lfs')
RECORDS = Path('/var/log/toddy/packages')


def main():
    subprocess.run([sys.executable, str(HERE / 'h11/require_gate.py')], check=True)
    prepared = TARGET / 'sources/evidence/h11-python-qa-preparation'
    if prepared.resolve() != prepared:
        raise SystemExit('Prepared ownership transfer directory redirects')
    plan = json.loads((prepared / 'prepared.json').read_text())
    stems = [plan['predecessor'], *plan['successors']]
    if len(stems) != 3:
        raise SystemExit('Expected exactly three recorded package identities')
    for name, stem in zip(('python', 'python', 'python-test-support'), stems):
        if not re.fullmatch(re.escape(name) + r'_[0-9][0-9A-Za-z.+:~_-]*_amd64', stem):
            raise SystemExit('Invalid recorded ownership transfer identity')
    paths = [RECORDS / (stem + '.json') for stem in stems]
    if any(path.resolve() != path for path in paths):
        raise SystemExit('Ownership transfer record redirects')
    records = [json.loads(path.read_text()) for path in paths]
    if [record['archive_sha256'] for record in records] != plan['archive_sha256']:
        raise SystemExit('Prepared archive identities no longer match the package records')
    archives = [prepared / 'predecessor.deb', *(prepared / (stem + '.deb') for stem in stems[1:])]
    result = execute(PackageBackend(TARGET), TARGET, records, archives, prepared / 'transaction.json',
                     donor_record_sha256=digest(paths[0]))
    if result.get('complete') is not True:
        raise SystemExit('Ownership transfer did not pass complete native verification')
    for path, record in zip(paths[1:], records[1:]):
        record['installed'] = True
        atomic_json(path, record)
    print(json.dumps(result['verification'], indent=2))


if __name__ == '__main__':
    main()
