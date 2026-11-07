"""Generate fresh live filesystem/time/resolver settings in private image staging.

The assembler supplies the accepted base package's original fstab SHA-256 and
retains this report as an explicit conffile transformation. No package database
is rewritten, and installed-target/host configuration is never an allowed root.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import stat

DEFAULT_LINKS = {'etc/localtime': '../usr/share/zoneinfo/UTC',
                 'etc/resolv.conf': '/run/systemd/resolve/stub-resolv.conf'}
LIVE_FSTAB = (
    '# Toddy OS live filesystem profile.\n'
    '# Verified media, compressed root and volatile overlay are mounted by /init.\n'
    '# No disk filesystem or swap is activated from this file.\n'
    '# The installer must generate a separate profile for the selected disk.\n')


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def stage_live_configuration(backend, image, expected_fstab_sha256, links,
                             records_directory=Path('/var/log/toddy/packages')):
    image = Path(image)
    if (not backend.native or os.geteuid() != 0 or image.resolve() != image or not image.is_dir()
            or not any(image.is_relative_to(backend.target / area) for area in ('tmp', 'sources/stage'))):
        raise ValueError('Live configuration requires a fresh private native image stage')
    if links != DEFAULT_LINKS or not re.fullmatch(r'[0-9a-f]{64}', expected_fstab_sha256):
        raise ValueError('Unreviewed live defaults or missing base fstab identity')
    fstab = image / 'etc/fstab'
    partial = image / 'etc/.toddy-live-fstab.part'
    if fstab.parent.resolve() != fstab.parent:
        raise ValueError('Image configuration parent redirects')
    info = fstab.lstat()
    if ((info.st_mode, info.st_uid, info.st_gid, info.st_nlink) != (stat.S_IFREG | 0o644, 0, 0, 1)
            or info.st_dev != image.stat().st_dev
            or digest(fstab) != expected_fstab_sha256):
        raise ValueError('Preserve changed/unreviewed base fstab')
    if partial.exists() or partial.is_symlink():
        raise ValueError('Preserve interrupted live configuration stage')
    for relative in links:
        path = image / relative
        if path.exists() or path.is_symlink() or path.parent.resolve() != path.parent:
            raise ValueError('Preserve existing/redirected live default: ' + relative)
    runtime = image / 'run'
    if not runtime.is_dir() or runtime.resolve() != runtime or runtime.stat().st_dev != image.stat().st_dev:
        raise ValueError('Fresh physical runtime directories are required')
    for parent, directories, files in os.walk(runtime, followlinks=False):
        if files:
            raise ValueError('Image runtime tree contains inherited data')
        for name in directories:
            path = Path(parent) / name
            if path.is_symlink() or path.stat().st_dev != image.stat().st_dev:
                raise ValueError('Image runtime directory redirects or crosses a filesystem')
    version, architecture, status = backend.run('dpkg-query', '-W', '-f=${Version}\t${Architecture}\t${Status}',
                                               'tzdata', capture_output=True, text=True).stdout.split('\t')
    record = json.loads((Path(records_directory) / f'tzdata_{version}_{architecture}.json').read_text())
    timezone = image / 'usr/share/zoneinfo/UTC'
    row = record['payload']['/usr/share/zoneinfo/UTC']
    if (status != 'install ok installed' or not record['installed'] or record['name'] != 'tzdata'
            or record['version'] != version or timezone.parent.resolve() != timezone.parent):
        raise ValueError('Native timezone provenance differs')
    actual = timezone.lstat()
    if ((actual.st_mode, actual.st_uid, actual.st_gid) != (row['mode'], row['uid'], row['gid'])
            or actual.st_dev != image.stat().st_dev or not stat.S_ISREG(actual.st_mode) or digest(timezone) != row['sha256']):
        raise ValueError('Image timezone differs from native owned UTC data')
    # Preflight completed. Any interrupted attempt remains a partial *image*
    # generation; preserve it and reconstruct a fresh stage instead of guessing
    # which writes to replay. Never replace installed configuration in place.
    with partial.open('xb') as stream:
        stream.write(LIVE_FSTAB.encode())
        stream.flush()
        os.fchmod(stream.fileno(), 0o644)
        os.fchown(stream.fileno(), 0, 0)
        os.fsync(stream.fileno())
    if digest(fstab) != expected_fstab_sha256:
        raise ValueError('Base fstab changed after preflight')
    partial.replace(fstab)
    for relative, target in links.items():
        path = image / relative
        path.symlink_to(target)
        os.chown(path, 0, 0, follow_symlinks=False)
    descriptor = os.open(image / 'etc', os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    if fstab.read_text() != LIVE_FSTAB or any((image / name).readlink().as_posix() != target for name, target in links.items()):
        raise ValueError('Live configuration readback differs')
    return {'modified_conffile': '/etc/fstab', 'before_sha256': expected_fstab_sha256,
            'after_sha256': digest(fstab), 'generated_links': dict(links),
            'timezone': {'version': version, 'sha256': row['sha256'], 'archive_sha256': record['archive_sha256']},
            'fstab_mount_entries': 0, 'runtime_data_imported': False,
            'package_database_rewritten': False, 'boot_or_dns_verified': False,
            'required_assembly_check': 'Original fstab identity must come from the accepted base package; retain its native conffile metadata.'}
