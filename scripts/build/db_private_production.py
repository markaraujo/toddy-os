#!/usr/bin/env python3
"""Verify production output/source separation without installing a package."""
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import traceback


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def save(path, value):
    with path.open('x') as stream:
        os.fchmod(stream.fileno(), 0o600)
        json.dump(value, stream, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


def snapshot(source):
    rows = {}
    for path in [source, *sorted(source.rglob('*'))]:
        info = path.lstat()
        if not path.resolve().is_relative_to(source):
            raise ValueError('Source alias escapes its generation')
        row = {'device': info.st_dev, 'inode': info.st_ino, 'mode': info.st_mode,
               'uid': info.st_uid, 'gid': info.st_gid, 'links': info.st_nlink}
        if path.is_file():
            row['sha256'] = digest(path)
        if path.is_symlink():
            row['symlink'] = os.readlink(path)
        rows[str(path.relative_to(source))] = row
    return rows


def main():
    base = Path(__file__).absolute().parent
    if (os.geteuid() != 0 or base.resolve() != base or
            base.parent != Path('/mnt/lfs/sources/recovery') or not base.name.startswith('db-production-') or
            base.stat().st_uid != 0 or base.stat().st_mode & 0o077):
        raise ValueError('Private production staging generation required')
    subprocess.run(['bash', '-c', 'source /opt/toddy-build/scripts/build/target.sh; guard_target'], check=True)
    lock = (base / 'lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    spec = json.loads((base / 'inputs.json').read_text())
    for name, sha in spec['files'].items():
        if Path(name).name != name or digest(base / name) != sha:
            raise ValueError('Private production input changed')
    source = Path(spec['source'])
    if source.resolve() != source or not source.is_relative_to(Path('/mnt/lfs/sources/recovery')):
        raise ValueError('Wrong native source generation')
    status = Path('/mnt/lfs/var/lib/dpkg/status')
    if digest(status) != spec['native_status_sha256']:
        raise ValueError('Native package status changed')
    if (base / 'result.json').exists():
        raise ValueError('Preserve completed production probe')
    before = snapshot(source)
    save(base / 'source-before.json', before)
    save(base / 'running.json', {'driver_pid': os.getpid(), 'started': datetime.now(timezone.utc).isoformat()})
    result = {'package_installed': False, 'full_suite_accepted': False, 'milestone_accepted': False,
              'source': str(source), 'inputs_sha256': digest(base / 'inputs.json'), 'stages': []}
    status_code = 1

    def stage(name, command, stdin=None):
        save(base / (name + '.intent.json'), {'command': command, 'timeout_seconds': 1800,
             'stdin_sha256': digest(stdin) if stdin else None})
        with (base / (name + '.log')).open('x') as log:
            input_stream = stdin.open('rb') if stdin else subprocess.DEVNULL
            try:
                process = subprocess.Popen(command, stdin=input_stream, stdout=log,
                                           stderr=subprocess.STDOUT, start_new_session=True)
                save(base / (name + '.pid.json'), {'pid': process.pid})
                timed_out = False
                try:
                    process.wait(timeout=1800)
                except subprocess.TimeoutExpired:
                    timed_out = True
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
            finally:
                if stdin:
                    input_stream.close()
            log.flush()
            os.fsync(log.fileno())
        evidence = {'exit': process.returncode, 'timed_out': timed_out,
                    'log_sha256': digest(base / (name + '.log'))}
        save(base / (name + '.exit.json'), evidence)
        result['stages'].append(dict(evidence, name=name))
        if process.returncode or timed_out:
            raise ValueError('Private production stage failed: ' + name)

    try:
        view = ['bash', str(base / 'berkeley-db-production-view.sh'), str(source), str(base)]
        stage('isolation', [*view, '/bin/bash', '-s'], base / 'readonly-check.sh')
        for name in ('configure', 'build', 'install', 'postcheck'):
            stage(name, [*view, 'bash', str(base / 'berkeley-db-private-production.sh'), str(base), name])
        after = snapshot(source)
        save(base / 'source-after.json', after)
        if after != before:
            raise ValueError('Production work changed the preserved source/custody tree')
        if digest(status) != spec['native_status_sha256']:
            raise ValueError('Installed native package database changed')
        if Path('/mnt/lfs/sources/stage/berkeley-db').exists():
            raise ValueError('Private staging escaped into shared package staging')
        library = base / 'stage/berkeley-db/usr/lib/libdb-5.3.so'
        if not library.is_file():
            raise ValueError('Native production library missing')
        if 'Native production DB commit/persistence/reopen/rollback passed' not in (base / 'postcheck.log').read_text():
            raise ValueError('Native transaction/reopen check incomplete')
        result.update(complete=True, source_unchanged=True, source_entries=len(before),
                      source_snapshot_sha256=digest(base / 'source-after.json'),
                      native_status_unchanged=True, shared_stage_absent=True,
                      production_library_sha256=digest(library))
        status_code = 0
    except BaseException as error:
        result.update(complete=False, error=str(error))
        traceback.print_exc()
    finally:
        save(base / 'result.json', result)
        save(base / 'driver.exit.json', {'exit': status_code})
        (base / 'running.json').unlink()
    return status_code


if __name__ == '__main__':
    sys.exit(main())
