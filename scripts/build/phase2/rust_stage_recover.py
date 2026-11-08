"""Reuse a successful Rust stage after the known Cargo-version probe assertion."""
import hashlib
import json
import os
from pathlib import Path
import resource
import re
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
    probe, original_probe = sys.argv[1:]
    compile(probe, 'rust_tools_probe.py', 'exec')
    root = Path('/build/stage-tests-4')
    assert (root / 'install.exit').read_text().strip() == '0'
    assert (root / 'tools.exit').read_text().strip() == '1'
    original = (root / 'tools.log').read_text()
    assert original.rstrip().endswith('AssertionError')
    expected = "    assert versions['cargo'].startswith('cargo 1.97.1 ')"
    lines = original_probe.splitlines()
    assert lines.count(expected) == 1
    failed_line = lines.index(expected) + 1
    # Python -c tracebacks carry line numbers, not the original statement text.
    # The parent supplies the exact original probe from job4's immutable receipt.
    frames = re.findall(r'File "<string>", line (\d+), in (\w+|<module>)', original)
    assert len(frames) == 2 and frames[-1] == (str(failed_line), 'main'), original
    assert not list(Path('/build/tool-consumers-4').iterdir()), 'Unexpected earlier consumer writes'
    work = Path('/build/stage-tests-recovery-5')
    assert not work.exists() and not Path('/build/tool-consumers-5').exists()
    stat = os.statvfs('/build')
    assert stat.f_bavail * stat.f_frsize >= 17 * 1024**3
    work.mkdir()
    before = entries()
    (work / 'stage-before.json').write_text(json.dumps(before, indent=2) + '\n')
    with (work / 'tools.log').open('xb') as output:
        result = subprocess.run(['python3', '-c', probe, '/stage/usr', '/build/tool-consumers-5'],
                                stdout=output, stderr=subprocess.STDOUT)
    (work / 'tools.exit').write_text(str(result.returncode) + '\n')
    assert result.returncode == 0, 'Preserve output and diagnose; never restage to retry a probe'
    after = entries()
    assert before == after, 'A tool consumer changed the SDK stage'
    consumers = json.loads(Path('/build/tool-consumers-5/results.json').read_text())
    assert consumers['versions']['cargo'].startswith('cargo 1.97.0 ')
    stat = os.statvfs('/build')
    row = {'scope': 'Preserved successful native stage plus corrected actual tool probe; no install replay',
           'original_install_exit': 0, 'original_tool_probe_exit': 1,
           'original_tool_probe_cause': 'Incorrect assumption that Cargo patch version equals rustc patch',
           'tools_exit': result.returncode, 'probe_sha256': hashlib.sha256(probe.encode()).hexdigest(),
           'original_tools_log_sha256': digest(root / 'tools.log'),
           'install_log_sha256': digest(root / 'install.log'),
           'tools_log_sha256': digest(work / 'tools.log'), 'consumers': consumers,
           'entries': after, 'stage_unchanged_by_probe': True,
           'free_bytes_after_probe': stat.f_bavail * stat.f_frsize}
    (work / 'results.json').write_text(json.dumps(row, indent=2) + '\n')
    print(json.dumps({k: v for k, v in row.items() if k != 'entries'}), flush=True)
    assert row['free_bytes_after_probe'] >= 16 * 1024**3


if __name__ == '__main__':
    main()
