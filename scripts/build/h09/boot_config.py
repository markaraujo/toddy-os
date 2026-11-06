#!/usr/bin/env python3
"""Render the LFS 13.1 direct-root boot entry from measured UUIDs.

This module does not install GRUB or write to a disk. The eventual H09
dispatcher must supply UUIDs obtained after the existing target guards pass.
"""
import re
import sys


def render(filesystem_uuid, partition_uuid):
    for identifier in (filesystem_uuid, partition_uuid):
        if not re.fullmatch(r'[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}', identifier):
            raise ValueError('Expected an ext4/GPT UUID, with no GRUB syntax')
    return f'''# Toddy OS: LFS 13.1-systemd direct-root builder boot
# Generated from the designated disposable target, never workstation disks.
set default=0
set timeout=5
insmod part_gpt
insmod ext2
insmod search_fs_uuid
serial --unit=0 --speed=115200 --word=8 --parity=no --stop=1
terminal_input console serial
terminal_output console serial
search --no-floppy --fs-uuid --set=root {filesystem_uuid.lower()}
set gfxpayload=1024x768x32
menuentry "Toddy OS, Linux 7.1.8-toddy" {{
    linux /boot/vmlinuz-7.1.8-toddy root=PARTUUID={partition_uuid.lower()} rootwait ro console=tty0 console=ttyS0,115200n8
}}
'''


if __name__ == '__main__':
    if len(sys.argv) != 3:
        raise SystemExit('Usage: boot_config.py FILESYSTEM_UUID GPT_PARTITION_UUID')
    print(render(*sys.argv[1:]), end='')
