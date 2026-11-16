"""Installed-root identity/login hygiene; no credentials in plans or receipts."""
import os
from pathlib import Path
import re
import select
import stat
import time

from .disk_plan import InstallError


def regular(root, relative, data, mode=0o644):
    """Write only below an owned real target tree; refuse symlink destinations."""
    target = Path(root)
    if target.is_symlink():
        raise InstallError('installer_target_root_symlink')
    for part in Path(relative).parts[:-1]:
        target /= part
        if target.is_symlink():
            raise InstallError('installer_identity_symlink')
        target.mkdir(exist_ok=True)
    target /= Path(relative).name
    if target.exists() and (target.is_symlink() or not target.is_file()):
        raise InstallError('installer_identity_not_regular')
    if target.is_symlink():
        raise InstallError('installer_identity_symlink')
    temporary = target.with_name(target.name + '.toddy-new')
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, mode)
    try:
        with os.fdopen(fd, 'wb', closefd=False) as stream:
            stream.write(data)
            stream.flush()
            os.fsync(fd)
        os.fchmod(fd, mode)
        os.replace(temporary, target)
        directory = os.open(target.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        os.close(fd)
        if temporary.exists():
            temporary.unlink()


def write_identity(root, plan, *, root_uuid, esp_uuid=None):
    options = plan['options']
    root = Path(root)
    for value in (root_uuid, esp_uuid):
        if value is not None and not re.fullmatch('[A-Fa-f0-9-]{4,40}', value):
            raise InstallError('installer_filesystem_uuid')
    machine = root / 'etc/machine-id'
    if machine.is_symlink() or (machine.exists() and machine.read_bytes() not in (b'', b'uninitialized\n')):
        raise InstallError('installer_payload_inherited_machine_id')
    regular(root, 'etc/machine-id', b'')
    regular(root, 'etc/hostname', (options['hostname'] + '\n').encode())
    regular(root, 'etc/locale.conf', ('LANG=' + options['locale'] + '\n').encode())
    timezone = root / 'usr/share/zoneinfo' / options['timezone']
    if not timezone.is_file() or timezone.is_symlink():
        raise InstallError('installer_target_timezone_unavailable')
    regular(root, 'etc/localtime', timezone.read_bytes())
    text = 'UUID=' + root_uuid + ' / ext4 defaults 0 1\n'
    if options['boot_mode'] == 'uefi':
        if esp_uuid is None:
            raise InstallError('installer_esp_uuid_required')
        text += 'UUID=' + esp_uuid + ' /boot/efi vfat umask=0077 0 2\n'
    regular(root, 'etc/fstab', text.encode())


def create_owner(root, plan, credential_fd, system):
    """Consume a bounded protected password pipe through native chpasswd stdin.

    Calamares' dedicated account flow supplies this private FD. It is never a
    JSON field, argv, environment variable, journal value or model input.
    """
    if type(credential_fd) is not int or not stat.S_ISFIFO(os.fstat(credential_fd).st_mode):
        raise InstallError('installer_private_login_pipe_required')
    if not select.select([credential_fd], [], [], 5)[0]:
        raise InstallError('installer_login_pipe_timeout')
    deadline = time.monotonic() + 5
    secret = bytearray()
    while True:
        if not select.select([credential_fd], [], [], max(0, deadline - time.monotonic()))[0]:
            raise InstallError('installer_login_pipe_timeout')
        chunk = os.read(credential_fd, 1025 - len(secret))
        if not chunk:
            break
        secret.extend(chunk)
        if len(secret) > 1024:
            raise InstallError('installer_login_password_bounds')
    password = bytes(secret)
    if not 12 <= len(password) <= 1024 or any(c in password for c in (b'\n', b'\r', b'\x00')):
        raise InstallError('installer_login_password_bounds')
    owner = plan['options']
    prefix = ['/usr/bin/chroot', str(root)]
    system.run([*prefix, '/usr/sbin/groupadd', '--gid', str(owner['gid']), owner['username']])
    system.run([*prefix, '/usr/sbin/useradd', '--uid', str(owner['uid']), '--gid', str(owner['gid']),
        '--create-home', '--shell', '/bin/bash', owner['username']])
    try:
        system.run([*prefix, '/usr/sbin/chpasswd'], data=owner['username'].encode() + b':' + password + b'\n')
    finally:
        password = b''  # no forensic secure-erasure claim for Python buffers


def audit_hygiene(root, plan):
    """Reject inherited state; never sanitize a dirty builder-root into a payload."""
    root = Path(root)
    forbidden = ['root/.ssh', 'root/.gnupg', 'root/.local/share/keyrings',
        'root/.bash_history', 'var/lib/systemd/random-seed', 'var/lib/systemd/credential.secret',
        'var/lib/NetworkManager/secret_key',
        'var/lib/toddy-executor', 'etc/systemd/system/getty@tty1.service.d/autologin.conf',
        'etc/systemd/system/serial-getty@ttyS0.service.d/autologin.conf']
    for relative in forbidden:
        if (root / relative).exists() or (root / relative).is_symlink():
            raise InstallError('installer_inherited_private_or_live_state')
    if list((root / 'etc/ssh').glob('ssh_host_*_key')):
        raise InstallError('installer_inherited_ssh_identity')
    if list((root / 'etc/NetworkManager/system-connections').glob('*')):
        raise InstallError('installer_inherited_network_credentials')
    machine = root / 'etc/machine-id'
    if machine.is_symlink() or not machine.is_file() or machine.read_bytes() != b'':
        raise InstallError('installer_machine_identity_not_fresh')
    dbus_id = root / 'var/lib/dbus/machine-id'
    if dbus_id.is_symlink():
        if os.readlink(dbus_id) != '/etc/machine-id':
            raise InstallError('installer_dbus_identity_not_fresh')
    elif dbus_id.exists() and dbus_id.read_bytes() != b'':
        raise InstallError('installer_dbus_identity_not_fresh')
    owner = plan['options']
    passwd = (root / 'etc/passwd').read_text().splitlines()
    found = False
    for line in passwd:
        fields = line.split(':')
        if len(fields) != 7:
            raise InstallError('installer_passwd_invalid')
        user, _, uid, gid, _, home, shell = fields
        if user in ('lfs', 'toddy', 'toddy-live', 'builder'):
            raise InstallError('installer_live_account_retained')
        if user == owner['username']:
            if (int(uid), int(gid), home, shell) != (owner['uid'], owner['gid'], '/home/' + user, '/bin/bash'):
                raise InstallError('installer_owner_identity')
            found = True
        elif 1000 <= int(uid) < 65534:
            raise InstallError('installer_unexpected_personal_account')
    if not found:
        raise InstallError('installer_owner_missing')
    homes = root / 'home'
    if homes.is_symlink() or not homes.is_dir() or sorted(p.name for p in homes.iterdir()) != [owner['username']]:
        raise InstallError('installer_inherited_home')
    home = homes / owner['username']
    if home.is_symlink() or home.stat().st_uid != owner['uid'] or home.stat().st_gid != owner['gid']:
        raise InstallError('installer_owner_home_ownership')
    for relative in ('.ssh', '.gnupg', '.mozilla', '.local/share/keyrings'):
        if (home / relative).exists():
            raise InstallError('installer_owner_inherited_credentials')
    for path in root.glob('etc/gdm/*'):
        if path.is_file() and re.search(r'^\s*AutomaticLogin(?:Enable)?\s*=\s*(?![Ff]alse\b|[Nn]o\b|0\b)\S+', path.read_text(), re.MULTILINE):
            raise InstallError('installer_live_autologin_retained')
    return {'verified': True, 'fresh_machine_identity': True, 'owner_uid': owner['uid']}
