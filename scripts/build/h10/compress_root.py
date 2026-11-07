#!/usr/bin/env python3
"""Compress a verified root and compare native extraction plus ACL restoration.

The production CLI requires milestone gates and accepted installed tools.
Component callers may use explicit verified private tools without release credit.
"""
import argparse
import copy
import fcntl
import hashlib
import json
import os
from pathlib import Path
import stat
import struct
import subprocess
import sys
import tempfile
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from copy_selected_root import snapshot, tree_names
from package_backend import PackageBackend

ACL_KEYS = {'system.posix_acl_access', 'system.posix_acl_default'}


def atomic_json(path, value):
    if path.is_symlink() or path.parent.resolve() != path.parent:
        raise ValueError('Compression evidence path redirects')
    fd, temporary = tempfile.mkstemp(prefix=path.name + '.', dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as stream:
            stream.write(json.dumps(value, indent=2) + '\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def superblock(artifact, epoch):
    with artifact.open('rb') as stream:
        raw = stream.read(96)
    if len(raw) != 96:
        raise ValueError('Truncated Squashfs superblock')
    values = struct.unpack('<5I6H8Q', raw)
    if (values[0] != 0x73717368 or values[9:11] != (4, 0) or values[5] != 4
            or values[2] != epoch or values[1] == 0 or not values[7] & (1 << 7)
            or values[7] & (1 << 9) or not 96 <= values[12] <= artifact.stat().st_size
            or not 96 <= values[18] < values[12]):
        raise ValueError('Squashfs format/compressor/epoch/export/xattr profile differs')
    return {'format': '4.0', 'compression': 'xz', 'epoch': values[2], 'inodes': values[1],
            'bytes_used': values[12], 'export_table_offset': values[18], 'exportable': True,
            'xattrs_enabled': True, 'superblock_sha256': hashlib.sha256(raw).hexdigest()}


def format_manifest(manifest, *, restored):
    """Squashfs stores uint32 whole-second timestamps; retain exact source too."""
    result = copy.deepcopy(manifest)
    for name, row in result['entries'].items():
        seconds = row['mtime_ns'] // 1_000_000_000
        if not 0 <= seconds <= 0xffffffff:
            raise ValueError('Image timestamp is outside the Squashfs format: ' + name)
        row['mtime_ns'] = seconds * 1_000_000_000
        if any(not key.startswith(('user.', 'trusted.', 'security.')) and key not in ACL_KEYS
               for key in row['xattrs']):
            raise ValueError('Unreviewed image xattr namespace: ' + name)
        if not restored:
            row['xattrs'] = {key: value for key, value in row['xattrs'].items() if key not in ACL_KEYS}
    return result


def compare(expected, actual):
    left, right = expected['entries'], actual['entries']
    changed = []
    for name in sorted(left.keys() & right.keys()):
        fields = sorted(key for key in left[name].keys() | right[name].keys()
                        if left[name].get(key) != right[name].get(key))
        if fields:
            changed.append({'path': name, 'fields': fields})
    result = {'missing': sorted(left.keys() - right.keys()), 'unknown': sorted(right.keys() - left.keys()),
              'changed': changed, 'hardlinks_match': expected['hardlink_groups'] == actual['hardlink_groups']}
    result['matches'] = not (result['missing'] or result['unknown'] or changed) and result['hardlinks_match']
    return result


def validate_layout(root, image, work):
    for path in (image, work):
        if (path.resolve() != path or not any(path != root / area and path.is_relative_to(root / area)
                                             for area in ('tmp', 'sources/stage'))):
            raise ValueError('Compression must stay in canonical private native staging')
    if (work.exists() or work.is_symlink() or not image.is_dir()
            or image.is_relative_to(work) or work.is_relative_to(image)):
        raise ValueError('Preserve existing/overlapping compression generations')
    parent = work.parent.stat()
    if (not stat.S_ISDIR(parent.st_mode) or parent.st_uid != 0 or parent.st_gid != 0
            or parent.st_mode & 0o022 or parent.st_dev != image.stat().st_dev):
        raise ValueError('Compression needs a protected same-filesystem output parent')


def compress(backend, image, work, expected, tools, epoch, helper=HERE / 'restore_live_acls.sh'):
    image, work = Path(image), Path(work)
    if not backend.native or os.geteuid() != 0 or type(epoch) is not int or not 0 <= epoch <= 0xffffffff:
        raise ValueError('Native root and explicit Squashfs-compatible epoch required')
    validate_layout(backend.target, image, work)
    if snapshot(image, tree_names(image)) != expected:
        raise ValueError('Image differs from its verified assembly manifest')
    uncompressed, restored = format_manifest(expected, restored=False), format_manifest(expected, restored=True)
    sparse_files = [name for name, row in expected['entries'].items()
                    if 'size' in row and (image / name).stat().st_blocks * 512 < row['size']]
    if 'usr/share/toddy/live-root.acl' not in expected['entries']:
        raise ValueError('The verified image lacks its ACL sidecar')
    needed = 2 * sum(row.get('size', 0) for row in expected['entries'].values()) + 2 * 1024**3
    space = os.statvfs(work.parent)
    if space.f_bavail * space.f_frsize < needed:
        raise ValueError('Insufficient space for compression, extraction evidence and reserve')

    def verify_tools():
        if set(tools['binaries']) != {'mksquashfs', 'unsquashfs'}:
            raise ValueError('Exact native compression/extraction tools required')
        for row in tools['binaries'].values():
            path = Path(row['path'])
            if (path.resolve() != path or not path.is_relative_to(backend.target) or not path.is_file()
                    or not path.stat().st_mode & 0o111 or digest(path) != row['sha256']):
                raise ValueError('Native compression tool provenance differs')
    verify_tools()
    helper_bytes = helper.read_bytes()
    work.mkdir(mode=0o700)
    helper_copy = work / 'restore_live_acls.sh'
    helper_copy.write_bytes(helper_bytes)
    report = {'started': datetime.now(timezone.utc).isoformat(), 'image': str(image), 'work': str(work),
              'complete': False, 'native_boot_verified': False, 'release_accepted': False,
              'tools': tools, 'epoch': epoch, 'steps': [], 'helper_sha256': digest(helper_copy)}
    atomic_json(work / 'compression.json', report)
    atomic_json(work / 'source-manifest.json', expected)

    def run(name, program, *args):
        log = work / (name + '.log')
        entry = {'name': name, 'exit': None}
        report['steps'].append(entry)
        atomic_json(work / 'compression.json', report)
        with log.open('xb') as output:
            try:
                result = backend.run('timeout', '--kill-after=60', '7200', '/usr/bin/' + program,
                                     *args, stdout=output, stderr=subprocess.STDOUT)
                entry['exit'] = result.returncode
            except subprocess.CalledProcessError as error:
                entry['exit'] = error.returncode
                raise
            finally:
                output.flush()
                os.fsync(output.fileno())
                entry['log_sha256'] = digest(log)
                atomic_json(work / 'compression.json', report)

    def virtual(path):
        return '/' + str(path.relative_to(backend.target))

    try:
        artifact, extracted = work / 'rootfs.squashfs', work / 'extracted'
        # Native tools live either in their accepted package path or an explicit
        # private experiment. Invoke absolute paths through the native shell.
        mk, un = (virtual(Path(tools['binaries'][name]['path'])) for name in ('mksquashfs', 'unsquashfs'))
        run('compress', 'bash', '-c', 'exec "$@"', 'compress', mk, virtual(image), virtual(artifact),
            '-noappend', '-comp', 'xz', '-processors', '2', '-mem', '256M', '-no-progress',
            '-xattrs', '-xattrs-exclude', r'^system\.posix_acl_(access|default)$',
            '-exports', '-exit-on-error', '-mkfs-time', str(epoch))
        header = superblock(artifact, epoch)
        atomic_json(work / 'superblock.json', header)
        run('extract', 'bash', '-c', 'exec "$@"', 'extract', un, '-strict-errors', '-processors', '2',
            '-no-progress', '-xattrs', '-d', virtual(extracted), virtual(artifact))
        raw = snapshot(extracted, tree_names(extracted))
        atomic_json(work / 'extracted-manifest.json', raw)
        before_acl = compare(uncompressed, raw)
        atomic_json(work / 'extraction-comparison.json', before_acl)
        if not before_acl['matches']:
            raise ValueError('Native extraction differs from declared Squashfs format transformation')
        run('restore-acls', 'bash', '--noprofile', '--norc', '-c',
            'cd -- "$1" && exec /bin/bash --noprofile --norc "$2" usr/share/toddy/live-root.acl',
            'restore', virtual(extracted), virtual(helper_copy))
        final = snapshot(extracted, tree_names(extracted))
        atomic_json(work / 'restored-manifest.json', final)
        comparison = compare(restored, final)
        atomic_json(work / 'restoration-comparison.json', comparison)
        if not comparison['matches']:
            raise ValueError('Native restored root differs from the verified image')
        if any((extracted / name).stat().st_blocks * 512 >= expected['entries'][name]['size']
               for name in sparse_files):
            raise ValueError('Native extraction lost sparse allocation')
        if snapshot(image, tree_names(image)) != expected or helper.read_bytes() != helper_bytes:
            raise ValueError('Source image or restoration helper changed during compression')
        verify_tools()
        report.update(complete=True, finished=datetime.now(timezone.utc).isoformat(),
                      artifact=str(artifact), artifact_sha256=digest(artifact), artifact_bytes=artifact.stat().st_size,
                      entries=len(expected['entries']), hardlink_groups=len(expected['hardlink_groups']),
                      superblock=header,
                      sparse_files=sparse_files, sparse_allocation_preserved=True,
                      source_unchanged=True, native_extraction_and_acl_restore_verified=True,
                      timestamp_policy='Squashfs uint32 whole seconds; original nanoseconds retained in source manifest')
        atomic_json(work / 'compression.json', report)
        return report
    except BaseException as error:
        report.update(complete=False, error=str(error), failed_at=datetime.now(timezone.utc).isoformat())
        atomic_json(work / 'compression.json', report)
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('assembly', type=Path)
    parser.add_argument('work', type=Path)
    parser.add_argument('--epoch', type=int, required=True)
    parser.add_argument('--release', action='store_true')
    args = parser.parse_args()
    subprocess.run(['python3', str(HERE.parent / 'h11/require_gate.py' if args.release else HERE / 'require_gate.py')], check=True)
    build = Path('/var/log/toddy/build')
    with (build / 'build.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if (build / 'input-sync.running').exists() or list(build.glob('*.running.json')):
            raise ValueError('Preserve active build/sync state before compression')
        marker = json.loads((build / 'h10-squashfs-tools.success.json').read_text())
        if marker.get('recipe_exit') != 0 or marker.get('postcheck_exit') != 0:
            raise ValueError('Installed native Squashfs tools have not passed acceptance')
        backend = PackageBackend()
        for path in (args.assembly, args.work):
            if path.resolve() != path or not path.is_relative_to(backend.target / 'sources/stage'):
                raise ValueError('Production compression requires designated physical staging paths')
        evidence = args.assembly.parent.stat()
        if evidence.st_uid != 0 or evidence.st_gid != 0 or evidence.st_mode & 0o022:
            raise ValueError('Assembly evidence is not protected native state')
        journal = json.loads(args.assembly.read_text())
        if (not journal.get('assembled') or journal.get('release_profile') != args.release
                or journal.get('evidence') != str(args.assembly.parent)
                or journal.get('assembler_sha256') != digest(HERE / 'assemble_root.py')):
            raise ValueError('Require successful assembly of the requested profile')
        action = next(row for row in journal['actions'] if row['step'] == 'image-manifest')
        if Path(action['report']).name != action['report']:
            raise ValueError('Assembly manifest report name redirects')
        manifest = args.assembly.parent / action['report']
        if not action['finished'] or digest(manifest) != action['sha256']:
            raise ValueError('Preserved image manifest differs from successful assembly')
        version, arch, state = backend.run('dpkg-query', '-W', '-f=${Version}\t${Architecture}\t${Status}',
                                           'squashfs-tools', capture_output=True, text=True).stdout.split('\t')
        record = json.loads((Path('/var/log/toddy/packages') / f'squashfs-tools_{version}_{arch}.json').read_text())
        if (version != '4.7.5-1' or state != 'install ok installed' or record.get('installed') is not True
                or record.get('name') != 'squashfs-tools' or record.get('version') != version or arch != 'amd64'
                or digest(Path('/var/cache/toddy/packages') / f'squashfs-tools_{version}_{arch}.deb') != record['archive_sha256']):
            raise ValueError('Installed compression package provenance differs')
        tools = {'accepted_package': True, 'archive_sha256': record['archive_sha256'], 'binaries': {
            name: {'path': str(backend.target / 'usr/bin' / name), 'sha256': record['payload']['/usr/bin/' + name]['sha256']}
            for name in ('mksquashfs', 'unsquashfs')}}
        print(json.dumps(compress(backend, Path(journal['image']), args.work,
                                 json.loads(manifest.read_text()), tools, args.epoch), indent=2))


if __name__ == '__main__':
    main()
