#!/usr/bin/env python3
"""Prepare a tiny native diagnostic initramfs from a terminal private kernel."""
import base64
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def prepare(kernel, source, token):
    root = Path('/mnt/lfs')
    if (kernel.resolve() != kernel or kernel.parent != root / 'sources/recovery'
            or not kernel.name.startswith('kernel-native-') or kernel.stat().st_mode & 0o077
            or kernel.stat().st_uid != 0):
        raise ValueError('Protected private kernel fixture required')
    pid = int((kernel / 'driver.pid').read_text())
    proc = Path('/proc') / str(pid)
    if proc.exists() and (proc / 'stat').read_text().rsplit(')', 1)[1].split()[0] != 'Z':
        raise ValueError('Kernel driver is still live')
    attempts = sorted((kernel / 'attempts').iterdir())
    if json.loads((attempts[-1] / 'driver.exit.json').read_text()) != {'exit': 0}:
        raise ValueError('Actual terminal kernel exit is not zero')
    built = json.loads((kernel / 'result.json').read_text())
    inputs = json.loads((kernel / 'inputs.json').read_text())
    if (built.get('complete') is not True or built.get('release') != '7.1.8-toddy'
            or built.get('installed') is not False or built.get('boot_validated') is not False
            or built.get('inputs_sha256') != digest(kernel / 'inputs.json')
            or built.get('source_sha256') != 'ff01dcb449279d5b4cfccdb01fee639cf5ff1803f1749a77844dd33915422c49'
            or digest(root / 'var/lib/dpkg/status') != inputs['native_status_sha256']):
        raise ValueError('Private kernel evidence differs')
    for name, sha in inputs['files'].items():
        if Path(name).name != name or digest(kernel / name) != sha:
            raise ValueError('Private kernel input changed')
    for name, record in built['files'].items():
        path = kernel / name
        if path.resolve() != path or not path.is_relative_to(kernel) or digest(path) != record['sha256']:
            raise ValueError('Private kernel artifact changed')
    for name in ('source', 'configure', 'build', 'private-modules', 'artifacts'):
        stage = json.loads((kernel / 'completed' / (name + '.json')).read_text())
        if stage['exit'] != 0 or stage['timed_out'] or digest(kernel / stage['log']) != stage['log_sha256']:
            raise ValueError('Kernel stage exit/log differs')
    modules = [kernel / name for name in built['files'] if Path(name).name == 'dummy.ko']
    if len(modules) != 1:
        raise ValueError('Exactly one staged native dummy module required')
    if len(token) != 32 or any(c not in '0123456789abcdef' for c in token):
        raise ValueError('Private invocation token required')
    base = Path(tempfile.mkdtemp(prefix='kernel-smoke-', dir=root / 'sources/recovery'))
    print('PRIVATE_KERNEL_SMOKE_FIXTURE ' + str(base), file=sys.stderr, flush=True)
    (base / 'init.c').write_bytes(source)
    stage = base / 'runtime'
    stage.mkdir()
    for name in ('dev', 'proc', 'sys', 'tmp'):
        (stage / name).mkdir()
    shutil.copyfile(modules[0], stage / 'dummy.ko')
    shutil.copyfile(kernel / 'linux-7.1.8/arch/x86/boot/bzImage', base / 'bzImage')
    native = '/' + str(base.relative_to(root))
    commands = [
        ['gcc', '-static', '-O2', '-Wall', '-Wextra', '-Werror', '-DPROBE_TOKEN="' + token + '"',
         native + '/init.c', '-o', native + '/runtime/init'],
        ['readelf', '-l', native + '/runtime/init'],
        ['bash', '-euc', 'cd ' + shlex.quote(native + '/runtime')
         + '; printf "%s\\0" dev dummy.ko init proc sys tmp | bsdcpio -o --null --format=newc --owner 0:0 --quiet > ../initramfs.cpio'],
        ['bash', '-euc', 'gzip -n -c ' + shlex.quote(native + '/initramfs.cpio')
         + ' > ' + shlex.quote(native + '/initramfs.cpio.gz')],
    ]
    for number, argv in enumerate(commands):
        run = subprocess.run(['chroot', str(root), '/usr/bin/env', '-i', 'PATH=/usr/bin:/usr/sbin', 'LC_ALL=C',
                              *argv], capture_output=True, timeout=60)
        (base / f'{number}.stdout').write_bytes(run.stdout)
        (base / f'{number}.stderr').write_bytes(run.stderr)
        (base / f'{number}.exit').write_text(str(run.returncode) + '\n')
        run.check_returncode()
        if number == 1 and b'INTERP' in run.stdout:
            raise ValueError('Diagnostic init must be linked to the native static libc')
    if digest(root / 'var/lib/dpkg/status') != inputs['native_status_sha256']:
        raise ValueError('Native package state changed during preparation')
    result = {'fixture': str(base), 'token': token, 'kernel_fixture': str(kernel),
              'kernel_result_sha256': digest(kernel / 'result.json'),
              'files': {name: digest(base / name) for name in ('init.c', 'bzImage', 'initramfs.cpio.gz')},
              'init_sha256': digest(stage / 'init'), 'module_sha256': digest(stage / 'dummy.ko'),
              'kernel_boot_verified': False, 'foundation_accepted': False}
    (base / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


if __name__ == '__main__':
    subprocess.run(['bash', '-c', 'source /opt/toddy-build/scripts/build/target.sh; guard_target'], check=True)
    request = json.loads(sys.stdin.read())
    print(json.dumps(prepare(Path(request['kernel']), base64.b64decode(request['source']), request['token'])))
