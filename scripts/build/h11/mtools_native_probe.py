#!/usr/bin/env python3
"""Durable private native Mtools build; no installed package or boot claim."""
import hashlib
import json
import os
from pathlib import Path
import shlex
import signal
import subprocess
import sys
import tarfile
import traceback


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def save(path, value):
    with path.open('x') as stream:
        stream.write(json.dumps(value, indent=2) + '\n')
        stream.flush()
        os.fsync(stream.fileno())


def main():
    base = Path(__file__).resolve().parent
    root = Path('/mnt/lfs')
    if (os.geteuid() != 0 or base.parent != root / 'sources/recovery'
            or not base.name.startswith('mtools-native-') or base.stat().st_mode & 0o077):
        raise ValueError('Private protected experiment directory required')
    subprocess.run(['bash', '-c', 'source /opt/toddy-build/scripts/build/target.sh; guard_target'], check=True)
    spec = json.loads((base / 'inputs.json').read_text())
    for name, sha in spec['files'].items():
        if Path(name).name != name or digest(base / name) != sha:
            raise ValueError('Private input hash differs')
    before = digest(root / 'var/lib/dpkg/status')
    save(base / 'running.json', {'pid': os.getpid(), 'status_sha256': before,
                               'inputs_sha256': digest(base / 'inputs.json')})
    native_base = '/' + str(base.relative_to(root))
    prefix = native_base + '/prefix'
    directory = native_base + '/mtools-4.0.50'
    command = ['chroot', str(root), '/usr/bin/env', '-i', 'HOME=' + native_base,
               'LC_ALL=C.UTF-8', 'PATH=' + prefix + '/bin:/usr/bin:/usr/sbin',
               'MTOOLSRC=/dev/null', 'PYTHONDONTWRITEBYTECODE=1']
    result = {'native_package_installed': False, 'milestone_accepted': False,
              'native_boot_verified': False, 'stages': []}
    exit_code = 1
    try:
        def stage(name, args):
            save(base / (name + '.intent.json'), {'argv': args, 'timeout_seconds': 1800})
            with (base / (name + '.log')).open('x') as output:
                run = subprocess.Popen([*command, *args], stdout=output,
                                       stderr=subprocess.STDOUT, start_new_session=True)
                timed_out = False
                try:
                    run.wait(timeout=1800)
                except subprocess.TimeoutExpired:
                    timed_out = True
                    os.killpg(run.pid, signal.SIGKILL)
                    run.wait()
                output.flush()
                os.fsync(output.fileno())
            save(base / (name + '.exit.json'), {'exit': run.returncode, 'timed_out': timed_out})
            result['stages'].append({'name': name, 'exit': run.returncode,
                                    'log_sha256': digest(base / (name + '.log'))})
            if run.returncode:
                raise ValueError('Private native stage failed: ' + name)

        with tarfile.open(base / 'mtools-4.0.50.tar.bz2') as source:
            for member in source.getmembers():
                tarfile.data_filter(member, base)
                if Path(member.name).parts[0] != 'mtools-4.0.50':
                    raise ValueError('Unexpected source root')
            source.extractall(base, filter='data')
        configure = ['./configure', '--prefix=' + prefix, '--sysconfdir=' + native_base,
                     '--without-x', '--disable-floppyd']
        stage('configure', ['/usr/bin/bash', '-c', 'cd ' + shlex.quote(directory)
                            + ' && exec ' + shlex.join(configure)])
        stage('build', ['/usr/bin/make', '-C', directory, '-j2'])
        stage('upstream-check', ['/usr/bin/make', '-C', directory, 'check'])
        if 'No self tests included' not in (base / 'upstream-check.log').read_text():
            raise ValueError('Unexpected upstream check target behavior')
        stage('private-install', ['/usr/bin/make', '-C', directory, 'install'])
        if (base / 'prefix/bin/floppyd').exists():
            raise ValueError('Unrequested floppy server installed')
        stage('roundtrip', ['/usr/bin/bash', native_base + '/mtools-image-roundtrip.sh'])
        if digest(root / 'var/lib/dpkg/status') != before:
            raise ValueError('Installed native package status changed')
        for name, sha in spec['files'].items():
            if digest(base / name) != sha:
                raise ValueError('Private probe input changed')
        result.update(complete=True, installed_status_unchanged=True,
                      upstream_self_tests_available=False,
                      binaries={name: digest(base / 'prefix/bin' / name)
                                for name in ('mformat', 'mcopy', 'mdir', 'mtools')})
        exit_code = 0
    except BaseException as error:
        result.update(complete=False, error=str(error))
        traceback.print_exc()
    finally:
        save(base / 'result.json', result)
        save(base / 'driver.exit.json', {'exit': exit_code})
    return exit_code


if __name__ == '__main__':
    sys.exit(main())
