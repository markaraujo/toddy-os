#!/usr/bin/env python3
"""Boot-only probe supplied to a disposable VM through system credentials.

Never install this program or its unit into the distributable root filesystem.
Its guards precede all writes/module operations. Login and ISO/installer tests
remain separate requirements even when this probe succeeds.
"""
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile


def run(*arguments):
    result = subprocess.run(arguments, capture_output=True, text=True, timeout=60)
    if result.returncode:
        print(json.dumps({'command': arguments, 'exit': result.returncode,
                          'stdout': result.stdout, 'stderr': result.stderr}), flush=True)
        result.check_returncode()
    return result.stdout.strip()


def main():
    if os.geteuid() != 0 or os.uname().release != '7.1.8-toddy':
        raise RuntimeError('Requires root inside the booted Toddy 7.1.8 target')
    if Path('/proc/1/comm').read_text().strip() != 'systemd':
        raise RuntimeError('Requires native Systemd PID 1')
    virtualization = run('systemd-detect-virt', '--vm')
    if virtualization not in {'kvm', 'qemu'}:
        raise RuntimeError('Requires the designated QEMU/KVM test guest')
    source = run('findmnt', '-n', '-o', 'SOURCE', '/')
    if not re.fullmatch(r'/dev/[a-z0-9]+', source):
        raise RuntimeError('Unexpected native root block device')
    parent = run('lsblk', '-ndo', 'PKNAME', source)
    if not re.fullmatch(r'[a-z0-9]+', parent):
        raise RuntimeError('Unexpected native root parent')
    if run('lsblk', '-dnro', 'SERIAL', '/dev/' + parent) != 'TODDY-BOOT-TEST':
        raise RuntimeError('Refusing a disk outside the disposable boot test')
    if run('findmnt', '-n', '-o', 'FSTYPE', '/') != 'ext4':
        raise RuntimeError('Unexpected native root filesystem')
    if run('blkid', '-s', 'LABEL', '-o', 'value', source) != 'TODDY_LFS':
        raise RuntimeError('Unexpected native root label')
    if Path('/sys/module/dummy').exists():
        raise RuntimeError('Preserve unexpectedly preloaded dummy module')

    with tempfile.TemporaryDirectory(prefix='toddy-native-boot-') as directory:
        root = Path(directory)
        program = root / 'probe.c'
        program.write_text('#include <stdio.h>\nint main(void) {\n'
                           'puts("TODDY_NATIVE_C_OK"); return 0;\n}\n')
        binary = root / 'probe'
        run('cc', '-Werror', '-O2', str(program), '-o', str(binary))
        if run(str(binary)) != 'TODDY_NATIVE_C_OK':
            raise RuntimeError('Native compiled C execution failed')
        linkage = run('ldd', str(binary))
        if '/tools/' in linkage or '/sources/' in linkage:
            raise RuntimeError('Temporary paths remain in native linkage')
        if '/lib64/ld-linux-x86-64.so.2' not in linkage:
            raise RuntimeError('Expected native dynamic loader not found')
        loaded = False
        try:
            run('modprobe', 'dummy', 'numdummies=1')
            loaded = True
            if not Path('/sys/module/dummy').exists() or not Path('/sys/class/net/dummy0').exists():
                raise RuntimeError('Native dummy module/interface did not appear')
        finally:
            if loaded:
                run('modprobe', '-r', 'dummy')
        if Path('/sys/module/dummy').exists() or Path('/sys/class/net/dummy0').exists():
            raise RuntimeError('Native dummy module/interface did not unload')
    result = {'kernel': os.uname().release, 'pid1': 'systemd',
              'virtualization': virtualization, 'root_source': source,
              'firmware': 'uefi' if Path('/sys/firmware/efi').is_dir() else 'bios',
              'native_c_execution': True, 'native_linkage': linkage,
              'dummy_load_unload': True, 'login_validated': False,
              'iso_validated': False, 'installer_validated': False}
    print('TODDY_NATIVE_BOOT_OK ' + json.dumps(result, sort_keys=True), flush=True)


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print('TODDY_NATIVE_BOOT_FAIL ' + str(error), flush=True)
        raise
