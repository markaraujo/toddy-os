#!/usr/bin/env python3
"""Compile the frozen kernel in a private fixture, without installing the OS."""
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
from datetime import datetime, timezone

ROOT = Path('/mnt/lfs')
ARCHIVE = 'linux-7.1.8.tar.xz'
SOURCE_SHA = 'ff01dcb449279d5b4cfccdb01fee639cf5ff1803f1749a77844dd33915422c49'
RELEASE = '7.1.8-toddy'


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def save(path, data):
    with path.open('x') as stream:
        stream.write(json.dumps(data, indent=2) + '\n')
        stream.flush()
        os.fsync(stream.fileno())


def main():
    base = Path(__file__).absolute().parent
    if (os.geteuid() != 0 or base.resolve() != base
            or base.parent != ROOT / 'sources/recovery'
            or not base.name.startswith('kernel-native-')
            or base.stat().st_uid != 0 or base.stat().st_mode & 0o077):
        raise ValueError('Protected private kernel fixture required')
    lock = (base / 'lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    subprocess.run(['bash', '-c', 'source /opt/toddy-build/scripts/build/target.sh; guard_target'], check=True)
    inputs = json.loads((base / 'inputs.json').read_text())
    for name, sha in inputs['files'].items():
        if Path(name).name != name or digest(base / name) != sha:
            raise ValueError('Private kernel input changed')
    if digest(ROOT / 'sources' / ARCHIVE) != SOURCE_SHA:
        raise ValueError('Frozen kernel archive changed')
    status = ROOT / 'var/lib/dpkg/status'
    if digest(status) != inputs['native_status_sha256']:
        raise ValueError('Native package state changed; review before resuming')
    if (base / 'result.json').exists():
        raise ValueError('Completed fixture is immutable; collect its result')
    attempts = base / 'attempts'
    attempts.mkdir(exist_ok=True)
    attempt = attempts / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    attempt.mkdir(mode=0o700)
    save(attempt / 'running.json', {'pid': os.getpid(), 'inputs_sha256': digest(base / 'inputs.json')})
    virtual = '/' + str(base.relative_to(ROOT))
    directory = virtual + '/linux-7.1.8'
    command = ['chroot', str(ROOT), '/usr/bin/env', '-i', 'PATH=/usr/bin:/usr/sbin',
               'LC_ALL=C', 'CONFIG_SITE=/dev/null', 'MAKEFLAGS=-j2',
               'KBUILD_BUILD_USER=toddy', 'KBUILD_BUILD_HOST=builder', 'KBUILD_BUILD_VERSION=1',
               'KBUILD_BUILD_TIMESTAMP=2026-11-05 00:00:00 UTC']
    completed = base / 'completed'
    completed.mkdir(exist_ok=True)
    exit_code = 1

    def stage(name, argv, timeout=7200):
        marker = completed / (name + '.json')
        if marker.exists():
            previous = json.loads(marker.read_text())
            if (previous['argv'] != argv or previous['exit'] != 0
                    or digest(base / previous['log']) != previous['log_sha256']):
                raise ValueError('Completed stage evidence differs: ' + name)
            return
        log = attempt / (name + '.log')
        save(attempt / (name + '.intent.json'), {'argv': argv, 'timeout_seconds': timeout})
        with log.open('x') as output:
            process = subprocess.Popen(argv, stdout=output, stderr=subprocess.STDOUT,
                                       start_new_session=True)
            save(attempt / (name + '.pid.json'), {'pid': process.pid})
            timed_out = False
            try:
                process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                timed_out = True
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            output.flush()
            os.fsync(output.fileno())
        evidence = {'argv': argv, 'exit': process.returncode, 'timed_out': timed_out,
                    'log': str(log.relative_to(base)), 'log_sha256': digest(log)}
        save(attempt / (name + '.exit.json'), evidence)
        if process.returncode or timed_out:
            raise ValueError('Native kernel stage failed: ' + name)
        save(marker, evidence)

    def native(name, body, timeout=7200):
        stage(name, [*command, '/usr/bin/bash', '-euc', body], timeout)

    try:
        # A failed/partial extraction is retained for diagnosis, never removed.
        stage('source', ['bash', '-euc', 'cd ' + shlex.quote(str(base))
                        + '; python3 /opt/toddy-build/scripts/build/source.py ' + ARCHIVE], 600)
        native('configure', f'''cd {shlex.quote(directory)}
make mrproper
make x86_64_defconfig
scripts/kconfig/merge_config.sh -m .config {shlex.quote(virtual + '/requested.config')}
make olddefconfig
python3 {shlex.quote(virtual + '/check_kernel_config.py')} {shlex.quote(virtual + '/requested.config')} .config --source .
make prepare
test "$(make -s kernelrelease)" = {RELEASE}
cp .config {shlex.quote(virtual + '/resolved.config')}
cc --version
''')
        source = base / 'linux-7.1.8'
        if digest(source / '.config') != digest(base / 'resolved.config'):
            raise ValueError('Resolved kernel configuration changed')
        native('build', 'cd ' + shlex.quote(directory) + '; make -j2')
        native('private-modules', f'''cd {shlex.quote(directory)}
make INSTALL_MOD_PATH={shlex.quote(virtual + '/stage')} modules_install
for name in build source; do
 link={shlex.quote(virtual + '/stage/lib/modules/' + RELEASE)}/$name
 if test -e "$link" || test -L "$link"; then
  test -L "$link"
  test "$(readlink "$link")" = {shlex.quote(directory)}
  rm "$link"
 fi
done
depmod -b {shlex.quote(virtual + '/stage')} {RELEASE}
''')
        native('artifacts', f'''cd {shlex.quote(directory)}
grub-file --is-x86-linux arch/x86/boot/bzImage
grub-file --is-x86_64-efi arch/x86/boot/bzImage
test "$(make -s kernelrelease)" = {RELEASE}
python3 {shlex.quote(virtual + '/check_kernel_config.py')} {shlex.quote(virtual + '/requested.config')} .config --source .
modinfo -b {shlex.quote(virtual + '/stage')} -k {RELEASE} -F vermagic dummy
test "$(modinfo -b {shlex.quote(virtual + '/stage')} -k {RELEASE} -F vermagic dummy | cut -d' ' -f1)" = {RELEASE}
''', 120)
        if digest(status) != inputs['native_status_sha256']:
            raise ValueError('Installed package database changed during experiment')
        if digest(source / '.config') != digest(base / 'resolved.config'):
            raise ValueError('Final configuration differs')
        for name, sha in inputs['files'].items():
            if digest(base / name) != sha:
                raise ValueError('Input changed during experiment')
        paths = [source / name for name in ('arch/x86/boot/bzImage', 'vmlinux', 'System.map', '.config')]
        paths += sorted((base / 'stage').rglob('*.ko'))
        if not any(path.name == 'dummy.ko' for path in paths):
            raise ValueError('Expected actual dummy module missing')
        save(base / 'result.json', {'complete': True, 'release': RELEASE,
             'source_sha256': SOURCE_SHA, 'inputs_sha256': digest(base / 'inputs.json'),
             'native_status_unchanged': True, 'installed': False, 'boot_validated': False,
             'milestone_accepted': False,
             'files': {str(p.relative_to(base)): {'sha256': digest(p), 'size': p.stat().st_size} for p in paths}})
        exit_code = 0
    except BaseException as error:
        save(attempt / 'error.json', {'error': str(error)})
        traceback.print_exc()
    finally:
        save(attempt / 'driver.exit.json', {'exit': exit_code})
    return exit_code


if __name__ == '__main__':
    sys.exit(main())
