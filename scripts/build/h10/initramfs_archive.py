#!/usr/bin/env python3
"""Package the verified early runtime and public live metadata as gzip/newc.

The caller supplies metadata derived from its actual root image. This component
does not establish Squashfs correctness, boot acceptance or publisher trust.
"""
import argparse
import fcntl
import gzip
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import initramfs_runtime as runtime


def validate_newc(raw, expected, epoch):
    """Compare every archive entry against the exact private staged inventory."""
    offset = 0
    seen = set()
    while True:
        header = raw[offset:offset + 110]
        if len(header) != 110 or header[:6] != b'070701':
            raise ValueError('Missing/truncated newc header')
        if not re.fullmatch(b'[0-9a-fA-F]{104}', header[6:]):
            raise ValueError('Invalid newc numeric header')
        fields = [int(header[i:i + 8], 16) for i in range(6, 110, 8)]
        ino, mode, uid, gid, nlink, mtime, size, devmaj, devmin, rmaj, rmin, namesize, crc = fields
        if namesize < 1:
            raise ValueError('Empty newc name')
        end = offset + 110 + namesize
        name_bytes = raw[offset + 110:end]
        if len(name_bytes) != namesize or name_bytes[-1:] != b'\0' or b'\0' in name_bytes[:-1]:
            raise ValueError('Invalid/truncated newc name')
        name = name_bytes[:-1].decode('utf-8')
        body_start = (end + 3) & ~3
        body_end = body_start + size
        offset = (body_end + 3) & ~3
        if offset > len(raw) or any(raw[end:body_start]) or any(raw[body_end:offset]):
            raise ValueError('Truncated or nonzero newc padding')
        body = raw[body_start:body_end]
        if name == 'TRAILER!!!':
            if size or any(raw[offset:]) or seen != set(expected):
                raise ValueError('Unexpected newc trailer, entries or trailing bytes')
            break
        if (name in seen or name not in expected or name.startswith('/')
                or '..' in PurePosixPath(name).parts or str(PurePosixPath(name)) != name):
            raise ValueError('Unexpected/duplicate/unsafe newc entry: ' + name)
        entry = expected[name]
        if (mode != entry['mode'] or uid != 0 or gid != 0 or mtime != epoch
                or crc != 0 or not nlink or (rmaj, rmin) != tuple(entry['rdev'])):
            raise ValueError('Archive metadata differs: ' + name)
        if hashlib.sha256(body).hexdigest() != entry['body_sha256'] or size != entry['size']:
            raise ValueError('Archive payload differs: ' + name)
        if not stat.S_ISDIR(mode) and nlink != 1:
            raise ValueError('Unexpected hardlink in minimal runtime: ' + name)
        seen.add(name)
    return len(seen)


def inventory(stage, epoch):
    result = {}
    paths = [stage] + sorted(stage.rglob('*'))
    for path in paths:
        name = '.' if path == stage else path.relative_to(stage).as_posix()
        info = path.lstat()
        if stat.S_ISREG(info.st_mode):
            body = path.read_bytes()
        elif stat.S_ISLNK(info.st_mode):
            body = os.readlink(path).encode()
        elif stat.S_ISDIR(info.st_mode):
            body = b''
        elif stat.S_ISCHR(info.st_mode) and name in ('dev/console', 'dev/null'):
            body = b''
        else:
            raise ValueError('Unexpected private runtime entry: ' + name)
        os.chown(path, 0, 0, follow_symlinks=False)
        os.utime(path, (epoch, epoch), follow_symlinks=False)
        result[name] = {'mode': info.st_mode, 'size': len(body),
                        'body_sha256': hashlib.sha256(body).hexdigest(),
                        'rdev': [os.major(info.st_rdev), os.minor(info.st_rdev)]}
    return result


