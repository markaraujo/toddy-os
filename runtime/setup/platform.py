"""Product host-safety guard: never acquire native packages on a foreign/live OS."""
import os
from pathlib import Path

from .pending import SetupError
from .releases import private_metadata


def installed_toddy(*,read=private_metadata,link=os.readlink,exists=lambda path:path.exists() or path.is_symlink()):
    path=Path('/etc/os-release')
    try:
        target=link(path)
    except OSError:
        target=None
    if target is not None:
        if target not in ('../usr/lib/os-release','/usr/lib/os-release'):
            raise SetupError('native_os_unsupported')
        path=Path('/usr/lib/os-release')
    try:
        data=read(path).decode('utf-8',errors='strict')
        identities=[line[3:] for line in data.splitlines() if line.startswith('ID=')]
        if len(identities)!=1 or identities[0] not in ('toddy','"toddy"',"'toddy'"):
            raise SetupError('native_os_unsupported')
        commandline=Path('/proc/cmdline').read_text().split()
        if 'toddy.live' in commandline or exists(Path('/run/toddy/live-session')):
            raise SetupError('acquisition_installed_owner_required')
    except (OSError,UnicodeError):
        raise SetupError('native_os_unsupported') from None
