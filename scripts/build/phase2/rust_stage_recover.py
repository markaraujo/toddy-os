"""Reuse the successful Rust stage after the known nonempty sysconfdir cleanup failure."""
import hashlib
import json
import os
from pathlib import Path
import resource
import subprocess
import sys


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def entries():
    rows = {}
    for path in sorted(Path('/stage').rglob('*')):
        if path.is_symlink():
            rows[str(path.relative_to('/stage'))] = {'symlink': os.readlink(path)}
        elif path.is_file():
            rows[str(path.relative_to('/stage'))] = {'sha256': digest(path), 'size': path.stat().st_size}
    return rows


def main():
    assert os.getuid() == 101
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    probe, original_failure = sys.argv[1:]
    compile(probe, 'rust_tools_probe.py', 'exec')
    root = Path('/build/stage-tests-4')
    assert (root / 'install.exit').read_text().strip() == '0'
    assert not (root / 'tools.exit').exists()
    assert original_failure.rstrip().endswith("OSError: [Errno 39] Directory not empty: '/stage/etc'")
    assert 'completion.parent.parent.rmdir()' in original_failure
    assert not Path('/build/tool-consumers-4').exists()
    assert not Path('/build/tool-consumers-5').exists()
    assert not Path('/build/stage-tests-recovery-5').exists()
    schema = Path('/stage/etc/target-spec-json-schema.json')
    assert schema.is_file() and not schema.is_symlink()
    assert set(p.name for p in schema.parent.iterdir()) == {schema.name}
    assert json.loads(schema.read_text())['title'] == 'TargetSpecJson'
    assert Path('/stage/usr/share/bash-completion/completions/cargo').is_file()
    assert not Path('/stage/etc/bash_completion.d').exists()
    previous = Path('/build/stage-tests-recovery-6')
    assert (previous / 'tools.exit').read_text().strip() == '1'
    assert "assert versions['cargo'].startswith('cargo 1.97.0 ')" in (previous / 'tools.log').read_text()
    attempted = Path('/build/tool-consumers-6')
    assert {p.name for p in attempted.iterdir()} == {'versions.json'}
    assert json.loads((attempted / 'versions.json').read_text())['cargo'].startswith('cargo 1.97.1 ')
    work = Path('/build/stage-tests-recovery-7')
    assert not work.exists() and not Path('/build/tool-consumers-7').exists()
    stat = os.statvfs('/build')
    assert stat.f_bavail * stat.f_frsize >= 17 * 1024**3
    work.mkdir()
    before = entries()
    assert before == json.loads((previous / 'stage-before.json').read_text()), 'Earlier probe changed stage'
    (work / 'stage-before.json').write_text(json.dumps(before, indent=2) + '\n')
    with (work / 'tools.log').open('xb') as output:
        result = subprocess.run(['python3', '-c', probe, '/stage/usr', '/build/tool-consumers-7'],
                                stdout=output, stderr=subprocess.STDOUT)
    (work / 'tools.exit').write_text(str(result.returncode) + '\n')
    assert result.returncode == 0, 'Preserve output and diagnose; never restage to retry a probe'
    after = entries()
    assert before == after, 'A tool consumer changed the SDK stage'
    consumers = json.loads(Path('/build/tool-consumers-7/results.json').read_text())
    assert consumers['versions']['cargo'].startswith('cargo 1.97.1 ')
    stat = os.statvfs('/build')
    row = {'scope': 'Preserved successful native stage plus corrected actual tool probe; no install replay',
           'original_install_exit': 0, 'original_stage_wrapper_exit': 1, 'refused_prediction_job_exit': 1,
           'original_stage_wrapper_cause': 'Cleanup tried removing sysconfdir containing legitimate target schema',
           'previous_probe_exit': 1, 'previous_probe_cause': 'Collector used Cargo fallback version; bootstrap CFG_RELEASE overrides it',
           'tools_exit': result.returncode, 'probe_sha256': hashlib.sha256(probe.encode()).hexdigest(),
           'original_failure_sha256': hashlib.sha256(original_failure.encode()).hexdigest(),
           'retained_schema_sha256': digest(schema),
           'install_log_sha256': digest(root / 'install.log'),
           'tools_log_sha256': digest(work / 'tools.log'), 'consumers': consumers,
           'entries': after, 'stage_unchanged_by_probe': True,
           'free_bytes_after_probe': stat.f_bavail * stat.f_frsize}
    (work / 'results.json').write_text(json.dumps(row, indent=2) + '\n')
    print(json.dumps({k: v for k, v in row.items() if k != 'entries'}), flush=True)
    assert row['free_bytes_after_probe'] >= 16 * 1024**3


if __name__ == '__main__':
    main()
