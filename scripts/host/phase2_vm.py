#!/usr/bin/env python3
"""Run Phase 2 in writable overlays over read-only cold foundation disks."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import shutil
import stat
import time

import vm

ROOT = vm.ROOT
WORK = vm.VM / 'phase2'
NAME = 'toddy-phase2'
KERNEL_SCRATCH_BYTES = 768 * 1024**2


def kernel_scratch_arguments():
    """Attach only the recorded preallocated project file, never another path."""
    receipt = WORK / 'kernel-landlock-scratch.json'
    disk = WORK / 'kernel-landlock-scratch.raw'
    if receipt.is_symlink() or disk.is_symlink():
        raise ValueError('Scratch symlink forbidden')
    if not receipt.exists() and not disk.exists():
        return []
    if not receipt.is_file() or not disk.is_file():
        raise ValueError('Reconcile incomplete scratch preparation')
    rs, ds = receipt.stat(), disk.stat()
    if rs.st_uid != os.getuid() or rs.st_nlink != 1 or rs.st_size > 65536:
        raise ValueError('Unsafe scratch receipt')
    row = json.loads(receipt.read_text())
    if (row.get('state') != 'prepared' or row.get('filename') != disk.name
            or row.get('format') != 'raw' or row.get('bytes') != KERNEL_SCRATCH_BYTES
            or row.get('serial') != 'TODDY-B02-KERNEL'):
        raise ValueError('Unexpected scratch declaration')
    if (not stat.S_ISREG(ds.st_mode) or ds.st_uid != os.getuid() or ds.st_nlink != 1
            or ds.st_mode & 0o077 or ds.st_size != KERNEL_SCRATCH_BYTES
            or ds.st_blocks * 512 < ds.st_size
            or ds.st_dev != row.get('device') or ds.st_ino != row.get('inode')):
        raise ValueError('Scratch identity/allocation mismatch')
    return ['-drive', 'file=/vm/phase2/kernel-landlock-scratch.raw,if=none,id=b02kernel,format=raw,discard=ignore',
            '-device', 'virtio-blk-pci,drive=b02kernel,serial=TODDY-B02-KERNEL']


def run(*args, **kwargs):
    return subprocess.run(args, check=True, **kwargs)


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def tool(*args):
    return run('docker', 'run', '--rm', '--user', f'{os.getuid()}:{os.getgid()}',
               '--cap-drop=ALL', '--security-opt=no-new-privileges',
               '-v', f'{vm.VM}:/vm:ro', '-v', f'{WORK}:/vm/phase2', vm.IMAGE,
               *args, capture_output=True, text=True)


def ssh_args():
    return ['ssh', '-i', str(vm.VM / 'id_ed25519'), '-p', '2223',
            '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10',
            '-o', 'StrictHostKeyChecking=accept-new',
            '-o', f'UserKnownHostsFile={WORK}/known_hosts', 'root@127.0.0.1']


def require_quiescent():
    running = run('docker', 'ps', '--format', '{{.Names}}', capture_output=True, text=True)
    if any(n.startswith('toddy-') for n in running.stdout.splitlines()):
        raise SystemExit('Stop project VMs before Phase 2 prepare/start')


def backing_identity(path):
    st = path.stat()
    return {'bytes': st.st_size, 'mtime_ns': st.st_mtime_ns,
            'device': st.st_dev, 'inode': st.st_ino}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['prepare', 'start', 'ssh', 'stop', 'inspect'])
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if vm.VM.is_symlink() or vm.VM.resolve() != vm.VM:
        raise SystemExit('Unsafe foundation storage')
    WORK.mkdir(mode=0o700, exist_ok=True)
    if WORK.is_symlink() or WORK.resolve() != WORK:
        raise SystemExit('Unsafe Phase 2 storage')
    review = json.loads((ROOT / 'status.json').read_text())['owner_review']
    if review.get('phase_2_approved') is not True or not (ROOT / review['approval_evidence']).is_file():
        raise SystemExit('Explicit recorded Phase 2 approval required')
    if args.action == 'prepare':
        # Refuse all running project QEMU containers, not just the historical name.
        require_quiescent()
        if any(WORK.iterdir()):
            raise SystemExit('Existing Phase 2 state: inspect; never replay prepare')
        receipt = {'source_commit': run('git', '-C', str(ROOT), 'rev-parse', 'HEAD',
                   capture_output=True, text=True).stdout.strip(), 'disks': {}}
        for filename in ('builder-base.img', 'builder.qcow2', 'lfs-target.qcow2', 'seed.img'):
            path = vm.VM / filename
            if path.is_symlink() or not path.is_file():
                raise SystemExit('Backing input must be a regular local image')
            started = time.monotonic()
            before = backing_identity(path)
            row = {'sha256': digest(path), 'bytes': path.stat().st_size}
            if before != backing_identity(path):
                raise SystemExit('Backing image changed while hashing')
            row['identity'] = before
            row['hash_seconds'] = round(time.monotonic() - started, 3)
            if filename.endswith('.qcow2'):
                row['check'] = tool('qemu-img', 'check', '/vm/' + filename).stdout.strip()
            receipt['disks'][filename] = row
        if receipt['disks']['builder-base.img']['sha256'] != json.loads(
                (ROOT / 'config/build-host.lock.json').read_text())['image_sha256']:
            raise SystemExit('Build-host base hash mismatch')
        # Receipt precedes creation so partial preparation is inspectable, never hidden.
        pending = WORK / 'backing.json.part'
        pending.write_text(json.dumps(receipt, indent=2) + '\n')
        for filename in ('builder.qcow2', 'lfs-target.qcow2'):
            tool('qemu-img', 'create', '-f', 'qcow2', '-F', 'qcow2',
                 '-b', '/vm/' + filename, '/vm/phase2/' + filename)
        pending.replace(WORK / 'backing.json')
        print(json.dumps(receipt, indent=2))
    elif args.action == 'start':
        require_quiescent()
        if not (WORK / 'backing.json').is_file() or (WORK / 'backing.json.part').exists():
            raise SystemExit('Complete cold-backing receipt required')
        receipt = json.loads((WORK / 'backing.json').read_text())
        for filename, row in receipt['disks'].items():
            path = vm.VM / filename
            if path.is_symlink() or row['identity'] != backing_identity(path):
                raise SystemExit('Backing identity changed: reconcile/re-hash before start')
        reserve = json.loads((ROOT / 'config/build-host.lock.json').read_text())['host_free_reserve_gib']
        if shutil.disk_usage(WORK).free < reserve * 1024**3:
            raise SystemExit('Host free-space reserve unavailable')
        for filename in ('builder.qcow2', 'lfs-target.qcow2'):
            if (WORK / filename).is_symlink() or not (WORK / filename).is_file():
                raise SystemExit('Missing or unsafe overlay')
        run('docker', 'run', '-d', '--name', NAME,
            '--user', f'{os.getuid()}:{os.getgid()}', '--device', '/dev/kvm',
            '--group-add', str(Path('/dev/kvm').stat().st_gid),
            '--cap-drop=ALL', '--security-opt=no-new-privileges',
            '--memory', '14g', '--cpus', '12', '-p', '127.0.0.1:2223:2223',
            '-v', f'{vm.VM}:/vm:ro', '-v', f'{WORK}:/vm/phase2', vm.IMAGE,
            'qemu-system-x86_64', '-enable-kvm', '-machine', 'q35', '-cpu', 'host',
            '-smp', '12', '-m', '12288', '-display', 'none',
            '-serial', 'file:/vm/phase2/serial.log',
            '-qmp', 'unix:/vm/phase2/qmp.sock,server=on,wait=off',
            '-drive', 'file=/vm/phase2/builder.qcow2,if=none,id=builder,format=qcow2',
            '-device', 'virtio-blk-pci,drive=builder,serial=TODDY-BUILDER',
            '-drive', 'file=/vm/phase2/lfs-target.qcow2,if=none,id=lfs,format=qcow2,discard=unmap',
            '-device', 'virtio-blk-pci,drive=lfs,serial=TODDY-LFS-TARGET',
            '-drive', 'file=/vm/seed.img,if=virtio,format=raw,readonly=on',
            '-netdev', 'user,id=net0,hostfwd=tcp:0.0.0.0:2223-:22',
            '-device', 'virtio-net-pci,netdev=net0', *kernel_scratch_arguments())
    elif args.action == 'ssh':
        run(*ssh_args(), *args.command)
    elif args.action == 'stop':
        run(*ssh_args(), 'poweroff')
        run('docker', 'wait', NAME)
        run('docker', 'rm', NAME)
    else:
        run('docker', 'inspect', '--format', '{{.State.Status}} {{.State.ExitCode}}', NAME)
        print(tool('qemu-img', 'info', '--force-share', '--backing-chain',
                   '/vm/phase2/lfs-target.qcow2').stdout)


if __name__ == '__main__':
    main()
