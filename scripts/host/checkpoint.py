#!/usr/bin/env python3
"""Save/restore a verified pair of cold VM disks; never touches physical disks."""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('toddy_vm', ROOT / 'scripts/host/vm.py')
vm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vm)
FOLDER = vm.VM / 'checkpoints'
RESTORING = vm.VM / 'restore-in-progress.json'
DISKS = {'builder': 'builder.qcow2', 'target': 'lfs-target.qcow2'}


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def stopped():
    if vm.VM.is_symlink() or vm.VM.resolve() != vm.VM:
        raise SystemExit('VM storage must be a real project-local directory')
    result = subprocess.run(['docker', 'inspect', '--format', '{{.State.Running}}', vm.NAME],
                            text=True, capture_output=True)
    if result.returncode == 0 and result.stdout.strip() == 'true':
        raise SystemExit('VM is running: cleanly stop it before checkpoint operations')
    # A daemon failure must not be mistaken for an absent stopped container.
    subprocess.run(['docker', 'info', '--format', '{{.ServerVersion}}'], check=True,
                   stdout=subprocess.DEVNULL)


def safe(path):
    if path.is_symlink() or not path.resolve().is_relative_to(vm.VM.resolve()):
        raise SystemExit(f'Unsafe VM path: {path}')


def copy(source, destination):
    safe(source)
    safe(destination)
    if not source.is_file():
        raise SystemExit('Checkpoint sources must be regular VM image files')
    subprocess.run(['cp', '--reflink=auto', '--sparse=always', '--', str(source), str(destination)], check=True)


def image_check(path):
    safe(path)
    vm.qemu_tool('qemu-img', 'check', '/vm/' + str(path.relative_to(vm.VM)))


def write(path, data):
    temp = path.with_suffix('.json.part')
    temp.write_text(json.dumps(data, indent=2) + '\n')
    temp.replace(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['save', 'verify', 'restore'])
    parser.add_argument('name')
    args = parser.parse_args()
    if not re.fullmatch(r'[a-z][a-z0-9-]{1,39}', args.name):
        raise SystemExit('Invalid checkpoint name')
    stopped()
    FOLDER.mkdir(parents=True, exist_ok=True)
    safe(FOLDER)
    manifest = FOLDER / (args.name + '.json')
    safe(manifest)
    if args.action == 'save':
        if RESTORING.exists() or manifest.exists():
            raise SystemExit('Restore pending or checkpoint already exists; inspect before proceeding')
        data = {'name': args.name, 'created_utc': datetime.now(timezone.utc).isoformat(),
                'base_sha256': digest(vm.VM / 'builder-base.img'), 'disks': {}}
        for kind, filename in DISKS.items():
            source = vm.VM / filename
            destination = FOLDER / (args.name + '-' + kind + '.qcow2')
            if destination.exists():
                raise SystemExit(f'Existing partial checkpoint; inspect {destination}')
            image_check(source)
            copy(source, destination)
            expected = digest(source)
            if digest(destination) != expected:
                raise SystemExit('Checkpoint copy hash mismatch')
            data['disks'][kind] = {'file': destination.name, 'sha256': expected}
        write(manifest, data)
        print(f'Verified paired checkpoint saved: {args.name}')
        return
    data = json.loads(manifest.read_text())
    if set(data['disks']) != set(DISKS):
        raise SystemExit('Checkpoint must contain exactly builder and target disks')
    if digest(vm.VM / 'builder-base.img') != data['base_sha256']:
        raise SystemExit('Base image differs from checkpoint')
    for disk in data['disks'].values():
        source = FOLDER / disk['file']
        safe(source)
        if digest(source) != disk['sha256']:
            raise SystemExit('Checkpoint hash mismatch')
        image_check(source)
    if args.action == 'verify':
        print(f'Both checkpoint hashes and qcow2 consistency checks passed: {args.name}')
        return
    if RESTORING.exists():
        pending = json.loads(RESTORING.read_text())
        if pending['name'] != args.name:
            raise SystemExit('Different restore pending; inspect restore-in-progress.json')
        print('Resuming the same stopped-VM restore from its verified checkpoint')
    else:
        backup_name = args.name + '-before-restore-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')
        backup = FOLDER / backup_name
        backup.mkdir()
        for filename in DISKS.values():
            copy(vm.VM / filename, backup / filename)
        pending = {'name': args.name, 'preserved_current_pair': backup.name}
        write(RESTORING, pending)
        print(f'Current disks preserved at checkpoints/{backup.name}', flush=True)
    for kind, disk in data['disks'].items():
        source = FOLDER / disk['file']
        destination = vm.VM / DISKS[kind]
        part = destination.with_suffix('.restore-part')
        copy(source, part)
        if digest(part) != disk['sha256']:
            raise SystemExit('Restore copy mismatch; VM start remains blocked')
        part.replace(destination)
    write(vm.VM / 'last-restore.json', {'checkpoint': data,
        'restored_utc': datetime.now(timezone.utc).isoformat(),
        'preserved_current_pair': pending['preserved_current_pair']})
    RESTORING.unlink()
    print(f'Paired checkpoint restored and hashes verified: {args.name}')


if __name__ == '__main__':
    main()
