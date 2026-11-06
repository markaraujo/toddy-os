#!/usr/bin/env python3
"""Stage an explicit source-owned early-userspace runtime; never copy host state."""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from audit_native_elf import target_resolve

PROGRAMS = (
    '/usr/bin/bash', '/usr/bin/mount', '/usr/bin/umount',
    '/usr/sbin/blkid', '/usr/sbin/switch_root', '/usr/sbin/chroot',
    '/usr/bin/mkdir', '/usr/bin/cat', '/usr/bin/sleep',
    '/usr/bin/readlink', '/usr/bin/sha256sum',
)
ALIASES = {'bin': 'usr/bin', 'sbin': 'usr/sbin', 'lib': 'usr/lib', 'lib64': 'usr/lib'}


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def destination_path(virtual):
    parts = PurePosixPath(virtual).parts
    if (not virtual.startswith('/') or virtual.startswith('//') or '..' in parts
            or PurePosixPath(virtual).as_posix() != virtual or any(c.isspace() for c in virtual)):
        raise ValueError('Unexpected runtime path')
    relative = virtual.lstrip('/')
    for alias, target in ALIASES.items():
        if relative.startswith(alias + '/'):
            relative = target + relative[len(alias):]
            break
    if not relative.startswith(('usr/bin/', 'usr/sbin/', 'usr/lib/')):
        raise ValueError('Runtime payload outside the declared binary/library directories')
    return relative


def installed_records(root, records):
    output = subprocess.check_output(['chroot', str(root), '/usr/bin/dpkg-query', '-W',
              '-f=${Package}\t${Version}\t${Architecture}\t${Status}\n'], text=True)
    owners = {}
    for line in output.splitlines():
        name, version, architecture, status = line.split('\t')
        if status != 'install ok installed':
            raise ValueError('Unconfigured native package: ' + name)
        record = json.loads((records / f'{name}_{version}_{architecture}.json').read_text())
        if not record['installed']:
            raise ValueError('Missing installed native provenance: ' + name)
        for virtual, metadata in record['payload'].items():
            if metadata.get('sha256'):
                if virtual in owners:
                    raise ValueError('Duplicate native file ownership: ' + virtual)
                owners[virtual] = (name, version, record['archive_sha256'], metadata)
    return owners


def runtime_dependencies(root, program):
    result = subprocess.run(['chroot', str(root), '/usr/bin/env', '-i',
                            'PATH=/usr/bin:/usr/sbin', 'LC_ALL=C',
                            '/usr/bin/ldd', program], check=True, text=True, capture_output=True)
    paths = set()
    for line in result.stdout.splitlines():
        line = line.strip()
        if re.fullmatch(r'linux-vdso\.so\.1 \(0x[0-9a-f]+\)', line):
            continue
        match = re.fullmatch(r'(?:\S+ => )?(/\S+) \(0x[0-9a-f]+\)', line)
        if not match:
            raise ValueError('Unresolved/unreviewed native loader output: ' + line)
        destination_path(match[1])
        paths.add(match[1])
    if '/lib64/ld-linux-x86-64.so.2' not in paths:
        raise ValueError('Missing native x86_64 loader')
    return paths


def stage_runtime(root, stage, records):
    if root.is_symlink() or root.resolve() != root or not root.is_dir():
        raise ValueError('Native source root must be canonical')
    if stage.exists() or stage.is_symlink() or stage.parent.resolve() != stage.parent:
        raise ValueError('Preserve existing/redirected runtime stage')
    if not any(stage.parent.is_relative_to(root / area) for area in ('sources/stage', 'tmp')):
        raise ValueError('Runtime stage must remain in target staging or private temporary storage')
    owners = installed_records(root, records)

    def verified(virtual):
        path, canonical = target_resolve(root, virtual)
        if canonical not in owners or not path.is_file() or path.is_symlink():
            raise ValueError('Missing canonical native file owner: ' + virtual)
        name, version, archive, metadata = owners[canonical]
        if digest(path) != metadata['sha256']:
            raise ValueError('Modified native runtime bytes: ' + canonical)
        return path, canonical, name, version, archive, metadata

    paths = set(PROGRAMS)
    for program in PROGRAMS:
        verified(program)
        paths.update(runtime_dependencies(root, program))
    plan = {virtual: verified(virtual) for virtual in sorted(paths)}
    # Every input is checked before creating the private stage. No /etc, home,
    # credentials, firmware, optional modules or workstation paths are copied.
    stage.mkdir(mode=0o755)
    stage.chmod(0o755)
    for directory in ('dev', 'proc', 'sys', 'run', 'newroot', 'etc', 'usr',
                      'usr/bin', 'usr/sbin', 'usr/lib'):
        (stage / directory).mkdir(parents=True, exist_ok=True, mode=0o755)
        (stage / directory).chmod(0o755)
    for alias, target in ALIASES.items():
        (stage / alias).symlink_to(target)
    (stage / 'usr/bin/sh').symlink_to('bash')
    files = {}
    for virtual, (source, canonical, name, version, archive, metadata) in plan.items():
        relative = destination_path(virtual)
        destination = stage / relative
        if relative in files:
            if files[relative]['sha256'] != metadata['sha256']:
                raise ValueError('Different providers map to the same runtime path')
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        # Early userspace has only PID 1/root; source set-ID bits and xattrs are
        # unnecessary here. This does not alter the full root's file metadata.
        mode = stat.S_IMODE(source.stat().st_mode) & 0o777
        destination.chmod(mode)
        os.chown(destination, 0, 0)
        if digest(destination) != metadata['sha256']:
            raise ValueError('Copied runtime bytes differ')
        files[relative] = {'requested': virtual, 'source_path': canonical,
                           'package': name, 'version': version,
                           'archive_sha256': archive, 'sha256': metadata['sha256'], 'mode': mode}
    for name, mode, device in [('console', 0o600, (5, 1)), ('null', 0o666, (1, 3))]:
        path = stage / 'dev' / name
        os.mknod(path, stat.S_IFCHR | mode, os.makedev(*device))
        path.chmod(mode)
        os.chown(path, 0, 0)
    return {'programs': PROGRAMS, 'files': files, 'root_aliases': ALIASES,
            'shell_alias': 'usr/bin/sh -> bash', 'devices': {'console': [5, 1], 'null': [1, 3]},
            'source_owned_bytes_verified': True, 'kernel_boot_validated': False,
            'live_root_assembled': False,
            'limitations': ['Loader dependency discovery does not establish optional dlopen/data coverage.',
                            'Actual early mounts, root discovery, overlay and ACL restore require native boot.']}


def main():
    if os.geteuid() != 0:
        raise ValueError('Requires designated build-guest root')
    here = Path(__file__).resolve().parent
    subprocess.run(['python3', str(here / 'require_gate.py')], check=True)
    root = Path('/mnt/lfs')
    stage = root / 'sources/stage/toddy-initramfs-runtime'
    report = stage_runtime(root, stage, Path('/var/log/toddy/packages'))
    evidence = root / 'sources/evidence/h10-initramfs'
    evidence.mkdir(parents=True, exist_ok=True)
    (evidence / 'runtime.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'files': len(report['files']), 'stage': str(stage), 'boot_validated': False}))


if __name__ == '__main__':
    main()
