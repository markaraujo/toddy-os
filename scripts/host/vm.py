#!/usr/bin/env python3
"""Manage the dedicated build VM; never attach physical host disks."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
VM = ROOT / '.local/vm'
IMAGE = 'toddy-qemu:h01'
NAME = 'toddy-builder'


def run(*args, **kwargs):
    return subprocess.run(args, check=True, **kwargs)


def require_phase2_inactive():
    # Original disks are cold backing inputs while Phase 2 overlays are running.
    # Docker errors must fail closed, never authorize a restore/start by absence.
    result = run('docker', 'ps', '--filter', 'name=^/toddy-phase2$',
                 '--format', '{{.Names}}', capture_output=True, text=True)
    if result.stdout.strip():
        raise SystemExit('Phase 2 VM is running: preserve its cold foundation backing disks')


def qemu_tool(*args):
    run('docker', 'run', '--rm', '--user', f'{os.getuid()}:{os.getgid()}',
        '--cap-drop=ALL', '--security-opt=no-new-privileges',
        '-v', f'{VM}:/vm', IMAGE, *args)


def ssh_args():
    return ['ssh', '-i', str(VM / 'id_ed25519'), '-p', '2222',
            '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10',
            '-o', 'StrictHostKeyChecking=accept-new',
            '-o', f'UserKnownHostsFile={VM}/known_hosts', 'root@127.0.0.1']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['prepare', 'start', 'ssh', 'stop', 'inspect'])
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if args.action in ('prepare', 'start'):
        require_phase2_inactive()
    VM.mkdir(parents=True, exist_ok=True, mode=0o700)
    if VM.is_symlink() or VM.resolve() != VM:
        raise SystemExit('VM storage must be a real directory inside this checkout')
    if args.action == 'prepare':
        # The downloaded base is checked separately against Ubuntu SHA256SUMS.
        if not (VM / 'builder-base.img').is_file():
            raise SystemExit('Download and verify the Ubuntu build-host image first')
        sums = (VM / 'SHA256SUMS').read_text().splitlines()
        expected = [line.split()[0] for line in sums
                    if line.split()[-1].lstrip('*') == 'ubuntu-24.04-server-cloudimg-amd64.img']
        with (VM / 'builder-base.img').open('rb') as source:
            actual = hashlib.file_digest(source, 'sha256').hexdigest()
        locked = json.loads((ROOT / 'config/build-host.lock.json').read_text())
        if expected != [actual] or actual != locked['image_sha256']:
            raise SystemExit('Ubuntu build-host image integrity mismatch')
        if not (VM / 'id_ed25519').exists():
            run('ssh-keygen', '-q', '-t', 'ed25519', '-N', '', '-f', str(VM / 'id_ed25519'))
        pubkey = (VM / 'id_ed25519.pub').read_text().strip()
        (VM / 'user-data').write_text(
            '#cloud-config\nhostname: toddy-builder\nmanage_etc_hosts: true\n'
            'disable_root: false\nssh_pwauth: false\n'
            'ssh_authorized_keys:\n  - ' + pubkey + '\n')
        (VM / 'meta-data').write_text('instance-id: toddy-builder-h01\nlocal-hostname: toddy-builder\n')
        if not (VM / 'seed.img').exists():
            qemu_tool('cloud-localds', '/vm/seed.img', '/vm/user-data', '/vm/meta-data')
        if not (VM / 'builder.qcow2').exists():
            qemu_tool('qemu-img', 'create', '-f', 'qcow2', '-F', 'qcow2',
                      '-b', '/vm/builder-base.img', '/vm/builder.qcow2', '32G')
        if not (VM / 'lfs-target.qcow2').exists():
            qemu_tool('qemu-img', 'create', '-f', 'qcow2', '/vm/lfs-target.qcow2', '180G')
    elif args.action == 'start':
        if (VM / 'restore-in-progress.json').exists():
            raise SystemExit('Incomplete checkpoint restore; finish it before VM start')
        for name in ['builder.qcow2', 'lfs-target.qcow2', 'seed.img']:
            if not (VM / name).is_file() or (VM / name).is_symlink():
                raise SystemExit(f'Missing or unsafe VM file: {name}')
        run('docker', 'run', '-d', '--name', NAME,
            '--user', f'{os.getuid()}:{os.getgid()}', '--device', '/dev/kvm',
            '--group-add', str(Path('/dev/kvm').stat().st_gid),
            '--cap-drop=ALL', '--security-opt=no-new-privileges',
            '--memory', '14g', '--cpus', '12',
            '-p', '127.0.0.1:2222:2222', '-v', f'{VM}:/vm', IMAGE,
            'qemu-system-x86_64', '-enable-kvm', '-machine', 'q35', '-cpu', 'host',
            '-smp', '12', '-m', '12288', '-display', 'none',
            '-serial', 'file:/vm/serial.log',
            '-qmp', 'unix:/vm/qmp.sock,server=on,wait=off',
            '-drive', 'file=/vm/builder.qcow2,if=none,id=builder,format=qcow2',
            '-device', 'virtio-blk-pci,drive=builder,serial=TODDY-BUILDER',
            '-drive', 'file=/vm/lfs-target.qcow2,if=none,id=lfs,format=qcow2',
            '-device', 'virtio-blk-pci,drive=lfs,serial=TODDY-LFS-TARGET',
            '-drive', 'file=/vm/seed.img,if=virtio,format=raw,readonly=on',
            '-netdev', 'user,id=net0,hostfwd=tcp:0.0.0.0:2222-:22',
            '-device', 'virtio-net-pci,netdev=net0')
    elif args.action == 'ssh':
        run(*ssh_args(), *args.command)
    elif args.action == 'stop':
        run(*ssh_args(), 'poweroff')
        run('docker', 'wait', NAME)
        run('docker', 'rm', NAME)
    elif args.action == 'inspect':
        run('docker', 'inspect', '--format', '{{.State.Status}} {{.State.ExitCode}}', NAME)
        qemu_tool('qemu-img', 'info', '--force-share', '/vm/lfs-target.qcow2')


if __name__ == '__main__':
    main()
