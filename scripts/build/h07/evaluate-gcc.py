#!/usr/bin/env python3
"""Accept complete final GCC results only against a pinned official LFS run."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

STATUS = re.compile(r'^(PASS|FAIL|XFAIL|XPASS|UNSUPPORTED|UNRESOLVED|ERROR|UNTESTED):\s+(.+)$')
UNEXPECTED = {'FAIL', 'XPASS', 'UNRESOLVED', 'ERROR'}


def normalize(line):
    return ' '.join(line.split())


def classify(reports, reference, exit_code, minimums):
    known = {normalize(line) for line in reference.splitlines()
             if STATUS.match(line) and STATUS.match(line)[1] in UNEXPECTED}
    suites = {}
    unexplained = []
    explained = []
    for name, minimum in minimums.items():
        text = reports.get(name, '')
        results = [STATUS.fullmatch(line.strip()) for line in text.splitlines()]
        results = [match.groups() for match in results if match]
        counts = Counter(status for status, test in results)
        declared = re.findall(r'^# of expected passes\s+(\d+)\s*$', text, re.M)
        complete = (bool(re.search(r'=== [^\n]+ Summary ===', text)) and len(declared) == 1
                    and int(declared[0]) == counts['PASS'] and counts['PASS'] >= minimum)
        suites[name] = {'counts': dict(counts), 'complete': complete,
                        'sha256': hashlib.sha256(text.encode()).hexdigest()}
        for status, test in results:
            if status not in UNEXPECTED:
                continue
            row = {'suite': name, 'status': status, 'test': test}
            if normalize(status + ': ' + test) in known:
                explained.append(row)
            else:
                unexplained.append(row)
    accepted = (bool(minimums) and all(suite['complete'] for suite in suites.values())
                and not unexplained and exit_code in (0, 2))
    if exit_code != 0 and not explained:
        accepted = False
    return {'suite_exit': exit_code, 'suites': suites,
            'known_reference_outcomes': explained, 'unexplained_outcomes': unexplained,
            'accepted': accepted}


def main():
    root = Path(__file__).resolve().parents[3]
    config_path = root / 'config/compiler-test-reference.json'
    config = json.loads(config_path.read_text())
    base = Path('/mnt/lfs/sources/gcc-16.2.0/build')
    evidence = Path('/mnt/lfs/sources/evidence/h07-gcc')
    reference_bytes = (evidence / 'reference.log').read_bytes()
    if hashlib.sha256(reference_bytes).hexdigest() != config['sha256']:
        raise SystemExit('Frozen official GCC reference mismatch; no acceptance')
    minimums = config['minimum_expected_passes']
    reports = {name: (base / name).read_text(errors='replace') for name in minimums}
    record = classify(reports, reference_bytes.decode(), int((evidence / 'check.exit').read_text()), minimums)
    record['reference'] = {'url': config['url'], 'sha256': config['sha256'],
                           'config_sha256': hashlib.sha256(config_path.read_bytes()).hexdigest()}
    for name in ['check.log', 'test-reports.tar.gz', 'test-summary.txt']:
        record[name + '_sha256'] = hashlib.sha256((evidence / name).read_bytes()).hexdigest()
    (evidence / 'classification.json').write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps(record))
    if not record['accepted']:
        raise SystemExit('Critical GCC suite not accepted; diagnose raw results before install')


if __name__ == '__main__':
    main()
