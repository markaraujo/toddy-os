#!/usr/bin/env python3
"""Compose a fresh H11 hybrid ISO from bound native release artifacts.

Creating and reading back an ISO is not release, license or guest-boot acceptance.
All inputs and failed generations remain available for independent review.
"""
import argparse
from datetime import datetime, timezone
import fcntl
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent / 'h10'), str(HERE.parent)]
import hybrid_media
import initramfs_archive
import initramfs_input
from compress_root import atomic_json
from package_backend import PackageBackend

VERSIONS = {'linux-kernel': '7.1.8-1', 'grub': '2.14-1+toddy1', 'mtools': '4.0.50-1',
            'libburn': '1.5.8-1', 'libisofs': '1.5.8.pl02-1', 'libisoburn': '1.5.8.pl02-1'}
BUILD = Path('/var/log/toddy/build')
digest = hybrid_media.digest


def packages(backend, versions=None):
    evidence, files = {}, {}
    for name, expected_version in (VERSIONS if versions is None else versions).items():
        version, arch, status = backend.run('dpkg-query', '-W', '-f=${Version}\t${Architecture}\t${Status}',
            name, capture_output=True, text=True).stdout.split('\t')
        if (version, arch, status) != (expected_version, 'amd64', 'install ok installed'):
            raise ValueError('Required native media package is not configured: ' + name)
        record_path = Path('/var/log/toddy/packages') / f'{name}_{version}_{arch}.json'
        record = json.loads(record_path.read_text())
        archive = Path('/var/cache/toddy/packages') / f'{name}_{version}_{arch}.deb'
        if (record.get('installed') is not True or record.get('name') != name
                or record.get('version') != version or digest(archive) != record['archive_sha256']):
            raise ValueError('Native media package provenance differs: ' + name)
        evidence[name] = {'version': version, 'record': str(record_path), 'record_sha256': digest(record_path),
                          'archive': str(archive), 'archive_sha256': record['archive_sha256']}
        for virtual, entry in record['payload'].items():
            path = backend.target / virtual.lstrip('/')
            if 'sha256' in entry:
                if (path.resolve() != path or not path.is_file() or digest(path) != entry['sha256']
                        or (path.stat().st_mode, path.stat().st_uid, path.stat().st_gid)
                        != (entry['mode'], entry['uid'], entry['gid'])):
                    raise ValueError('Native media package payload changed: ' + virtual)
                files[virtual] = entry['sha256']
            elif 'symlink' in entry:
                if (not path.is_symlink() or str(path.readlink()) != entry['symlink']
                        or (path.lstat().st_mode, path.lstat().st_uid, path.lstat().st_gid)
                        != (entry['mode'], entry['uid'], entry['gid'])):
                    raise ValueError('Native media package alias changed: ' + virtual)
    return evidence, files


