#!/usr/bin/env python3
"""Build the frozen shared ISO stack in a private prefix, never install a package."""
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
            or not base.name.startswith('libburnia-native-') or base.stat().st_mode & 0o077):
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
    command = ['chroot', str(root), '/usr/bin/env', '-i', 'HOME=' + native_base,
               'LC_ALL=C.UTF-8', 'PATH=' + prefix + '/bin:/usr/bin:/usr/sbin',
               'PKG_CONFIG_PATH=' + prefix + '/lib/pkgconfig',
               'CPPFLAGS=-I' + prefix + '/include', 'LDFLAGS=-L' + prefix + '/lib',
               'LD_LIBRARY_PATH=' + prefix + '/lib', 'PYTHONDONTWRITEBYTECODE=1']
    result = {'native_package_installed': False, 'milestone_accepted': False,
              'native_kernel_boot_verified': False, 'stages': []}
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

        for package, suffix, options in (
                ('libburn', '', ['--disable-libcdio']),
                ('libisofs', '.pl02', ['--disable-libjte']),
                ('libisoburn', '.pl02', ['--enable-pkg-check-modules',
                                       '--disable-libjte', '--disable-libcdio'])):
            source_root = package + '-1.5.8'
            archive = base / (source_root + suffix + '.tar.gz')
            with tarfile.open(archive) as source:
                for member in source.getmembers():
                    tarfile.data_filter(member, base)
                    if Path(member.name).parts[0] != source_root:
                        raise ValueError('Unexpected source root')
                source.extractall(base, filter='data')
            if package == 'libisoburn':
                # Frozen libisofs already prefers Glibc's sys/xattr.h. This old
                # configure check must probe that real header too, not cache a
                # fabricated successful check for removed attr/xattr.h.
                for filename in ('configure', 'configure.ac'):
                    path = base / source_root / filename
                    text = path.read_text()
                    if 'attr/xattr.h' not in text:
                        raise ValueError('Frozen xattr header check differs')
                    original = path.stat()
                    path.write_text(text.replace('attr/xattr.h', 'sys/xattr.h'))
                    # Both shipped input and generated configure are patched;
                    # do not request regeneration with upstream Automake 1.14.
                    os.utime(path, ns=(original.st_atime_ns, original.st_mtime_ns))
            directory = native_base + '/' + source_root
            if package == 'libisoburn':
                stage('symlink-metadata-patch', ['/usr/bin/patch', '--batch', '--fuzz=0',
                      '-d', directory, '-p1', '-i', native_base + '/libisoburn-symlink-metadata.patch'])
            configure = ['./configure', '--prefix=' + prefix, '--disable-static',
                         '--disable-ldconfig-at-install', *options]
            stage(package + '-configure', ['/usr/bin/bash', '-c',
                  'cd ' + shlex.quote(directory) + ' && exec ' + shlex.join(configure)])
            generated = (base / source_root / 'Makefile').read_text()
            if package != 'libburn':
                for feature in ('Libisofs_with_aaip_acL', 'Libisofs_with_aaip_xattR', 'Libisofs_with_zliB'):
                    if '-D' + feature not in generated:
                        raise ValueError('Missing ISO metadata feature: ' + feature)
            if package == 'libisoburn' and '-DXorriso_with_readlinE' not in generated:
                raise ValueError('Missing native Readline support')
            stage(package + '-build', ['/usr/bin/make', '-C', directory, '-j2'])
            stage(package + '-private-install', ['/usr/bin/make', '-C', directory, 'install'])
        stage('version', [prefix + '/bin/xorriso', '-no_rc', '-version'])
        version = (base / 'version.log').read_text()
        for label in ('xorriso version', 'libisofs', 'libburn', 'libisoburn'):
            if not any(label in line and '1.5.8' in line for line in version.splitlines()):
                raise ValueError('Unexpected runtime version: ' + label)
        stage('linkage', ['/usr/bin/ldd', prefix + '/bin/xorriso'])
        linkage = (base / 'linkage.log').read_text()
        for library in ('libburn.so', 'libisofs.so', 'libisoburn.so'):
            if not any(library in line and '=> ' + prefix + '/lib/' in line for line in linkage.splitlines()):
                raise ValueError('Private shared provider not resolved: ' + library)
        stage('roundtrip', ['/usr/bin/python3', native_base + '/iso-roundtrip.py',
                            '--evidence-directory', native_base + '/evidence'])
        if digest(root / 'var/lib/dpkg/status') != before:
            raise ValueError('Installed native package status changed')
        for name, sha in spec['files'].items():
            if digest(base / name) != sha:
                raise ValueError('Private probe input changed')
        result.update(complete=True, installed_status_unchanged=True,
                      xorriso_sha256=digest(base / 'prefix/bin/xorriso'),
                      iso_evidence=json.loads((base / 'evidence/iso-roundtrip.json').read_text()),
                      shared_libraries={path.name: digest(path) for path in
                          (base / 'prefix/lib').glob('*.so.*') if not path.is_symlink()})
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
