#!/usr/bin/env python3
"""Durable private native Squashfs build/roundtrip, never a package install."""
import hashlib
import json
import os
import signal
from pathlib import Path
import subprocess
import sys
import tarfile
import traceback

OPTIONS = ['GZIP_SUPPORT=1', 'XZ_SUPPORT=1', 'ZSTD_SUPPORT=1',
           'LZO_SUPPORT=0', 'LZ4_SUPPORT=0', 'LZMA_SUPPORT=0', 'LZMA_XZ_SUPPORT=0',
           'XATTR_SUPPORT=1', 'XATTR_OS_SUPPORT=1', 'COMP_DEFAULT=xz']


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
            or not base.name.startswith('squashfs-native-') or base.stat().st_mode & 0o077):
        raise ValueError('Private protected native experiment directory required')
    subprocess.run(['bash', '-c', 'source /opt/toddy-build/scripts/build/target.sh; guard_target'], check=True)
    spec = json.loads((base / 'inputs.json').read_text())
    for name, sha in spec['files'].items():
        if Path(name).name != name or digest(base / name) != sha:
            raise ValueError('Private probe input hash differs')
    before = digest(root / 'var/lib/dpkg/status')
    save(base / 'running.json', {'pid': os.getpid(), 'status_sha256': before, 'inputs_sha256': digest(base / 'inputs.json')})
    result = {'native_package_installed': False, 'milestone_accepted': False,
              'native_kernel_boot_verified': False, 'stages': []}
    exit_code = 1
    try:
        archive = base / 'squashfs-tools-4.7.5.tar.gz'
        with tarfile.open(archive) as source:
            for member in source.getmembers():
                tarfile.data_filter(member, base)
                if Path(member.name).parts[0] != 'squashfs-tools-4.7.5':
                    raise ValueError('Unexpected source root')
            source.extractall(base, filter='data')
        directory = base / 'squashfs-tools-4.7.5/squashfs-tools'
        native_directory = '/' + str(directory.relative_to(root))
        command = ['chroot', str(root), '/usr/bin/env', '-i', 'HOME=/root', 'LC_ALL=C',
                   'PATH=' + native_directory + ':/usr/bin:/usr/sbin', 'PYTHONDONTWRITEBYTECODE=1']

        def stage(name, args):
            with (base / (name + '.log')).open('x') as output:
                run = subprocess.Popen([*command, *args], stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
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

        stage('build', ['/usr/bin/make', '-C', native_directory, '-j2', *OPTIONS, 'mksquashfs', 'unsquashfs'])
        result['binaries'] = {name: digest(directory / name) for name in ('mksquashfs', 'unsquashfs')}
        stage('version', [native_directory + '/mksquashfs', '-version'])
        if 'mksquashfs version 4.7.5' not in (base / 'version.log').read_text():
            raise ValueError('Unexpected compiled compressor version')
        stage('roundtrip', ['/usr/bin/python3', '/' + str((base / 'squashfs-roundtrip.py').relative_to(root))])
        if digest(root / 'var/lib/dpkg/status') != before:
            raise ValueError('Installed native package status changed during private experiment')
        result.update(complete=True, installed_status_unchanged=True, build_options=OPTIONS,
                      source_sha256=digest(archive), kernel=os.uname().release)
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
