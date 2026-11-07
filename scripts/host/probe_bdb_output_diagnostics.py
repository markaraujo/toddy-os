#!/usr/bin/env python3
"""Classify terminal DB diagnostics using the frozen native Tcl output checker.

This probe never accepts a suite, edits its sources or rewrites terminal results.
Only short diagnostic fixtures are created in a private disposable target path.
"""
import hashlib
import json
import subprocess

from vm import ROOT, ssh_args


REMOTE = r'''
import datetime, hashlib, json, pathlib, shutil, subprocess, tempfile
P = pathlib.Path
root = P('/mnt/lfs')
source = root / 'sources/db-5.3.28'
corrected = root / 'sources/recovery/db-standard-nfv62s4o/source'
def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()
terminal = P('/var/log/toddy/build/h07-berkeley-db.failed.json')
record = json.loads(terminal.read_text())
assert record['recipe_exit'] == 1 and record['changed_paths'] == 0
assert json.loads(terminal.with_name('h07-berkeley-db.manifest.json').read_text()) == {}
assert sha(terminal.with_name('h07-berkeley-db.log')) == record['log_sha256']
assert P('/var/log/toddy/h07-bdb-corrected-standard-driver.exit').read_text().strip() == '1'
checker = source / 'test/tcl/test.tcl'
assert sha(checker) == '81b82f33c9ca4fc878ee51fd1f235645824f1d4faba28d187bc23955c21681df'
text = checker.read_text()
proc = text[text.index('proc check_output '):text.index('\nproc r {')]
message = '\t Test142.b: Exclusive databases can have only 1 active txn.'
assert 'puts "\\t Test$tnum.b: Exclusive databases can have only 1 active txn."' in (source/'test/tcl/test142.tcl').read_text()
stdout_path = root / 'sources/evidence/h07-berkeley-db/standard.log'
unexpected = [l.removeprefix('UNEXPECTED OUTPUT: ') for l in stdout_path.read_text().splitlines()
              if l.startswith('UNEXPECTED OUTPUT: ')]
failures = [l for l in unexpected if l.startswith('FAIL:')]
warnings = [l for l in unexpected if l.startswith('WARNING: log record type ') and l.endswith(': not tested')]
other = [l for l in unexpected if l not in failures + warnings and l != message]
inputs = {name: {'original': sha(source/name), 'corrected': sha(corrected/name)} for name in
          ('test/tcl/test.tcl','test/tcl/test142.tcl','test/tcl/logtrack.tcl','test/tcl/logtrack.list')}
assert all(row['original'] == row['corrected'] for row in inputs.values())
work = P(tempfile.mkdtemp(prefix='bdb-output-diagnostic-', dir=root/'tmp'))
report = {'observed_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'original_terminal': record, 'installed_changes': 0, 'source_sha256': inputs,
          'original_standard_sha256': sha(stdout_path),
          'unexpected_total': len(unexpected), 'actual_failures': failures,
          'test142_information_count': unexpected.count(message),
          'uncovered_recovery_records': warnings, 'unclassified': other,
          'native_checks': [], 'suite_accepted': False, 'package_accepted': False}
try:
    cases = [('original informational spacing', message, 1),
             ('same message without extra space', message.replace('\t ', '\t', 1), 0),
             ('real failure remains rejected', 'FAIL: deliberate diagnostic control', 1),
             ('missing coverage remains rejected', warnings[0], 1)]
    for i, (label, line, expected) in enumerate(cases):
        sample = work / ('sample-' + str(i))
        sample.write_text(line + '\n')
        entry = work / ('check-' + str(i) + '.tcl')
        virtual = '/' + str(sample.relative_to(root))
        entry.write_text(proc + '\nset result [check_output {' + virtual + '}]\n'
                         + 'puts "CHECK_RESULT $result"\nif {$result != ' + str(expected) + '} {exit 1}\n')
        run = subprocess.run(['chroot',str(root),'/usr/bin/env','-i','PATH=/usr/bin','LC_ALL=C',
                              '/usr/bin/tclsh','/' + str(entry.relative_to(root))],
                             capture_output=True,text=True,timeout=30)
        report['native_checks'].append({'case': label, 'exit': run.returncode,
                                       'expected_checker_result': expected,
                                       'stdout': run.stdout, 'stderr': run.stderr})
        run.check_returncode()
    # The control changes only a diagnostic string in a new small fixture;
    # the actual suite, checker and all terminal logs remain byte-identical.
    assert sha(stdout_path) == report['original_standard_sha256']
    assert all(sha(source/n) == row['original'] and sha(corrected/n) == row['corrected']
               for n, row in inputs.items())
    report['source_and_original_output_unchanged'] = True
    report['complete'] = True
    shutil.rmtree(work)
except BaseException as error:
    report.update(complete=False, error=str(error), preserved_fixture=str(work))
print(json.dumps(report,indent=2))
raise SystemExit(0 if report.get('complete') else 1)
'''


def main():
    run = subprocess.run(ssh_args() + ['python3 -B -'], input=REMOTE, text=True,
                         capture_output=True, timeout=180)
    raw = (run.stdout + run.stderr).encode()
    sha = hashlib.sha256(raw).hexdigest()
    path = ROOT / '.local/logs' / ('h07-db-output-diagnostics-' + sha + '.json')
    path.write_bytes(raw)
    if run.returncode:
        raise RuntimeError('Diagnostic failed; preserve ' + str(path))
    report = json.loads(run.stdout)
    # Keep the complete captured terminal provenance in content-addressed evidence.
    report['original_terminal'] = {key: report['original_terminal'][key] for key in
                                  ('finished', 'recipe_exit', 'postcheck_exit', 'changed_paths')}
    print(json.dumps(report, indent=2))
    print('EVIDENCE_SHA256 ' + sha)


if __name__ == '__main__':
    main()
