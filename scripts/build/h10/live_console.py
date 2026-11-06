"""Stage the foundation live-console profile into a fresh disposable image.

No installed-target entry point: the assembly caller must enforce the H10 gate
and record these generated paths separately from native package payload.
"""
import hashlib
import os
from pathlib import Path

UNITS = {'getty@tty1.service': 'getty@.service',
         'serial-getty@ttyS0.service': 'serial-getty@.service'}
MARKER = 'run/toddy/live-session'


def profile_files():
    files = {'usr/share/toddy/live.issue': (
        'Toddy OS experimental live foundation\n'
        'Local console: automatic root login. Changes are volatile.\n'
        'This profile is for live media, not an installed system.\n\n')}
    for unit in UNITS:
        serial = '--keep-baud 115200,57600,38400,9600 ' if unit.startswith('serial-') else ''
        files['etc/systemd/system/' + unit + '.d/50-toddy-live.conf'] = (
            '[Unit]\nConditionKernelCommandLine=toddy.live\n'
            'ConditionPathExists=/run/toddy/live-session\n\n'
            '[Service]\nExecStart=\n'
            'ExecStart=-/usr/sbin/agetty --noreset --noclear '
            '--issue-file /usr/share/toddy/live.issue --autologin root '
            + serial + '- ${TERM}\n')
    return files


def stage_console(root):
    root = Path(root)
    if root.resolve() != root or not root.is_dir() or os.geteuid() != 0:
        raise ValueError('Live console requires a canonical disposable image and guest root')
    # This profile does not unlock accounts, copy credentials, or generate the
    # runtime marker. Only /init creates that marker after verified root setup.
    for relative in ('etc/passwd', 'etc/shadow'):
        path = root / relative
        if path.is_symlink() or path.parent.resolve() != path.parent or not path.is_file():
            raise ValueError('Fresh image account files are required')
    passwd = (root / 'etc/passwd').read_text().splitlines()
    shadow = (root / 'etc/shadow').read_text().splitlines()
    if ('root:x:0:0:root:/root:/bin/bash' not in passwd
            or 'root:!:::::::' not in shadow):
        raise ValueError('Fresh locked root account is required')
    marker = root / MARKER
    if marker.exists() or marker.is_symlink() or marker.parent.resolve() != marker.parent:
        raise ValueError('A runtime live-session marker must not be baked into the image')
    files = profile_files()
    links = {'etc/systemd/system/getty.target.wants/' + unit:
             '/usr/lib/systemd/system/' + template for unit, template in UNITS.items()}
    retained = []
    # Preflight everything before writing. A normal Systemd installation already
    # supplies tty1's exact enablement link; retain its existing ownership.
    for relative in (*files, *links):
        path = root / relative
        if path.parent.resolve() != path.parent:
            raise ValueError('Redirected live-console parent: ' + relative)
        if path.exists() or path.is_symlink():
            if (relative in links and path.is_symlink()
                    and path.readlink().as_posix() == links[relative]
                    and path.lstat().st_uid == path.lstat().st_gid == 0):
                retained.append(relative)
            else:
                raise ValueError('Preserve existing live-console input: ' + relative)
    for relative, text in files.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('x') as stream:
            stream.write(text)
        path.chmod(0o644)
        os.chown(path, 0, 0)
    for relative, target in links.items():
        if relative not in retained:
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.symlink_to(target)
            os.chown(path, 0, 0, follow_symlinks=False)
    return {'files': {path: hashlib.sha256(text.encode()).hexdigest()
                      for path, text in files.items()},
            'enablement_links': links, 'retained_owned_links': retained,
            'runtime_marker_embedded': False, 'accounts_unchanged': True,
            'automatic_login_consoles': ['tty1', 'ttyS0'],
            'native_boot_verified': False}