def assemble(root, work, records, init_script, media_helper, media_id, root_sha256, epoch):
    if any(not re.fullmatch('[0-9a-f]{64}', value) for value in (media_id, root_sha256)):
        raise ValueError('Expected lowercase SHA-256-shaped public metadata')
    if type(epoch) is not int or not 0 <= epoch <= 0xffffffff:
        raise ValueError('Explicit newc-compatible timestamp required')
    if (root.is_symlink() or root.resolve() != root or not root.is_dir()
            or work.exists() or work.is_symlink() or work.parent.resolve() != work.parent
            or not any(work.parent.is_relative_to(root / area) for area in ('sources/stage', 'tmp'))):
        raise ValueError('Preserve existing/redirected work; require private target storage')
    # Archive tools must also be installed source-owned native bytes.
    owners = runtime.installed_records(root, records)
    tools = {}
    for virtual in ('/usr/bin/bsdcpio', '/usr/bin/gzip'):
        path, canonical = runtime.target_resolve(root, virtual)
        if canonical not in owners or not path.is_file() or path.is_symlink():
            raise ValueError('Missing native archive tool owner: ' + virtual)
        package, version, archive, metadata = owners[canonical]
        if runtime.digest(path) != metadata['sha256']:
            raise ValueError('Modified native archive tool: ' + virtual)
        tools[virtual] = {'package': package, 'version': version,
                          'archive_sha256': archive, 'sha256': metadata['sha256']}
    work.mkdir(mode=0o700)
    stage = work / 'runtime'
    runtime_report = runtime.stage_runtime(root, stage, records)
    for directory in ('etc/toddy-live', 'usr/lib/toddy'):
        (stage / directory).mkdir(mode=0o755)
        (stage / directory).chmod(0o755)
    additions = {
        'init': (init_script.read_bytes(), 0o755),
        'usr/lib/toddy/live_media.sh': (media_helper.read_bytes(), 0o644),
        'usr/lib/toddy/restore_live_acls.sh': (init_script.with_name('restore_live_acls.sh').read_bytes(), 0o644),
        'etc/toddy-live/media-id': ((media_id + '\n').encode(), 0o644),
        'etc/toddy-live/rootfs.sha256': ((root_sha256 + '\n').encode(), 0o644),
    }
    for name, (body, mode) in additions.items():
        with (stage / name).open('xb') as stream:
            stream.write(body)
        (stage / name).chmod(mode)
    expected = inventory(stage, epoch)
    names = b'\0'.join(name.encode() for name in sorted(expected)) + b'\0'
    archive = work / 'initramfs.cpio'
    prefix = ['chroot', str(root), '/usr/bin/env', '-i', 'PATH=/usr/bin:/usr/sbin', 'LC_ALL=C']
    with archive.open('xb') as output, (work / 'cpio.log').open('xb') as log:
        subprocess.run(prefix + ['/bin/bash', '-c',
            'cd "$1" && exec bsdcpio -o --null --format=newc --owner 0:0 --quiet',
            'archive', '/' + str(stage.relative_to(root))], input=names,
            stdout=output, stderr=log, check=True)
    raw = archive.read_bytes()
    count = validate_newc(raw, expected, epoch)
    compressed = work / 'initramfs.cpio.gz'
    with compressed.open('xb') as output, (work / 'gzip.log').open('xb') as log:
        subprocess.run(prefix + ['/usr/bin/gzip', '-n', '-9', '-c',
                       '/' + str(archive.relative_to(root))], stdout=output, stderr=log, check=True)
    if gzip.decompress(compressed.read_bytes()) != raw:
        raise ValueError('Compressed archive roundtrip differs')
    report = {'format': 'newc 070701 + gzip -n -9', 'epoch': epoch,
              'media_id': media_id, 'rootfs_sha256': root_sha256,
              'runtime': runtime_report, 'archive_tools': tools, 'entries': expected,
              'entry_count': count, 'cpio_sha256': runtime.digest(archive),
              'gzip_sha256': runtime.digest(compressed), 'gzip_bytes': compressed.stat().st_size,
              'kernel_boot_validated': False, 'root_image_validated': False}
    (work / 'manifest.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


def main():
    if os.geteuid() != 0:
        raise ValueError('Requires designated build-guest root')
    here = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('compression', type=Path, help='Verified native compression.json with assembly binding')
    parser.add_argument('work', type=Path, help='Fresh private generation under sources/stage')
    parser.add_argument('--media-id', required=True)
    parser.add_argument('--release', action='store_true', help='Use the H11 release-profile gate')
    args = parser.parse_args()
    gate = here.parent / 'h11/require_gate.py' if args.release else here / 'require_gate.py'
    subprocess.run(['python3', str(gate)], check=True)
    root = Path('/mnt/lfs')
    from initramfs_input import physical, verify, unchanged
    from compress_root import atomic_json
    build = Path('/var/log/toddy/build')
    with (build / 'build.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if (build / 'input-sync.running').exists() or list(build.glob('*.running.json')):
            raise ValueError('Preserve active build/sync state before initramfs generation')
        if any(path.resolve() != path or not path.is_relative_to(root / 'sources/stage')
               for path in (args.compression, args.work)):
            raise ValueError('Production initramfs requires designated physical staging paths')
        physical(root, args.work.parent, directory=True)
        binding = verify(root, args.compression, args.release)
        if any(args.work.is_relative_to(source) or source.is_relative_to(args.work)
               for source in (args.compression.parent, Path(binding['source_image']),
                              Path(binding['assembly_evidence_directory']))):
            raise ValueError('Preserve disjoint assembly, compression and initramfs generations')
        report = assemble(root, args.work, Path('/var/log/toddy/packages'),
                          here / 'live_init.sh', here / 'live_media.sh', args.media_id,
                          binding['rootfs_sha256'], binding['epoch'])
        unchanged(root, binding)
        report['compression_binding'] = binding
        atomic_json(args.work / 'manifest.json', report)
        print(json.dumps({k: report[k] for k in ('entry_count', 'gzip_sha256', 'gzip_bytes', 'compression_binding')}))


if __name__ == '__main__':
    main()
