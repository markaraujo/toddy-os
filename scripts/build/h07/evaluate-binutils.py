#!/usr/bin/env python3
"""Classify the complete critical Binutils suite against frozen LFS evidence."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import sys

# Minimum pass counts from the official LFS 13.1 x86_64 reference run.
SUITES = {'binutils/binutils.sum': 351, 'gas/testsuite/gas.sum': 2098,
          'ld/ld.sum': 3304, 'libsframe/libsframe.sum': 168,
          'libctf/libctf.sum': 40, 'gprofng/gprofng.sum': 5}
EXPECTED = ('gprofng/gprofng.sum', 'tmpdir/gp-gmon')


def classify(reports, exit_code, gprof_log):
    suites = {}
    unexplained = []
    expected = []
    complete = True
    for name, minimum in SUITES.items():
        text = reports.get(name, '')
        results = re.findall(r'^(PASS|FAIL|XFAIL|XPASS|UNSUPPORTED|UNRESOLVED|ERROR|UNTESTED): (.*)$', text, re.M)
        counts = Counter(status for status, test in results)
        summary = re.search(r'# of expected passes\s+(\d+)', text)
        finished = bool(re.search(r'=== \w+ Summary ===', text) and summary
                        and int(summary[1]) == counts['PASS'] and counts['PASS'] >= minimum)
        complete = complete and finished
        suites[name] = {'counts': dict(counts), 'complete': finished,
                        'sha256': hashlib.sha256(text.encode()).hexdigest()}
        for status, test in results:
            if status == 'FAIL' and (name, test) == EXPECTED:
                expected.append({'suite': name, 'test': test})
            elif status in ('FAIL', 'XPASS', 'UNRESOLVED', 'ERROR'):
                unexplained.append({'suite': name, 'status': status, 'test': test})
    gprof_ok = (bool(re.search(r'^# TOTAL:\s+3$', gprof_log, re.M))
                and bool(re.search(r'^# PASS:\s+3$', gprof_log, re.M))
                and bool(re.search(r'^# FAIL:\s+0$', gprof_log, re.M))
                and bool(re.search(r'^# ERROR:\s+0$', gprof_log, re.M)))
    accepted = complete and gprof_ok and not unexplained and exit_code in (0, 2)
    if exit_code != 0 and not expected:
        accepted = False
    return {'suite_exit': exit_code, 'suites': suites, 'gprof_passed': gprof_ok,
            'expected_failures': expected, 'unexplained_failures': unexplained,
            'reference': 'LFS 13.1-systemd 8.22 and official 13.1 i7-14700K test log',
            'accepted': accepted}


def main():
    base = Path('/mnt/lfs/sources/binutils-2.47/build')
    folder = Path('/mnt/lfs/sources/evidence/h07-binutils')
    record = classify({name: (base / name).read_text(errors='replace') for name in SUITES},
                      int((folder / 'check.exit').read_text()),
                      (base / 'gprof/testsuite/test-suite.log').read_text(errors='replace'))
    for name in ['check.log', 'test-reports.tar.gz']:
        record[name + '_sha256'] = hashlib.sha256((folder / name).read_bytes()).hexdigest()
    (folder / 'classification.json').write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps(record))
    if not record['accepted']:
        raise SystemExit('Critical Binutils suite not accepted; diagnose before installation')


if __name__ == '__main__':
    main()
