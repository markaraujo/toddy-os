"""Reject inherited identity/authentication state in a fresh foundation image.

Read-only, independent of package ownership. This bounded path policy does not
detect arbitrary credentials embedded in other configuration or documentation.
The assembly caller owns the private stage, exclusive lock and milestone gate.
Never return unexpected file contents, hashes, attributes or child filenames.
"""
import os
from pathlib import Path
import stat

from live_accounts import account_data

ABSENT = (
    'etc/.pwd.lock', 'etc/passwd-', 'etc/group-', 'etc/shadow-', 'etc/gshadow-',
    'etc/subuid-', 'etc/subgid-', 'etc/apt/auth.conf',
    'var/lib/systemd/credential.secret', 'var/lib/systemd/random-seed',
    'var/lib/systemd/entropy', 'var/lib/cloud',
)
EMPTY_DIRECTORIES = (
    'root', 'home', 'etc/apt/auth.conf.d', 'etc/ssl/private',
    'etc/NetworkManager/system-connections', 'var/lib/iwd',
    *(f'{base}/credstore{suffix}' for base in ('etc', 'run', 'usr/lib')
      for suffix in ('', '.encrypted')),
)


def audit(image, baseline):
    image = Path(image)
    if image.resolve() != image or not image.is_dir() or image == Path('/'):
        raise ValueError('Identity audit requires a canonical private image directory')
    device = image.stat().st_dev
    files, users, groups = account_data(baseline)
    findings = []

    def finding(name, reason):
        findings.append({'path': '/' + name, 'reason': reason})

    def entry(name):
        # Inspect every ancestor without following links, including dangling
        # ones. An absent parent makes the policy path absent; a redirected or
        # mounted parent is a finding, never permission to read outside image.
        parts = Path(name).parts
        for index in range(1, len(parts) + 1):
            relative = '/'.join(parts[:index])
            try:
                info = (image / relative).lstat()
            except FileNotFoundError:
                return None
            if info.st_dev != device or (index < len(parts) and not stat.S_ISDIR(info.st_mode)):
                finding(relative, 'Policy path crosses a nonphysical or mounted parent')
                return None
        return info

    def regular(name, data, mode):
        info = entry(name)
        if info is None:
            finding(name, 'Required fresh account file is missing or inaccessible')
            return
        if (info.st_mode != stat.S_IFREG | mode or info.st_uid != 0 or info.st_gid != 0
                or info.st_nlink != 1 or info.st_size != len(data)):
            finding(name, 'Fresh account type, ownership, mode, link count or size differs')
            return
        fd = os.open(image / name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        try:
            current = os.fstat(fd)
            if ((current.st_dev, current.st_ino, current.st_mode, current.st_size)
                    != (info.st_dev, info.st_ino, info.st_mode, info.st_size)):
                raise ValueError('Private image changed during identity inspection')
            if os.listxattr(fd) or os.read(fd, len(data) + 1) != data:
                finding(name, 'Fresh account bytes or extended attributes differ')
        finally:
            os.close(fd)

    for name, (data, mode) in sorted(files.items()):
        regular(name, data.encode(), mode)
    for name in ABSENT:
        if entry(name) is not None:
            finding(name, 'Inherited authentication, identity or initialization state is forbidden')
    for name in EMPTY_DIRECTORIES:
        info = entry(name)
        if info is None:
            if name == 'root':
                finding(name, 'Required fresh root home is absent')
            continue
        if not stat.S_ISDIR(info.st_mode):
            finding(name, 'Credential/home location must be a physical empty directory')
            continue
        if name == 'root' and (stat.S_IMODE(info.st_mode), info.st_uid, info.st_gid) != (0o700, 0, 0):
            finding(name, 'Fresh root home metadata differs')
        if os.listxattr(image / name) or any((image / name).iterdir()):
            finding(name, 'Credential/home location has entries or extended attributes')
    name = 'var/lib/dbus/machine-id'
    info = entry(name)
    if info is not None and (not stat.S_ISLNK(info.st_mode)
            or info.st_uid != 0 or info.st_gid != 0
            or os.readlink(image / name) != '/etc/machine-id'
            or os.listxattr(image / name, follow_symlinks=False)):
        finding(name, 'Only the canonical root-owned DBus identity alias is permitted')
    name = 'etc/ssh'
    info = entry(name)
    if info is not None:
        if not stat.S_ISDIR(info.st_mode):
            finding(name, 'SSH configuration directory is redirected or nonphysical')
        elif any(path.name.startswith('ssh_host_') for path in (image / name).iterdir()):
            finding(name, 'Generated SSH host identity is forbidden')
    return {'fresh_identity_check_passed': not findings, 'findings': findings,
            'account_files_checked': len(files), 'users': users, 'groups': groups,
            'absent_paths_checked': len(ABSENT), 'empty_locations_checked': len(EMPTY_DIRECTORIES),
            'unexpected_content_exported': False, 'package_ownership_grants_exception': False,
            'scope': 'Fresh foundation distribution before first boot, not an installed user system',
            'whole_image_credential_audit_accepted': False, 'boot_identity_generation_verified': False}
