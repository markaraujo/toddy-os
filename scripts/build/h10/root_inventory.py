"""Select verified package payload for a future fresh live-root assembly.

This inventory alone omits generated configuration and the package database.
It is not a complete bootable root or release credential approval.
"""
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import stat

FRESH_DIRECTORIES = {'dev': 0o755, 'proc': 0o755, 'sys': 0o755, 'run': 0o755,
                     'tmp': 0o1777, 'home': 0o755, 'root': 0o700, 'var/tmp': 0o1777}
GENERATED_ACCOUNTS = {'/etc/' + name for name in ('passwd', 'group', 'shadow', 'gshadow',
    'subuid', 'subgid', 'machine-id', 'passwd-', 'group-', 'shadow-', 'gshadow-', '.pwd.lock')}


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def package_inventory(records):
    names, owners, entries, packages = {'.'}, {}, {}, {}
    fresh = {path: {'mode': stat.S_IFDIR | mode, 'uid': 0, 'gid': 0, 'directory': True}
             for path, mode in FRESH_DIRECTORIES.items()}
    for record in records:
        name = record['name']
        if (not re.fullmatch(r'[a-z0-9][a-z0-9+.-]+', name) or name in packages
                or record.get('installed') is not True or not record.get('payload')
                or not re.fullmatch(r'[0-9a-f]{64}', record['archive_sha256'])):
            raise ValueError('Incomplete or duplicate installed own-package record')
        packages[name] = {'version': record['version'], 'archive_sha256': record['archive_sha256'],
                          'payload_entries': len(record['payload'])}
        for path, row in record['payload'].items():
            parsed = PurePosixPath(path)
            if (not path.startswith('/') or path.startswith('//') or path == '/'
                    or '..' in parsed.parts or parsed.as_posix() != path or '\0' in path):
                raise ValueError('Noncanonical package payload path')
            relative = path[1:]
            if relative.split('/')[0] in {'sources', 'tools'}:
                raise ValueError('Build-only package path cannot enter an image: ' + path)
            if path in GENERATED_ACCOUNTS:
                raise ValueError('Package payload attempts to carry generated account/identity state: ' + path)
            if path == '/var/lib/dbus/machine-id' and (name != 'dbus' or row != {
                    'mode': stat.S_IFLNK | 0o777, 'uid': 0, 'gid': 0, 'symlink': '/etc/machine-id'}):
                raise ValueError('DBus must own only the canonical machine-ID link')
            fresh_tree = next((base for base in FRESH_DIRECTORIES
                               if relative == base or relative.startswith(base + '/')), None)
            if fresh_tree is not None:
                if not row.get('directory'):
                    raise ValueError('Runtime/home state cannot be package image payload: ' + path)
                if relative not in fresh:
                    fresh[relative] = row
                elif fresh[relative] != row:
                    raise ValueError('Package directory conflicts with fresh runtime policy: ' + path)
                continue
            if not row.get('directory') and (relative.startswith(('var/log/', 'var/cache/', 'var/lib/dpkg/'))
                                              or relative in {'var/log', 'var/cache', 'var/lib/dpkg'}):
                raise ValueError('Mutable generated database/cache/log cannot be package payload: ' + path)
            if path in entries and (not row.get('directory') or entries[path] != row):
                raise ValueError('Conflicting package ownership or shared directory metadata: ' + path)
            entries[path] = row
            owners.setdefault(path, set()).add(name)
            names.add(relative)
            parent = PurePosixPath(relative).parent
            while parent.as_posix() != '.':
                names.add(parent.as_posix())
                parent = parent.parent
    if not packages:
        raise ValueError('An empty package set is not an image inventory')
    # Every actual source parent must itself be an owned directory. No implicit
    # traversal through an unreviewed directory or merged-/usr alias is allowed.
    for relative in names - {'.'}:
        if '/' + relative not in entries:
            raise ValueError('Selected package parent has no native provenance: /' + relative)
    return {'names': sorted(names), 'entries': entries,
            'owners': {path: sorted(value) for path, value in owners.items()},
            'fresh_directories': fresh, 'packages': packages,
            'complete_image_inventory': False,
            'pending_inputs': ['validated native package database', 'reviewed generated configuration links',
                               'fresh account/identity state', 'live filesystem/login profile',
                               'derived caches/indexes and final image audits']}


def inspect_installed(backend, records_directory, cache_directory):
    root = backend.target
    if not backend.native or root.resolve() != root:
        raise ValueError('Image inventory requires an explicit accepted native target')
    status_path = root / 'var/lib/dpkg/status'
    status_before = digest(status_path)
    text = backend.run('dpkg-query', '-W', '-f=${Package}\t${Version}\t${Architecture}\t${Status}\n',
                       capture_output=True, text=True).stdout
    records, record_hashes = [], {}
    for line in text.splitlines():
        name, version, architecture, status = line.split('\t')
        if status != 'install ok installed':
            raise ValueError('Unconfigured package prevents a stable image inventory: ' + name)
        if (not re.fullmatch(r'[a-z0-9][a-z0-9+.-]+', name)
                or not re.fullmatch(r'[0-9][0-9A-Za-z.+:~_-]*', version)
                or architecture not in {'amd64', 'all'}):
            raise ValueError('Unexpected native package identity')
        stem = f'{name}_{version}_{architecture}'
        path = Path(records_directory) / (stem + '.json')
        archive = Path(cache_directory) / (stem + '.deb')
        if path.resolve() != path or archive.resolve() != archive:
            raise ValueError('Own package provenance/archive redirects')
        raw = path.read_bytes()
        record = json.loads(raw)
        if record['name'] != name or record['version'] != version or digest(archive) != record['archive_sha256']:
            raise ValueError('Own package archive/record identity differs: ' + name)
        records.append(record)
        record_hashes[str(path)] = hashlib.sha256(raw).hexdigest()
    inventory = package_inventory(records)
    device = root.stat().st_dev
    files = 0
    for virtual, row in inventory['entries'].items():
        path = root / virtual[1:]
        if path.parent.resolve() != path.parent:
            raise ValueError('Selected package parent redirects: ' + virtual)
        actual = path.lstat()
        if actual.st_dev != device:
            raise ValueError('Selected package source crosses a filesystem: ' + virtual)
        if row.get('directory'):
            if not stat.S_ISDIR(actual.st_mode):
                raise ValueError('Owned package directory changed type: ' + virtual)
            continue
        if (actual.st_mode, actual.st_uid, actual.st_gid) != (row['mode'], row['uid'], row['gid']):
            raise ValueError('Owned package file metadata changed: ' + virtual)
        if 'sha256' in row:
            if digest(path) != row['sha256']:
                raise ValueError('Owned package bytes changed: ' + virtual)
        elif path.readlink().as_posix() != row['symlink']:
            raise ValueError('Owned package link changed: ' + virtual)
        files += 1
    if digest(status_path) != status_before or any(digest(Path(path)) != sha for path, sha in record_hashes.items()):
        raise ValueError('Package state/provenance changed during inventory inspection')
    inventory['verification'] = {'configured_packages': len(records), 'own_archives_verified': len(records),
                                  'installed_files_and_links_verified': files,
                                  'installed_status_sha256': status_before,
                                  'record_sha256': record_hashes, 'installed_state_unchanged': True}
    return inventory
