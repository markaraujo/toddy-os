"""Native Rust language/FFI checks, preserving the already passed std tests."""
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


def main():
    assert os.getuid() == 101
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    work = Path('/build')
    root = work / 'compiler-tests-3'
    assert not root.exists(), 'Inspect previous results; no replay'
    stat = os.statvfs(work)
    assert stat.f_bavail * stat.f_frsize >= 20 * 1024**3
    root.mkdir()
    host = work / 'compile/x86_64-unknown-linux-gnu'
    compiler = host / 'stage2/bin/rustc'
    before = digest(compiler)
    env = dict(os.environ, PATH='/build/bootstrap/usr/bin:' + os.environ['PATH'],
               CARGO_HOME='/build/home/.cargo', CARGO_NET_OFFLINE='true',
               CARGO_BUILD_JOBS='4', RUST_TEST_THREADS='4',
               LIBSQLITE3_SYS_USE_PKG_CONFIG='1', OPENSSL_NO_VENDOR='1')
    if subprocess.run(['pkg-config', '--exists', 'libssh2']).returncode == 0:
        env['LIBSSH2_SYS_USE_PKG_CONFIG'] = '1'
    # List only, never rerun passed std cases. Libtest identifies its own five
    # upstream ignores; count them independently from the 6223 passed cases.
    deps = host / 'stage2-std/x86_64-unknown-linux-gnu/dist/deps'
    env['LD_LIBRARY_PATH'] = ':'.join(map(str, [
        host / 'stage2/lib/rustlib/x86_64-unknown-linux-gnu/lib',
        host / 'stage2/lib', deps]))
    ignored = []
    for pattern in ['coretests-*', 'std-*', 'env_modify-*', 'sync-*']:
        bins = [p for p in deps.glob(pattern) if p.is_file() and os.access(p, os.X_OK)]
        assert len(bins) == 1, (pattern, bins)
        listing = subprocess.run([str(bins[0]), '--list', '--ignored'],
                                 env=env, capture_output=True, text=True)
        (root / (pattern[:-1] + 'ignored.log')).write_text(listing.stdout + listing.stderr)
        assert listing.returncode == 0
        names = re.findall(r'^(.+): test$', listing.stdout, re.M)
        ignored.extend({'driver': bins[0].name, 'case': name} for name in names)
    assert len(ignored) == 5, 'Unknown native ignore set; inspect source before accepting'
    (root / 'std-upstream-ignored.json').write_text(json.dumps(ignored, indent=2) + '\n')
    paths = ['borrowck', 'async-await', 'ffi', 'extern', 'editions',
             'rust-2024', 'threads-sendsync']
    command = ['python3', 'x.py', '--config', '/src/bootstrap.toml',
               '--build-dir', '/build/compile', 'test',
               *['tests/ui/' + p for p in paths]]
    log = root / 'native.log'
    with log.open('xb') as output:
        result = subprocess.run(command, cwd='/src/rustc-1.97.1-src', env=env,
                                stdout=output, stderr=subprocess.STDOUT)
    (root / 'native.exit').write_text(str(result.returncode) + '\n')
    text = log.read_text()
    summaries = re.findall(r'test result: (ok|FAILED)\. (\d+) passed; (\d+) failed; '
                           r'(\d+) ignored; (\d+) measured; (\d+) filtered out;', text)
    stat = os.statvfs(work)
    row = {'scope': 'Original native UI compiler suites for ownership, async, FFI, '
           'external linkage, editions and thread Send/Sync; not GTK UI tests',
           'command': command, 'native_exit': result.returncode, 'summaries': summaries,
           'log_sha256': digest(log), 'compiler_before_sha256': before,
           'compiler_after_sha256': digest(compiler),
           'upstream_std_ignored': ignored,
           'free_bytes_after_tests': stat.f_bavail * stat.f_frsize}
    (root / 'results.json').write_text(json.dumps(row, indent=2) + '\n')
    print(json.dumps(row), flush=True)
    assert result.returncode == 0 and summaries
    assert all(r[0] == 'ok' and int(r[2]) == 0 for r in summaries)
    assert sum(int(r[1]) for r in summaries) > 100
    assert row['compiler_before_sha256'] == row['compiler_after_sha256']
    assert row['free_bytes_after_tests'] >= 16 * 1024**3


if __name__ == '__main__':
    main()
