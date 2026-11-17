"""Installed-root identity/login hygiene; no credentials in plans or receipts."""
import os
from pathlib import Path
import re
import select
import stat
import time

from .disk_plan import InstallError


def regular(root, relative, data, mode=0o644, *, replace_known_symlink=None):
    """Write only below an owned real target tree; refuse symlink destinations."""
    target = Path(root)
    if target.is_symlink():
        raise InstallError('installer_target_root_symlink')
    for part in Path(relative).parts[:-1]:
        target /= part
        if target.is_symlink():
            raise InstallError('installer_identity_symlink')
        target.mkdir(mode=0o755, exist_ok=True)
    target /= Path(relative).name
    was_link = target.is_symlink()
    if was_link:
        if replace_known_symlink is None or os.readlink(target) != replace_known_symlink:
            raise InstallError('installer_identity_symlink')
    elif target.exists() and not target.is_file():
        raise InstallError('installer_identity_not_regular')
    temporary = target.with_name(target.name + '.toddy-new')
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, mode)
    try:
        with os.fdopen(fd, 'wb', closefd=False) as stream:
            stream.write(data)
            stream.flush()
            os.fsync(fd)
        os.fchmod(fd, mode)
        if was_link and (not target.is_symlink() or os.readlink(target) != replace_known_symlink):
            raise InstallError('installer_identity_changed_before_replace')
        os.replace(temporary, target)
        directory = os.open(target.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
        metadata = target.lstat()
        if not stat.S_ISREG(metadata.st_mode) or stat.S_IMODE(metadata.st_mode) != mode or target.read_bytes() != data:
            raise InstallError('installer_identity_write_postcondition')
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
    # H10's reviewed UTC link is generated configuration, not an arbitrary
    # filesystem redirect. Replace that exact leaf atomically, preserving the
    # zoneinfo source; refuse every unrecognized link without following it.
    regular(root, 'etc/localtime', timezone.read_bytes(),
        replace_known_symlink='../usr/share/zoneinfo/UTC')
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
    group_path=Path(root)/'etc/group'
    if group_path.is_symlink() or not group_path.is_file():
        raise InstallError('installer_admin_group_missing')
    wheels=[line.split(':') for line in group_path.read_text().splitlines() if line.startswith('wheel:')]
    if len(wheels)!=1 or len(wheels[0])!=4 or wheels[0][2]!='97' or wheels[0][3]!='':
        raise InstallError('installer_admin_group_baseline')
    prefix = ['/usr/sbin/chroot', str(root)]
    system.run([*prefix, '/usr/sbin/groupadd', '--gid', str(owner['gid']), owner['username']])
    system.run([*prefix, '/usr/sbin/useradd', '--uid', str(owner['uid']), '--gid', str(owner['gid']),
        '--groups','wheel','--create-home', '--shell', '/bin/bash', owner['username']])
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
        'var/lib/toddy-executor','var/lib/toddy/executor','var/lib/toddy/installer',
        'root/.config/toddy','etc/systemd/system/getty@tty1.service.d/autologin.conf',
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
        if user in ('lfs', 'tester', 'toddy', 'toddy-live', 'builder'):
            raise InstallError('installer_live_account_retained')
        if user == owner['username']:
            if (int(uid), int(gid), home, shell) != (owner['uid'], owner['gid'], '/home/' + user, '/bin/bash'):
                raise InstallError('installer_owner_identity')
            found = True
        elif 1000 <= int(uid) < 65534:
            raise InstallError('installer_unexpected_personal_account')
    if not found:
        raise InstallError('installer_owner_missing')
    group=root/'etc/group'
    if group.is_symlink() or not group.is_file():raise InstallError('installer_admin_group_missing')
    wheels=[line.split(':') for line in group.read_text().splitlines() if line.startswith('wheel:')]
    if len(wheels)!=1 or len(wheels[0])!=4 or wheels[0][2]!='97' or wheels[0][3]!=owner['username']:
        raise InstallError('installer_owner_admin_membership')
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
