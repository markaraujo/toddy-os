"""Run frozen Rust's native core/alloc/std unit and integration tests offline."""
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import subprocess


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def qualify_preserved_log(text):
    """Recover test evidence only when the original bootstrap reports success."""
    assert len(re.findall(r'^Build completed successfully in .+$', text, re.M)) == 1
    assert text.rstrip().splitlines()[-1].startswith('Build completed successfully in ')
    assert not re.search(r'^test result: FAILED\.', text, re.M)
    # One explicitly declared harness=false subprocess driver prints its own
    # success sentinel, rather than a libtest summary. Never infer an unknown
    # custom driver's success from absence of a failure.
    parts = re.split(r'(?m)^\s+Running ', text)[1:]
    custom = [p for p in parts if 'test result:' not in p]
    assert len(custom) == 1 and custom[0].startswith('tests/pipe_subprocess.rs (')
    assert '\nTest pipe_subprocess.rs success\n' in custom[0]
    runs = [p.splitlines()[0] for p in parts if 'test result:' in p]
    summaries = [dict(zip(['passed', 'failed', 'ignored', 'measured', 'filtered'],
                         map(int, row))) for row in re.findall(
        r'^test result: ok\. (\d+) passed; (\d+) failed; (\d+) ignored; '
        r'(\d+) measured; (\d+) filtered out;', text, re.M)]
    assert runs and len(runs) == len(summaries), 'Missing test-driver result'
    for required in ['alloctests-', 'coretests-', '/deps/std-']:
        assert any(required in run for run in runs), 'Missing critical suite'
    assert sum(row['passed'] for row in summaries) > 1000
    assert all(row['failed'] == row['filtered'] == row['measured'] == 0
               for row in summaries)
    return [{'driver': run, **row} for run, row in zip(runs, summaries)]


def main():
    assert os.getuid() == 101
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    work = Path('/build')
    proof = json.loads((work / 'compile-result.json').read_text())
    assert proof['version'] == '1.97.1' and proof['compiler_consumer_exit'] == 0
    report = work / 'std-tests-2.json'
    log = work / 'std-tests-2.log'
    assert not report.exists() and not log.exists(), 'Reconcile previous test output'
    stat = os.statvfs(work)
    assert stat.f_bavail * stat.f_frsize >= 20 * 1024**3
    # Bootstrap deliberately recreates stage2/bin while assembling a test
    # sysroot. Tool build outputs live separately; do not treat the ephemeral
    # install layout as a durable input or rebuild tools after its removal.
    host = work / 'compile/x86_64-unknown-linux-gnu'
    tools = sorted((host / 'stage2-tools-bin').glob('*'))
    tools += [host / 'stage2/bin/rustc', host / 'stage2/bin/rustdoc']
    before = {str(p): digest(p) for p in tools if p.is_file()}
    assert any(p.endswith('/rustc') for p in before)
    (work / 'std-tests-2-inputs.json').write_text(json.dumps(before, indent=2) + '\n')
    env = dict(os.environ, PATH='/build/bootstrap/usr/bin:' + os.environ['PATH'],
               CARGO_HOME='/build/home/.cargo', CARGO_NET_OFFLINE='true',
               CARGO_BUILD_JOBS='4', RUST_TEST_THREADS='4',
               LIBSQLITE3_SYS_USE_PKG_CONFIG='1', OPENSSL_NO_VENDOR='1')
    if subprocess.run(['pkg-config', '--exists', 'libssh2']).returncode == 0:
        env['LIBSSH2_SYS_USE_PKG_CONFIG'] = '1'
    command = ['python3', 'x.py', '--config', '/src/bootstrap.toml',
               '--build-dir', '/build/compile', 'test', '--tests',
               'library/core', 'library/alloc', 'library/std']
    with log.open('xb') as output:
        result = subprocess.run(command, cwd='/src/rustc-1.97.1-src', env=env,
                                stdout=output, stderr=subprocess.STDOUT)
    (work / 'std-tests-2-native.exit').write_text(str(result.returncode) + '\n')
    summaries = [dict(zip(['passed', 'failed', 'ignored', 'measured', 'filtered'],
                         map(int, row))) for row in re.findall(
        r'test result: (?:ok|FAILED)\. (\d+) passed; (\d+) failed; (\d+) ignored; '
        r'(\d+) measured; (\d+) filtered out;', log.read_text())]
    after = {p: digest(Path(p)) for p in before}
    stat = os.statvfs(work)
    row = {'scope': 'Native core/alloc/std unit and integration tests only; '
           'doctests/compiler suites/tool tests/staging/install remain separate',
           'command': command, 'exit': result.returncode, 'summaries': summaries,
           'log_sha256': digest(log), 'compiler_tools_before': before,
           'compiler_tools_unchanged': before == after,
           'free_bytes_after_tests': stat.f_bavail * stat.f_frsize}
    report.write_text(json.dumps(row, indent=2) + '\n')
    print(json.dumps(row), flush=True)
    assert result.returncode == 0 and summaries, 'Native tests failed or produced no results'
    assert sum(r['passed'] for r in summaries) > 1000
    assert all(r['failed'] == 0 for r in summaries)
    assert before == after, 'Compiler tools unexpectedly changed; inspect before continuing'
    assert row['free_bytes_after_tests'] >= 16 * 1024**3


if __name__ == '__main__':
    main()
