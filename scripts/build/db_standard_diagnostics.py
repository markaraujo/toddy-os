"""Classify complete DB output without rewriting it or accepting a package.

ADR-0083 supplies source/native evidence for two exact diagnostic categories.
The full result's process/input/coverage checks remain separate requirements.
"""
from collections import Counter
import hashlib
from pathlib import Path
import re
import subprocess

from db_standard_progress import HEADERS, SOURCE_SHA256, CONFIG_SHA256

INFORMATIONAL = '\t Test142.b: Exclusive databases can have only 1 active txn.'
COVERAGE_TYPES = ('__bam_irep', '__crdel_inmem_create', '__crdel_inmem_remove',
                  '__crdel_inmem_rename', '__db_merge', '__db_pg_trunc', '__db_pgno',
                  '__db_realloc', '__ham_changeslot', '__ham_contract')
WARNINGS = tuple('WARNING: log record type ' + name + ': not tested' for name in COVERAGE_TYPES)
EXPECTED = Counter({INFORMATIONAL: 13, **{line: 1 for line in WARNINGS}})
VERSION = 'Berkeley DB 5.3.28: (September  9, 2013)'
SOURCE_FILES = {
    'test/tcl/test.tcl': SOURCE_SHA256,
    'build-test/db_config.h': CONFIG_SHA256,
    'test/tcl/test142.tcl': '3cacea1ce719d20e585e74d40a7f5b3cc07671f32f78c52aa64aea3c269ac28b',
    'test/tcl/logtrack.tcl': 'ae98ef9d4edf15c271281bea4dd3b9d4e3400c56a54d5dc5a154bd17e3595e6f',
    'test/tcl/logtrack.list': 'a057684e81a7810325f0425516d116f93dd1e224c65903a79bbade01150e0b99'}


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def complete_lines(report):
    lines = report.splitlines()
    stamp = r'\d{2}:\d{2} \d{2}/\d{2}/(?:\d{2}|\d{4})'
    if (len(lines) < 4 or not re.fullmatch('Test suite run started at: ' + stamp, lines[0])
            or lines[1] != VERSION or lines.count('Regression Tests Failed') != 1
            or 'Regression Tests Succeeded' in lines or lines[-2] != 'Regression Tests Failed'
            or not re.fullmatch('Test suite run completed at: ' + stamp, lines[-1])):
        raise ValueError('Require the complete unmodified failed-summary profile')
    return lines


def classify(report, stdout, checker_stdout):
    """Reconcile the original summary with independent native checker output.

    A classification may describe real failures. It never grants acceptance.
    The caller must bind checker_stdout to actual native execution and inputs.
    """
    lines = complete_lines(report)
    checker = checker_stdout.splitlines()
    if (not checker or checker[-1] != 'TODDY_CHECK_RESULT 1'
            or any(not line.startswith('UNEXPECTED OUTPUT: ') for line in checker[:-1])):
        raise ValueError('Independent native checker did not reproduce the failed result')
    unexpected = [line.removeprefix('UNEXPECTED OUTPUT: ') for line in checker[:-1]]
    expected_stdout = ([lines[0], VERSION] + HEADERS + checker[:-1] +
                       ['Regression Tests Failed', 'Check UNEXPECTED OUTPUT lines.',
                        'Review ALL.OUT.x for details.', lines[-1],
                        'Complete DB regression summary failed'])
    if stdout.splitlines() != expected_stdout:
        raise ValueError('Outer dispatch, terminal stdout or native checker reconciliation differs')
    # A true caught exception remains a failure, regardless of whether its
    # message happens to contain a qualified warning or informational string.
    failures = [line for line in lines if line.startswith('FAIL')]
    checker_failures = [line for line in unexpected if line.startswith('FAIL')]
    if failures != checker_failures:
        raise ValueError('Native checker and report disagree about actual failures')
    counts = Counter(unexpected)
    classified = Counter({line: counts[line] for line in EXPECTED if counts[line]})
    unknown = [line for line in unexpected if line not in EXPECTED and not line.startswith('FAIL')]
    return {'classification_complete': True, 'outer_headers': len(HEADERS),
            'actual_failures': failures, 'unclassified': unknown,
            'informational_count': counts[INFORMATIONAL],
            'coverage_warning_counts': {name: counts[line] for name, line in zip(COVERAGE_TYPES, WARNINGS)},
            'exact_diagnostic_profile': classified == EXPECTED,
            'unexpected_count': len(unexpected), 'raw_summary': 'Regression Tests Failed',
            'suite_accepted': False, 'package_accepted': False}


