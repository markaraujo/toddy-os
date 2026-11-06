#!/usr/bin/env python3
"""Require every Bash group and classify only exact source-backed differences."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import re


def grouped_diffs(text):
    groups = {}
    current = None
    for line in text.splitlines():
        if re.fullmatch(r'run-[A-Za-z0-9_-]+', line.strip()):
            current = line.strip()
        if re.match(r'^[<>] ', line):
            groups.setdefault(current, []).append(line)
    return groups


def classify(text, expected, known=None):
    known = known or {}
    lines = text.splitlines()
    headers = Counter(line.strip() for line in lines if line.strip() in expected)
    missing = sorted(expected - headers.keys())
    duplicates = sorted(k for k,v in headers.items() if v != 1)
    accepted_groups = {}
    unknown = {}
    for group, differences in grouped_diffs(text).items():
        if group in known and differences == known[group]:
            accepted_groups[group] = differences
        else:
            unknown[group or 'before_first_group'] = differences
    fatal = [l for l in lines if re.search(r'(^make.*\*\*\*|Segmentation fault|core dumped)',l)]
    return {'expected_tests': len(expected), 'observed_tests': len(headers),
            'missing': missing, 'duplicate_headers': duplicates,
            'classified_reference_differences': accepted_groups,
            'unclassified_diff_output': unknown, 'fatal_output': fatal,
            'accepted': len(expected) >= 50 and not missing and not duplicates
                        and not unknown and not fatal}


def main():
    base = Path('/mnt/lfs/sources/bash-5.3/tests')
    expected = {path.name for path in base.glob('run-*') if path.is_file()
                and path.name not in ('run-all', 'run-minimal', 'run-gprof')
                and not path.name.endswith(('.orig', '~'))}
    folder = Path('/mnt/lfs/sources/evidence/h07-bash')
    config = json.loads((Path(__file__).resolve().parents[3]/'config/bash-test-reference.json').read_text())
    reference = (folder/'reference.log').read_bytes()
    if hashlib.sha256(reference).hexdigest() != config['sha256']:
        raise SystemExit('Unverified official Bash reference')
    reference_groups = grouped_diffs(reference.decode())
    for group,allowed in config['known_diff_groups'].items():
        if Counter(allowed) - Counter(reference_groups.get(group, [])):
            raise SystemExit('Exception not supported by pinned official reference')
    record = classify((folder/'check.log').read_text(errors='replace'), expected,
                      config['known_diff_groups'])
    record['reference_sha256'] = config['sha256']
    (folder/'classification.json').write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps(record))
    if not record['accepted']:
        raise SystemExit('Bash suite incomplete or has unclassified output; inspect raw tests')


if __name__ == '__main__':
    main()
