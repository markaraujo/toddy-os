#!/usr/bin/env python3
"""Assemble loader-only native GRUB media in private storage, never a release."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import tempfile


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def save(path, value):
    with path.open('x') as stream:
        stream.write(json.dumps(value, indent=2) + '\n')
        stream.flush()
        os.fsync(stream.fileno())


def verified_fixture(path, prefix):
    if (path.resolve() != path or path.parent != Path('/mnt/lfs/sources/recovery')
            or not path.name.startswith(prefix) or path.stat().st_uid
            or path.stat().st_mode & 0o077):
        raise ValueError('Protected completed native fixture required')
    if json.loads((path / 'driver.exit.json').read_text()) != {'exit': 0}:
        raise ValueError('Private driver did not succeed')
    result = json.loads((path / 'result.json').read_text())
    if not result.get('complete') or not result.get('installed_status_unchanged'):
        raise ValueError('Incomplete private native build')
    for name, sha in json.loads((path / 'inputs.json').read_text())['files'].items():
        if Path(name).name != name or digest(path / name) != sha:
            raise ValueError('Private native input changed')
    binaries = result.get('binaries', {})
    if prefix == 'libburnia-native-':
        binaries = {'xorriso': result['xorriso_sha256']}
        for name, sha in result['shared_libraries'].items():
            if Path(name).name != name or digest(path / 'prefix/lib' / name) != sha:
                raise ValueError('Private ISO library changed')
    for name, sha in binaries.items():
        if Path(name).name != name or digest(path / 'prefix/bin' / name) != sha:
            raise ValueError('Private native executable changed')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mtools', type=Path)
    parser.add_argument('libburnia', type=Path)
    args = parser.parse_args()
    subprocess.run(['bash', '-c', 'source /opt/toddy-build/scripts/build/target.sh; guard_target'], check=True)
    verified_fixture(args.mtools, 'mtools-native-')
    verified_fixture(args.libburnia, 'libburnia-native-')
    accepted = json.loads(Path('/var/log/toddy/build/h07-grub.success.json').read_text())
    if accepted['recipe_exit'] or accepted['postcheck_exit']:
        raise ValueError('Native GRUB package is not accepted')
    grub_record = Path('/var/log/toddy/packages/grub_2.14-1_amd64.json')
    record = json.loads(grub_record.read_text())
    if not record['installed']:
        raise ValueError('Missing native GRUB provenance')
    root = Path('/mnt/lfs')
    owned = {root / name.lstrip('/'): meta['sha256'] for name, meta in record['payload'].items()
             if meta.get('sha256')}
    for path, sha in owned.items():
        if path.is_symlink() or digest(path) != sha:
            raise ValueError('Native GRUB payload differs: ' + str(path))
    before = digest(root / 'var/lib/dpkg/status')
    base = Path(tempfile.mkdtemp(prefix='grub-media-', dir=root / 'sources/recovery'))
    native = '/' + str(base.relative_to(root))
    mtools = '/' + str(args.mtools.relative_to(root)) + '/prefix'
    libburnia = '/' + str(args.libburnia.relative_to(root)) + '/prefix'
    token = os.urandom(12).hex()
    save(base / 'intent.json', {'pid': os.getpid(), 'token': token,
         'mtools_fixture': str(args.mtools), 'libburnia_fixture': str(args.libburnia),
         'grub_record_sha256': digest(grub_record), 'installed_status_sha256': before})
    result = {'fixture': str(base), 'token': token, 'release_iso': False,
              'kernel_included': False, 'native_boot_verified': False, 'stages': []}
    print('GRUB_MEDIA_FIXTURE ' + str(base), flush=True)
    code = 1
    try:
        source = base / 'input'
        (source / 'boot/grub').mkdir(parents=True)
        (source / 'probe-id').write_text('TODDY_GRUB_MEDIA_DATA ' + token + '\n')
        (source / 'boot/grub/grub.cfg').write_text(
            'serial --unit=0 --speed=115200\nterminal_input serial\nterminal_output serial\n'
            'echo TODDY_GRUB_MEDIA_EXEC platform=$grub_platform token=' + token + '\n'
            'cat /probe-id\nsleep 1\nhalt\n')
        wrapper = base / 'xorriso-no-rc'
        wrapper.write_text('#!/bin/bash\nexec ' + shlex.quote(libburnia + '/bin/xorriso') + ' -no_rc "$@"\n')
        wrapper.chmod(0o700)
        command = ['chroot', str(root), '/usr/bin/env', '-i', 'HOME=' + native,
                   'PATH=' + mtools + '/bin:/usr/bin:/usr/sbin', 'LC_ALL=C.UTF-8',
                   'LD_LIBRARY_PATH=' + libburnia + '/lib', 'MTOOLSRC=/dev/null']

        def stage(name, argv):
            save(base / (name + '.intent.json'), {'argv': argv, 'timeout_seconds': 120})
            with (base / (name + '.log')).open('x') as output:
                run = subprocess.run([*command, '/usr/bin/timeout', '--kill-after=5', '120', *argv],
                                     stdout=output, stderr=subprocess.STDOUT)
                output.flush()
                os.fsync(output.fileno())
            save(base / (name + '.exit.json'), {'exit': run.returncode})
            result['stages'].append({'name': name, 'exit': run.returncode,
                                    'log_sha256': digest(base / (name + '.log'))})
            if run.returncode:
                raise ValueError('Native media stage failed: ' + name)

        stage('config', ['/usr/bin/grub-script-check', native + '/input/boot/grub/grub.cfg'])
        # Follow frozen grub-mkrescue's BIOS/FAT/hybrid recipe explicitly.
        # Its unconditional Apple label renderer needs an unrelated font.
        # This x86_64 text profile has no Apple boot or graphical-label claim.
        early = base / 'early.cfg'
        early.write_text('search --no-floppy --file --set=root /probe-id\n'
                         'set prefix=($root)/boot/grub\n')
        (source / 'boot/grub/i386-pc').mkdir()
        (base / 'EFI/BOOT').mkdir(parents=True)
        modules = ['iso9660', 'fat', 'part_gpt', 'part_msdos', 'normal', 'configfile',
                   'search', 'search_fs_file', 'serial', 'terminal', 'cat', 'sleep',
                   'halt', 'test', 'linux', 'reboot', 'echo']
        stage('bios-core', ['/usr/bin/grub-mkimage', '-O', 'i386-pc-eltorito',
                            '-p', '/boot/grub', '-c', native + '/early.cfg',
                            '-o', native + '/input/boot/grub/i386-pc/eltorito.img',
                            'biosdisk', *modules])
        stage('uefi-core', ['/usr/bin/grub-mkimage', '-O', 'x86_64-efi',
                            '-p', '/boot/grub', '-c', native + '/early.cfg',
                            '-o', native + '/EFI/BOOT/BOOTX64.EFI', *modules])
        stage('efi-format', ['/usr/bin/grub-file', '--is-x86_64-efi', native + '/EFI/BOOT/BOOTX64.EFI'])
        stage('fat-create', [mtools + '/bin/mformat', '-C', '-f', '2880', '-L', '16',
                            '-i', native + '/input/efi.img', '::'])
        stage('fat-copy', [mtools + '/bin/mcopy', '-s', '-i', native + '/input/efi.img', native + '/EFI', '::/'])
        stage('assemble', [native + '/xorriso-no-rc', '-as', 'mkisofs', '-R', '-V', 'TODDY_PROBE',
                           '-o', native + '/loader-probe.iso',
                           '--grub2-mbr', '/usr/lib/grub/i386-pc/boot_hybrid.img', '--grub2-boot-info',
                           '-b', 'boot/grub/i386-pc/eltorito.img', '-c', 'boot/grub/boot.cat',
                           '-no-emul-boot', '-boot-load-size', '4', '-boot-info-table',
                           '--efi-boot', 'efi.img', '-efi-boot-part', '--efi-boot-image',
                           '--protective-msdos-label', native + '/input'])
        stage('catalog', [native + '/xorriso-no-rc', '-indev', 'stdio:' + native + '/loader-probe.iso',
                          '-report_el_torito', 'plain', '-report_system_area', 'plain', '-end'])
        stage('readback', [native + '/xorriso-no-rc', '-indev', 'stdio:' + native + '/loader-probe.iso',
                           '-osirrox', 'on', '-extract', '/probe-id', native + '/readback-id',
                           '-extract', '/boot/grub/grub.cfg', native + '/readback.cfg', '-end'])
        if ((base / 'readback-id').read_bytes() != (source / 'probe-id').read_bytes()
                or (base / 'readback.cfg').read_bytes() != (source / 'boot/grub/grub.cfg').read_bytes()):
            raise ValueError('Native ISO readback differs')
        catalog = (base / 'catalog.log').read_text()
        if not all(term in catalog for term in ('BIOS', 'UEFI', 'GPT')):
            raise ValueError('Missing dual firmware/hybrid image catalog')
        for path, sha in owned.items():
            if digest(path) != sha:
                raise ValueError('GRUB source state changed')
        verified_fixture(args.mtools, 'mtools-native-')
        verified_fixture(args.libburnia, 'libburnia-native-')
        if digest(root / 'var/lib/dpkg/status') != before:
            raise ValueError('Installed package status changed')
        result.update(complete=True, iso_sha256=digest(base / 'loader-probe.iso'),
                      iso_size=(base / 'loader-probe.iso').stat().st_size,
                      installed_status_unchanged=True, grub_payload_unchanged=True)
        code = 0
    except BaseException as error:
        result.update(complete=False, error=str(error))
        raise
    finally:
        save(base / 'result.json', result)
        save(base / 'driver.exit.json', {'exit': code})
        print(json.dumps(result), flush=True)


if __name__ == '__main__':
    main()
