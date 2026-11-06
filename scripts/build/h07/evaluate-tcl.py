#!/usr/bin/env python3
"""Tcl's harness can report failures despite make exiting zero: inspect summaries."""
import json
from pathlib import Path
import re
import sys


def classify(text):
    summaries = [tuple(map(int, row)) for row in re.findall(
        r'^all\.tcl:\s+Total\s+(\d+)\s+Passed\s+(\d+)\s+Skipped\s+(\d+)\s+Failed\s+(\d+)\s*$',
        text, re.M)]
    optional = []
    failures = []
    for line in text.splitlines():
        if not re.search(r'^==== .* FAILED$|Test file error:|^Error in startup script:', line):
            continue
        # ADR-0011: only these exact missing optional database-client libraries
        # are classified unavailable, never reported as passing tests.
        match = re.search(r'Test file error: couldn\x27t load file "(libmysql\.so\.15|libiodbc\.so|libpq\.so\.5)": \1: cannot open shared object file: No such file or directory$', line)
        if match:
            optional.append({'library': match[1], 'output': line})
        else:
            failures.append(line)
    # Core Tcl has tens of thousands of tests; extension-only summaries do not
    # establish that the core suite finished. Require its large final summary.
    complete = any(total >= 10000 for total, passed, skipped, failed in summaries)
    valid = all(total == passed + skipped + failed for total, passed, skipped, failed in summaries)
    return {'summaries': summaries, 'complete': complete, 'failure_lines': failures,
            'unavailable_optional_database_tests': optional,
            'accepted': complete and valid and not failures and all(row[3] == 0 for row in summaries)}


def main():
    record = classify(Path(sys.argv[1]).read_text(errors='replace'))
    Path(sys.argv[2]).write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps(record))
    if not record['accepted']:
        raise SystemExit('Tcl full suite incomplete or failed; inspect original output')


if __name__ == '__main__':
    main()
