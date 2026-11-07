"""Native BIOS/EFI hybrid composition shared by private probes and release CLI.

The caller verifies tool/payload provenance and owns milestone/build locks.
This component verifies media readback, not kernel execution or release safety.
"""
import hashlib
import os
from pathlib import Path, PurePosixPath
import re
import stat


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def live_configuration():
    return '''# Toddy OS source-built foundation; live writes are volatile.
set default=0
set timeout=5
serial --unit=0 --speed=115200 --word=8 --parity=no --stop=1
terminal_input console serial
terminal_output console serial
menuentry "Toddy OS live (volatile session)" {
    linux /boot/vmlinuz-7.1.8-toddy toddy.live console=tty0 console=ttyS0,115200n8
    initrd /boot/initramfs.cpio.gz
}
menuentry "Toddy OS early recovery shell" {
    linux /boot/vmlinuz-7.1.8-toddy toddy.live toddy.rescue console=tty0 console=ttyS0,115200n8
    initrd /boot/initramfs.cpio.gz
}
'''


def compose(root, work, stage, *, mtools='/usr', xorriso='/usr/bin/xorriso',
            marker='/.toddy-media-id', volume='TODDY_OS', filename='toddy.iso'):
    root, work = Path(root), Path(work)
    if (os.geteuid() != 0 or root.resolve() != root or work.resolve() != work
            or not any(work != root / area and work.is_relative_to(root / area)
                       for area in ('tmp', 'sources/stage', 'sources/recovery'))
            or not work.is_dir() or work.stat().st_uid or work.stat().st_mode & 0o077):
        raise ValueError('Hybrid composition requires a private disposable-target generation')
    if (not re.fullmatch('[A-Z0-9_]{1,32}', volume)
            or not re.fullmatch('[a-z0-9][a-z0-9-]{0,60}\\.iso', filename)
            or not re.fullmatch('/[A-Za-z0-9_./-]+', marker)
            or marker.startswith('//')
            or '..' in PurePosixPath(marker).parts or PurePosixPath(marker).as_posix() != marker):
        raise ValueError('Noncanonical media identity, volume or artifact name')
    for program in (mtools, xorriso):
        if (not program.startswith('/') or program.startswith('//') or PurePosixPath(program).as_posix() != program
                or '..' in PurePosixPath(program).parts or any(c.isspace() for c in program)):
            raise ValueError('Native media tool path must be canonical')
    source = work / 'input'
    if source.resolve() != source or not source.is_dir():
        raise ValueError('Expected physical staged media payload')
    payload = {}
    for path in sorted(source.rglob('*')):
        info = path.lstat()
        if (info.st_dev != root.stat().st_dev or info.st_uid or info.st_gid
                or info.st_mode & 0o022 or not (stat.S_ISREG(info.st_mode) or stat.S_ISDIR(info.st_mode))):
            raise ValueError('Media input must contain only protected physical files/directories')
        if stat.S_ISREG(info.st_mode):
            payload[path.relative_to(source).as_posix()] = digest(path)
    if 'boot/grub/grub.cfg' not in payload or marker[1:] not in payload:
        raise ValueError('Media configuration or search identity is missing')
    for path in (source / 'boot/grub/i386-pc', source / 'efi.img', work / 'EFI',
                 work / 'early.cfg', work / filename, work / 'readback', work / 'efi-readback'):
        if path.exists() or path.is_symlink():
            raise ValueError('Preserve existing media assembly output')
    virtual = lambda path: '/' + path.relative_to(root).as_posix()
    native = virtual(work)
    early = work / 'early.cfg'
    early.write_text('search --no-floppy --file --set=root ' + marker + '\n'
                     'set prefix=($root)/boot/grub\n')
    (source / 'boot/grub/i386-pc').mkdir()
    (work / 'EFI/BOOT').mkdir(parents=True)
    stage('config', ['/usr/bin/grub-script-check', native + '/input/boot/grub/grub.cfg'])
    modules = ['iso9660', 'fat', 'part_gpt', 'part_msdos', 'normal', 'configfile',
               'search', 'search_fs_file', 'serial', 'terminal', 'cat', 'sleep',
               'halt', 'test', 'linux', 'reboot', 'echo']
    stage('bios-core', ['/usr/bin/grub-mkimage', '-O', 'i386-pc-eltorito',
                       '-p', '/boot/grub', '-c', native + '/early.cfg',
                       '-o', native + '/input/boot/grub/i386-pc/eltorito.img', 'biosdisk', *modules])
    stage('uefi-core', ['/usr/bin/grub-mkimage', '-O', 'x86_64-efi',
                       '-p', '/boot/grub', '-c', native + '/early.cfg',
                       '-o', native + '/EFI/BOOT/BOOTX64.EFI', *modules])
    stage('efi-format', ['/usr/bin/grub-file', '--is-x86_64-efi', native + '/EFI/BOOT/BOOTX64.EFI'])
    stage('fat-create', [mtools + '/bin/mformat', '-C', '-f', '2880', '-L', '16',
                       '-i', native + '/input/efi.img', '::'])
    stage('fat-copy', [mtools + '/bin/mcopy', '-s', '-i', native + '/input/efi.img', native + '/EFI', '::/'])
    stage('fat-readback', [mtools + '/bin/mcopy', '-i', native + '/input/efi.img',
                         '::/EFI/BOOT/BOOTX64.EFI', native + '/efi-readback'])
    if digest(work / 'efi-readback') != digest(work / 'EFI/BOOT/BOOTX64.EFI'):
        raise ValueError('Embedded EFI loader differs after FAT readback')
    stage('assemble', [xorriso, '-no_rc', '-as', 'mkisofs', '-R', '-V', volume,
                      '-o', native + '/' + filename,
                      '--grub2-mbr', '/usr/lib/grub/i386-pc/boot_hybrid.img', '--grub2-boot-info',
                      '-b', 'boot/grub/i386-pc/eltorito.img', '-c', 'boot/grub/boot.cat',
                      '-no-emul-boot', '-boot-load-size', '4', '-boot-info-table',
                      '--efi-boot', 'efi.img', '-efi-boot-part', '--efi-boot-image',
                      '--protective-msdos-label', native + '/input'])
    stage('catalog', [xorriso, '-no_rc', '-indev', 'stdio:' + native + '/' + filename,
                     '-report_el_torito', 'plain', '-report_system_area', 'plain', '-end'])
    if not all(term in (work / 'catalog.log').read_text() for term in ('BIOS', 'UEFI', 'GPT')):
        raise ValueError('Missing dual firmware/hybrid image catalog')
    # Verify immutable input bytes by reading them from the actual ISO. GRUB's
    # generated El Torito core receives documented boot-info patches separately.
    (work / 'readback').mkdir()
    for index, (name, sha) in enumerate(sorted(payload.items())):
        output = work / 'readback' / str(index)
        stage('readback-' + str(index), [xorriso, '-no_rc', '-indev', 'stdio:' + native + '/' + filename,
              '-osirrox', 'on', '-extract', '/' + name, virtual(output), '-end'])
        if digest(output) != sha or digest(source / name) != sha:
            raise ValueError('ISO payload readback or source stability differs: ' + name)
    artifact = work / filename
    return {'artifact': str(artifact), 'sha256': digest(artifact), 'bytes': artifact.stat().st_size,
            'payload_sha256': payload, 'efi_sha256': digest(work / 'EFI/BOOT/BOOTX64.EFI'),
            'payload_readback_verified': True, 'firmware_catalog_verified': True,
            'native_kernel_boot_verified': False, 'release_accepted': False}