def require_diagnostic_profile(report):
    if (report.get('classification_complete') is not True or report.get('actual_failures') != []
            or report.get('unclassified') != [] or report.get('exact_diagnostic_profile') is not True
            or report.get('informational_count') != 13 or report.get('unexpected_count') != 23
            or report.get('coverage_warning_counts') != {name: 1 for name in COVERAGE_TYPES}
            or report.get('outer_headers') != len(HEADERS)
            or report.get('suite_accepted') is not False or report.get('package_accepted') is not False):
        raise ValueError('Actual failures, unknown output or changed diagnostic multiplicity remain')


def native_review(source, all_out, stdout_path, work, root=Path('/mnt/lfs')):
    """Run only the frozen checker on a copy of the terminal report body.

    Does not source test.tcl, execute any database case or edit original reports.
    work must be a fresh private directory inside the disposable target.
    """
    source, all_out, stdout_path, work = map(Path, (source, all_out, stdout_path, work))
    if (work.resolve() != work or work == root / 'tmp' or not work.is_relative_to(root / 'tmp')
            or work.stat().st_uid != 0 or work.stat().st_mode & 0o077
            or any(work.iterdir())):
        raise ValueError('Native diagnostic requires a fresh private target work directory')
    for name, expected in SOURCE_FILES.items():
        if digest(source / name) != expected:
            raise ValueError('Frozen diagnostic source/configuration changed: ' + name)
    original_sha = {str(p): digest(p) for p in (all_out, stdout_path)}
    raw = all_out.read_text()
    lines = complete_lines(raw)
    source_text = (source / 'test/tcl/test.tcl').read_text()
    procedure = source_text[source_text.index('proc check_output '):source_text.index('\nproc r {')]
    body = work / 'terminal-body.txt'
    body.write_text('\n'.join(lines[:-2]) + '\n')
    program = work / 'checker.tcl'
    native_body = '/' + body.relative_to(root).as_posix()
    program.write_text(procedure + '\nset result [check_output {' + native_body + '}]\n'
                       'puts "TODDY_CHECK_RESULT $result"\n')
    command = ['chroot', str(root), '/usr/bin/env', '-i', 'PATH=/usr/bin', 'LC_ALL=C',
               '/usr/bin/tclsh', '/' + program.relative_to(root).as_posix()]
    completed = subprocess.run(command, capture_output=True, text=True, timeout=60)
    (work / 'checker.stdout').write_text(completed.stdout)
    (work / 'checker.stderr').write_text(completed.stderr)
    (work / 'checker.exit').write_text(str(completed.returncode) + '\n')
    completed.check_returncode()
    if completed.stderr:
        raise ValueError('Independent checker emitted unexpected stderr')
    report = classify(raw, stdout_path.read_text(), completed.stdout)
    if (any(digest(Path(path)) != sha for path, sha in original_sha.items())
            or any(digest(source / name) != sha for name, sha in SOURCE_FILES.items())):
        raise ValueError('Original report or source changed during independent review')
    report.update(original_sha256=original_sha, source_sha256=SOURCE_FILES,
                  native_command=command, native_exit=completed.returncode,
                  checker_sha256=digest(program), body_sha256=digest(body),
                  checker_stdout_sha256=digest(work / 'checker.stdout'),
                  original_reports_unchanged=True)
    return report