def archive_input(root, manifest, scripts=HERE.parent / 'h10', *, release=True):
    manifest = initramfs_input.physical(root, manifest)
    report = json.loads(manifest.read_text())
    recorded = report.get('compression_binding', {})
    if type(release) is not bool or recorded.get('compression_bound') is not True or recorded.get('release_profile') is not release:
        raise ValueError('Require the exact completed initramfs assembly profile')
    compression_files = [Path(name) for name in recorded['evidence_sha256'] if Path(name).name == 'compression.json']
    if len(compression_files) != 1:
        raise ValueError('Require a unique bound compression report')
    binding = initramfs_input.verify(root, compression_files[0], release, assembler=scripts / 'assemble_root.py')
    if recorded != binding or report.get('rootfs_sha256') != binding['rootfs_sha256'] or report.get('epoch') != binding['epoch']:
        raise ValueError('Initramfs and compressed root belong to different generations')
    media_id = report.get('media_id', '')
    if not re.fullmatch('[0-9a-f]{64}', media_id):
        raise ValueError('Invalid embedded media identity')
    archive = initramfs_input.physical(root, manifest.parent / 'initramfs.cpio.gz')
    if archive.stat().st_size != report['gzip_bytes'] or digest(archive) != report['gzip_sha256']:
        raise ValueError('Initramfs artifact differs from its verified manifest')
    with gzip.open(archive, 'rb') as stream:
        raw = stream.read(256 * 1024 ** 2 + 1)
    if len(raw) > 256 * 1024 ** 2 or hashlib.sha256(raw).hexdigest() != report['cpio_sha256']:
        raise ValueError('Unexpected or changed minimal initramfs payload')
    if initramfs_archive.validate_newc(raw, report['entries'], binding['epoch']) != report['entry_count']:
        raise ValueError('Initramfs entry inventory differs')
    public = {'etc/toddy-live/media-id': (media_id + '\n').encode(),
              'etc/toddy-live/rootfs.sha256': (binding['rootfs_sha256'] + '\n').encode(),
              'init': (scripts / 'live_init.sh').read_bytes(),
              'usr/lib/toddy/live_media.sh': (scripts / 'live_media.sh').read_bytes(),
              'usr/lib/toddy/restore_live_acls.sh': (scripts / 'restore_live_acls.sh').read_bytes()}
    if any(report['entries'][name]['body_sha256'] != hashlib.sha256(data).hexdigest()
           for name, data in public.items()):
        raise ValueError('Initramfs metadata or reviewed early-boot scripts differ')
    return report, binding, {str(manifest): digest(manifest), str(archive): digest(archive)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('initramfs_manifest', type=Path)
    parser.add_argument('work', type=Path)
    parser.add_argument('--validation', action='store_true',
        help='H10 validation media only; require the H10 root profile and gate')
    args = parser.parse_args()
    gate = HERE.parent / 'h10/require_gate.py' if args.validation else HERE / 'require_gate.py'
    subprocess.run(['python3', str(gate)], check=True)
    backend = PackageBackend()
    root, work = backend.target, args.work
    with (BUILD / 'build.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if (BUILD / 'input-sync.running').exists() or list(BUILD.glob('*.running.json')):
            raise ValueError('Preserve active dispatcher/sync state before ISO assembly')
        if (os.geteuid() != 0 or not backend.native or work.resolve() != work
                or not work.is_relative_to(root / 'sources/stage') or work.exists() or work.is_symlink()):
            raise ValueError('Require a fresh private production ISO generation')
        if (args.initramfs_manifest.resolve() != args.initramfs_manifest
                or not args.initramfs_manifest.is_relative_to(root / 'sources/stage')):
            raise ValueError('Production media requires a staged initramfs generation')
        initramfs_input.physical(root, work.parent, directory=True)
        for step in ('h07-grub', 'h09-kernel', 'h09-bootloader', 'h10-squashfs-tools',
                     'h11-mtools', 'h11-libburn', 'h11-libisofs', 'h11-libisoburn'):
            marker = json.loads((BUILD / (step + '.success.json')).read_text())
            if marker.get('recipe_exit') != 0 or marker.get('postcheck_exit') != 0:
                raise ValueError('Required native media prerequisite failed: ' + step)
        initial_packages, files = packages(backend)
        archive, binding, evidence = archive_input(root, args.initramfs_manifest, release=not args.validation)
        inputs = {'boot/vmlinuz-7.1.8-toddy': root / 'boot/vmlinuz-7.1.8-toddy',
                  'boot/initramfs.cpio.gz': args.initramfs_manifest.parent / 'initramfs.cpio.gz',
                  'live/rootfs.squashfs': Path(binding['artifact'])}
        hashes = {'boot/vmlinuz-7.1.8-toddy': files['/boot/vmlinuz-7.1.8-toddy'],
                  'boot/initramfs.cpio.gz': archive['gzip_sha256'],
                  'live/rootfs.squashfs': binding['rootfs_sha256']}
        source_manifest_path = Path(binding['artifact']).parent / 'source-manifest.json'
        source_manifest = json.loads(source_manifest_path.read_text())['entries']
        kernel_record = json.loads(Path(initial_packages['linux-kernel']['record']).read_text())
        if any(source_manifest.get(name.lstrip('/'), {}).get('sha256') != row['sha256']
               for name, row in kernel_record['payload'].items() if 'sha256' in row):
            raise ValueError('Compressed root kernel/modules differ from the selected native kernel generation')
        # Work may not be nested in any existing source/evidence generation.
        protected = [args.initramfs_manifest.parent, Path(binding['artifact']).parent,
                     Path(binding['source_image']), Path(binding['assembly_evidence_directory'])]
        if any(work.is_relative_to(path) or path.is_relative_to(work) for path in protected):
            raise ValueError('Preserve disjoint ISO and input generations')
        if shutil.disk_usage(work.parent).free < 3 * sum(p.stat().st_size for p in inputs.values()) + 2 * 1024 ** 3:
            raise ValueError('Insufficient space for ISO payload, full readback and reserve')
        work.mkdir(mode=0o700)
        result = {'started': datetime.now(timezone.utc).isoformat(), 'work': str(work),
                  'complete': False, 'release_accepted': False, 'validation_only': args.validation,
                  'native_kernel_boot_verified': False,
                  'physical_hardware_tested': False, 'stages': [], 'native_packages': initial_packages,
                  'input_sha256': {str(inputs[name]): sha for name, sha in hashes.items()},
                  'initramfs_evidence_sha256': evidence, 'compression_binding': binding,
                  'assembler_sha256': digest(Path(__file__)), 'composer_sha256': digest(HERE / 'hybrid_media.py')}
        atomic_json(work / 'result.json', result)
        try:
            source = work / 'input'
            for name, original in inputs.items():
                destination = source / name
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(original, destination)
                destination.chmod(0o644)
                if digest(destination) != hashes[name]:
                    raise ValueError('Copied media payload differs: ' + name)
            (source / 'boot/grub').mkdir()
            (source / '.toddy').mkdir()
            media_id = archive['media_id']
            (source / '.toddy' / media_id).touch()
            (source / '.toddy-media-id').write_text(media_id + '\n')
            (source / 'boot/grub/grub.cfg').write_text(hybrid_media.live_configuration())

            def stage(name, argv):
                entry = {'name': name, 'argv': argv, 'exit': None, 'timeout_seconds': 1800}
                result['stages'].append(entry)
                atomic_json(work / 'result.json', result)
                with (work / (name + '.log')).open('xb') as log:
                    command = ['chroot', str(root), '/usr/bin/env', '-i',
                        'HOME=/' + work.relative_to(root).as_posix(), 'PATH=/usr/bin:/usr/sbin',
                        'LC_ALL=C.UTF-8', 'MTOOLSRC=/dev/null', '/usr/bin/timeout', '--kill-after=60', '1800', *argv]
                    completed = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
                    log.flush()
                    os.fsync(log.fileno())
                entry.update(exit=completed.returncode, log_sha256=digest(work / (name + '.log')))
                atomic_json(work / 'result.json', result)
                completed.check_returncode()

            media = hybrid_media.compose(root, work, stage, marker='/.toddy/' + media_id)
            initramfs_input.unchanged(root, binding)
            if (any(digest(Path(name)) != sha for name, sha in evidence.items())
                    or packages(backend) != (initial_packages, files)):
                raise ValueError('Native media input changed during composition')
            with (work / 'SHA256SUMS').open('x') as checksum:
                checksum.write(media['sha256'] + '  toddy.iso\n')
                checksum.flush()
                os.fsync(checksum.fileno())
            result.update(complete=True, finished=datetime.now(timezone.utc).isoformat(), media=media,
                          pending_acceptance=['complete component/source/license inventory',
                              'final distribution credential review', 'actual native BIOS/UEFI/USB boot and recovery'])
            atomic_json(work / 'result.json', result)
            print(json.dumps(result, indent=2))
        except BaseException as error:
            result.update(complete=False, error=str(error), failed_at=datetime.now(timezone.utc).isoformat())
            atomic_json(work / 'result.json', result)
            raise


if __name__ == '__main__':
    main()
