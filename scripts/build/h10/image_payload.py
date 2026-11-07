"""Independently compare a private image's native ownership and actual payload.

This does not classify unowned/generated data, dependency closure or credentials.
The assembly caller must retain and pass those separate checks before release.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import stat

from fresh_directories import APT_DIRECTORIES
from live_configuration import LIVE_FSTAB
import package_database
from root_inventory import FRESH_DIRECTORIES


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def file_digests(path):
    sha, md5 = hashlib.sha256(), hashlib.md5(usedforsecurity=False)
    with path.open('rb') as stream:
        while chunk := stream.read(1024 * 1024):
            sha.update(chunk)
            md5.update(chunk)
    return sha.hexdigest(), md5.hexdigest()


def audit(backend, image, records_directory=Path('/var/log/toddy/packages'),
          cache_directory=Path('/var/cache/toddy/packages'), *, live_profile=False):
    image = Path(image)
    if (not backend.native or os.geteuid() != 0 or image.resolve() != image or not image.is_dir()
            or not any(image != backend.target / area and image.is_relative_to(backend.target / area)
                       for area in ('tmp', 'sources/stage'))):
        raise ValueError('Payload audit requires a private canonical native image')
    database = image / 'var/lib/dpkg'
    before = package_database.snapshot(database)
    virtual_database = '/' + str(database.relative_to(backend.target))
    identity = backend.run('dpkg-query', '--admindir=' + virtual_database, '-W',
                           '-f=' + package_database.QUERY, capture_output=True, text=True).stdout
    records, record_hashes, entries, owners, native_md5 = {}, {}, {}, {}, {}
    for line in identity.splitlines():
        name, version, architecture, status = line.split('\t')
        if (status != 'install ok installed' or name in records
                or not re.fullmatch(r'[a-z0-9][a-z0-9+.-]+', name)
                or not re.fullmatch(r'[0-9][0-9A-Za-z.+:~_-]*', version)
                or architecture not in {'amd64', 'all'}):
            raise ValueError('Unconfigured or invalid native image package identity')
        stem = f'{name}_{version}_{architecture}'
        record_path, archive = Path(records_directory) / (stem + '.json'), Path(cache_directory) / (stem + '.deb')
        if record_path.resolve() != record_path or archive.resolve() != archive:
            raise ValueError('Own package provenance redirects')
        raw = record_path.read_bytes()
        record = json.loads(raw)
        if (record.get('installed') is not True or record['name'] != name or record['version'] != version
                or digest(archive) != record['archive_sha256']):
            raise ValueError('Image package differs from verified own archive: ' + name)
        records[name] = record
        record_hashes[str(record_path)] = hashlib.sha256(raw).hexdigest()
        for path, row in record['payload'].items():
            package_database.canonical_path(path)
            if path == '/':
                raise ValueError('The image root cannot be an ordinary package entry')
            if path in entries and (not row.get('directory') or entries[path] != row):
                raise ValueError('Conflicting image package ownership: ' + path)
            entries[path] = row
            owners.setdefault(path, []).append(name)
    namespace = package_database.validate_info(database, records, before)
    for name in records:
        for line in (database / 'info' / (name + '.md5sums')).read_text().splitlines():
            value, relative = line.split('  ', 1)
            native_md5['/' + relative] = value
    checked = backend.run('dpkg', '--admindir=' + virtual_database, '--audit', capture_output=True, text=True)
    if checked.stdout or checked.stderr:
        raise ValueError('Native image database audit produced diagnostics')
    if live_profile and owners.get('/etc/fstab') != ['toddy-base-config']:
        raise ValueError('Live profile requires the accepted base package fstab')
    if live_profile and '/etc/fstab' not in (database / 'info/toddy-base-config.conffiles').read_text().splitlines():
        raise ValueError('Live fstab must retain its native conffile identity')
    original_fstab_md5 = None
    if live_profile:
        source = backend.target / 'etc/fstab'
        if source.resolve() != source or not source.is_file():
            raise ValueError('Original owned base fstab is missing or redirects')
        source_sha, original_fstab_md5 = file_digests(source)
        if source_sha != entries['/etc/fstab']['sha256']:
            raise ValueError('Original base fstab differs from the accepted package record')
    findings, transformations = [], []
    device = image.stat().st_dev
    for virtual, original in sorted(entries.items()):
        expected = dict(original)
        if live_profile and virtual == '/etc/fstab':
            expected['sha256'] = hashlib.sha256(LIVE_FSTAB.encode()).hexdigest()
        if live_profile and original.get('directory'):
            name = virtual[1:]
            if name in FRESH_DIRECTORIES:
                expected.update(mode=stat.S_IFDIR | FRESH_DIRECTORIES[name], uid=0, gid=0)
            elif name in APT_DIRECTORIES:
                mode, uid, gid = APT_DIRECTORIES[name]
                expected.update(mode=stat.S_IFDIR | mode, uid=uid, gid=gid)
        path = image / virtual[1:]
        problems = []
        if path.parent.resolve() != path.parent:
            problems.append('Package parent redirects outside its physical namespace')
        else:
            try:
                current = path.lstat()
            except FileNotFoundError:
                problems.append('Recorded payload missing')
            else:
                if current.st_dev != device:
                    problems.append('Package path crosses a filesystem')
                if (current.st_mode, current.st_uid, current.st_gid) != (expected['mode'], expected['uid'], expected['gid']):
                    problems.append('Package type/mode/owner/group differs')
                if current.st_dev != device:
                    pass  # Never read a file across the refused filesystem boundary.
                elif 'sha256' in expected:
                    actual_sha, actual_md5 = file_digests(path) if stat.S_ISREG(current.st_mode) else (None, None)
                    if actual_sha != expected['sha256']:
                        problems.append('Package regular file bytes/type differ')
                    packaged_md5 = original_fstab_md5 if live_profile and virtual == '/etc/fstab' else actual_md5
                    if packaged_md5 != native_md5[virtual]:
                        problems.append('Native stored MD5 differs from the package bytes')
                elif 'symlink' in expected:
                    if not stat.S_ISLNK(current.st_mode) or path.readlink().as_posix() != expected['symlink']:
                        problems.append('Package link target/type differs')
                elif not original.get('directory') or not stat.S_ISDIR(current.st_mode):
                    problems.append('Unsupported or changed package entry type')
        if problems:
            findings.append({'path': virtual, 'owners': owners[virtual], 'problems': problems})
        elif expected != original:
            transformations.append({'path': virtual, 'owners': owners[virtual],
                                    'packaged': original, 'live_profile': expected})
    if package_database.snapshot(database) != before:
        raise ValueError('Image database changed during payload audit')
    if any(digest(Path(path)) != sha for path, sha in record_hashes.items()):
        raise ValueError('Own-package provenance changed during image audit')
    return {'scope': 'Configured own-package identities, native ownership namespace and actual recorded payload',
            'configured_packages': len(records), 'own_archives_verified': len(records),
            'package_names': sorted(records), 'unique_owned_entries': len(entries),
            'owned_files_and_links': sum(not row.get('directory') for row in entries.values()),
            'native_database_namespace': namespace, 'native_database_audit_clean': True,
            'record_sha256': record_hashes, 'qualified_live_transformations': transformations,
            'findings': findings, 'owned_payload_check_passed': not findings,
            'unowned_generated_state_audited': False, 'dependency_closure_verified': False,
            'credentials_or_boot_accepted': False}
