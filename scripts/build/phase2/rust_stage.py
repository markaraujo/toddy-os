"""Stage the qualified native Rust SDK and test the staged real tool consumers."""
import hashlib
import json
import os
from pathlib import Path
import resource
import shutil
import subprocess
import sys


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    assert os.getuid() == 101
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    probe, std_log_sha = sys.argv[1:]
    compile(probe, 'rust_tools_probe.py', 'exec')
    work = Path('/build')
    root = work / 'stage-tests-4'
    assert not root.exists() and not Path('/stage/usr').exists(), 'Inspect existing stage; no replay'
    assert digest(work / 'std-tests-2.log') == std_log_sha
    compiler = json.loads((work / 'compiler-tests-3/results.json').read_text())
    assert compiler['native_exit'] == 0 and compiler['summaries'] == [['ok', '1552', '0', '7', '0', '19666']]
    assert (work / 'compiler-tests-3/native.exit').read_text().strip() == '0'
    stat = os.statvfs(work)
    assert stat.f_bavail * stat.f_frsize >= 20 * 1024**3
    root.mkdir()
    env = dict(os.environ, PATH='/build/bootstrap/usr/bin:' + os.environ['PATH'],
               CARGO_HOME='/build/home/.cargo', CARGO_NET_OFFLINE='true',
               CARGO_BUILD_JOBS='4', RUST_TEST_THREADS='4', DESTDIR='/stage',
               LIBSQLITE3_SYS_USE_PKG_CONFIG='1', OPENSSL_NO_VENDOR='1')
    if subprocess.run(['pkg-config', '--exists', 'libssh2']).returncode == 0:
        env['LIBSSH2_SYS_USE_PKG_CONFIG'] = '1'
    command = ['python3', 'x.py', '--config', '/src/bootstrap.toml',
               '--build-dir', '/build/compile', 'install']
    with (root / 'install.log').open('xb') as output:
        install = subprocess.run(command, cwd='/src/rustc-1.97.1-src', env=env,
                                 stdout=output, stderr=subprocess.STDOUT)
    (root / 'install.exit').write_text(str(install.returncode) + '\n')
    assert install.returncode == 0
    completion = Path('/stage/etc/bash_completion.d/cargo')
    moved = False
    if completion.exists():
        destination = Path('/stage/usr/share/bash-completion/completions/cargo')
        destination.parent.mkdir(parents=True, exist_ok=True)
        assert not destination.exists()
        shutil.move(completion, destination)
        completion.parent.rmdir()
        # Rust also installs its target-spec JSON schema under sysconfdir.
        # Keep legitimate payload; remove only a genuinely empty directory.
        if not any(completion.parent.parent.iterdir()):
            completion.parent.parent.rmdir()
        moved = True
    with (root / 'tools.log').open('xb') as output:
        result = subprocess.run(['python3', '-c', probe, '/stage/usr', '/build/tool-consumers-4'],
                                env=env, stdout=output, stderr=subprocess.STDOUT)
    (root / 'tools.exit').write_text(str(result.returncode) + '\n')
    assert result.returncode == 0
    consumers = json.loads((work / 'tool-consumers-4/results.json').read_text())
    entries = {}
    for path in sorted(Path('/stage').rglob('*')):
        if path.is_symlink():
            entries[str(path.relative_to('/stage'))] = {'symlink': os.readlink(path)}
        elif path.is_file():
            entries[str(path.relative_to('/stage'))] = {'sha256': digest(path), 'size': path.stat().st_size}
    stat = os.statvfs(work)
    proof = {'scope': 'Native Rust SDK staged and actual offline tool consumers only; owned install pending',
             'install_exit': install.returncode, 'tools_exit': result.returncode,
             'probe_sha256': hashlib.sha256(probe.encode()).hexdigest(),
             'std_log_sha256': std_log_sha, 'compiler_log_sha256': compiler['log_sha256'],
             'cargo_completion_moved_to_shared_data': moved,
             'consumers': consumers, 'entries': entries,
             'install_log_sha256': digest(root / 'install.log'),
             'tools_log_sha256': digest(root / 'tools.log'),
             'free_bytes_after_stage': stat.f_bavail * stat.f_frsize}
    (root / 'results.json').write_text(json.dumps(proof, indent=2) + '\n')
    print(json.dumps({k: v for k, v in proof.items() if k != 'entries'}), flush=True)
    assert proof['free_bytes_after_stage'] >= 16 * 1024**3


if __name__ == '__main__':
    main()
