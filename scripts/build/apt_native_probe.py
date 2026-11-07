#!/usr/bin/env python3
"""Compile and test the frozen native APT in private storage without installation."""
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shlex
import signal
import subprocess
import sys
import traceback

ARCHIVE = 'apt_3.0.4.tar.xz'
SOURCE_SHA = 'e853aec49afbe520ebcd4dbcbc98e1c55262c6bf1c119cf43e6aec69752443c6'
ROOT = Path('/mnt/lfs')


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def save(path, value):
    with path.open('x') as stream:
        os.fchmod(stream.fileno(), 0o600)
        json.dump(value, stream, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


def main():
    base = Path(__file__).absolute().parent
    if (os.geteuid() != 0 or base.resolve() != base or base.parent != ROOT / 'sources/recovery' or
            not base.name.startswith('apt-native-') or base.stat().st_uid != 0 or base.stat().st_mode & 0o022):
        raise ValueError('Designated private native APT generation required')
    subprocess.run(['bash', '-c', 'source /opt/toddy-build/scripts/build/target.sh; guard_target'], check=True)
    lock = (base / 'lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    inputs = json.loads((base / 'inputs.json').read_text())
    for name, expected in inputs['files'].items():
        if Path(name).name != name or sha(base / name) != expected:
            raise ValueError('Private APT recipe changed')
    if sha(ROOT / 'sources' / ARCHIVE) != SOURCE_SHA:
        raise ValueError('Frozen APT archive changed')
    status = ROOT / 'var/lib/dpkg/status'
    if sha(status) != inputs['native_status_sha256']:
        raise ValueError('Native package database changed')
    berkeley = Path(inputs['berkeley_prefix'])
    for name, expected in inputs['berkeley_files'].items():
        if sha(berkeley / name) != expected:
            raise ValueError('Verified private production DB input changed')
    if (base / 'result.json').exists():
        raise ValueError('Preserve existing native APT result')
    virtual = '/' + str(base.relative_to(ROOT))
    native_db = '/' + str(berkeley.relative_to(ROOT))
    save(base / 'running.json', {'pid': os.getpid(), 'started': datetime.now(timezone.utc).isoformat()})
    result = {'package_installed': False, 'milestone_accepted': False, 'berkeley_suite_accepted': False,
              'inputs_sha256': sha(base / 'inputs.json'), 'source_sha256': SOURCE_SHA, 'stages': []}
    code = 1

    def stage(name, argv, body=None):
        save(base / (name + '.intent.json'), {'argv': argv, 'stdin_sha256':
             hashlib.sha256(body).hexdigest() if body else None, 'timeout_seconds': 7200})
        with (base / (name + '.log')).open('x') as log:
            run = subprocess.Popen(argv, stdin=subprocess.PIPE if body else subprocess.DEVNULL,
                                   stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            save(base / (name + '.pid.json'), {'pid': run.pid})
            timed_out = False
            try:
                run.communicate(body, timeout=7200)
            except subprocess.TimeoutExpired:
                timed_out = True
                os.killpg(run.pid, signal.SIGKILL)
                run.wait()
            log.flush()
            os.fsync(log.fileno())
        row = {'name': name, 'exit': run.returncode, 'timed_out': timed_out,
               'log_sha256': sha(base / (name + '.log'))}
        save(base / (name + '.exit.json'), row)
        result['stages'].append(row)
        if run.returncode or timed_out:
            raise ValueError('Private APT stage failed: ' + name)

    try:
        stage('source', ['bash', '--noprofile', '--norc', '-euc', 'cd ' + shlex.quote(str(base)) +
                         '; python3 -B /opt/toddy-build/scripts/build/source.py ' + ARCHIVE])
        command = ['chroot', str(ROOT), '/usr/bin/env', '-i', 'HOME=/root', 'TERM=dumb',
                   'PATH=/usr/bin:/usr/sbin', 'LC_ALL=POSIX', 'CONFIG_SITE=/dev/null',
                   'TODDY_APT_SOURCE=' + virtual + '/apt-3.0.4',
                   'TODDY_APT_EVIDENCE=' + virtual + '/evidence', 'TODDY_APT_JOBS=2',
                   'TODDY_APT_BERKELEY_PREFIX=' + native_db]
        for name in ('configure', 'build', 'check'):
            stage(name, [*command, '/usr/bin/bash', '--noprofile', '--norc', '-s', '--', name],
                  (base / 'apt-inner.sh').read_bytes())
        if sha(status) != inputs['native_status_sha256']:
            raise ValueError('Native installed package state changed')
        for name, expected in inputs['berkeley_files'].items():
            if sha(berkeley / name) != expected:
                raise ValueError('Private Berkeley production inputs changed')
        binary = base / 'apt-3.0.4/build/ftparchive/apt-ftparchive'
        if not binary.is_file():
            raise ValueError('Actual apt-ftparchive binary missing')
        result.update(complete=True, native_status_unchanged=True,
                      apt_ftparchive_sha256=sha(binary),
                      consumer_cache_checks_passed=False)
        code = 0
    except BaseException as error:
        result.update(complete=False, error=str(error))
        traceback.print_exc()
    finally:
        save(base / 'result.json', result)
        save(base / 'driver.exit.json', {'exit': code})
        (base / 'running.json').unlink()
    return code


if __name__ == '__main__':
    sys.exit(main())
