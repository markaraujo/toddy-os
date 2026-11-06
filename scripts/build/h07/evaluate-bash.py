#!/usr/bin/env python3
"""Bash run-all always exits zero; require full coverage and inspect diff output."""
import json
from pathlib import Path
import re


def classify(text, expected):
    lines = text.splitlines()
    observed = {line.strip() for line in lines if line.strip() in expected}
    differences = [line for line in lines if re.match(r'^[<>] ', line)]
    missing = sorted(expected - observed)
    return {'expected_tests': len(expected), 'observed_tests': len(observed),
            'missing': missing, 'unclassified_diff_output': differences,
            'accepted': len(expected) >= 50 and not missing and not differences}


def main():
    base = Path('/mnt/lfs/sources/bash-5.3/tests')
    expected = {path.name for path in base.glob('run-*') if path.is_file()
                and path.name not in ('run-all', 'run-minimal', 'run-gprof')
                and not path.name.endswith(('.orig', '~'))}
    folder = Path('/mnt/lfs/sources/evidence/h07-bash')
    record = classify((folder / 'check.log').read_text(errors='replace'), expected)
    (folder / 'classification.json').write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps(record))
    if not record['accepted']:
        raise SystemExit('Bash suite incomplete or has unclassified diff output; inspect raw tests')


if __name__ == '__main__':
    main()
