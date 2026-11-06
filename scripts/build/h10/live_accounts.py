"""Create fresh book-derived image accounts without reading builder credentials.

This is an assembly component, not an installed-target account migration tool.
The caller supplies a fresh private image stage under its milestone guard.
"""
import hashlib
import json
import os
from pathlib import Path
import re

BASELINE = Path(__file__).resolve().parents[3] / 'config/live-account-baseline.json'


def account_data(baseline):
    passwd = [row.split(':') for row in baseline['passwd'].splitlines()]
    groups = [row.split(':') for row in baseline['group'].splitlines()]
    if (any(len(row) != 7 or row[1] != 'x' for row in passwd)
            or any(len(row) != 4 or row[1] != 'x' for row in groups)):
        raise ValueError('Malformed book account baseline')
    users = {row[0]: row for row in passwd}
    group_names = {row[0]: row for row in groups}
    if (len(users) != len(passwd) or len(group_names) != len(groups)
            or len({row[2] for row in passwd}) != len(passwd)
            or len({row[2] for row in groups}) != len(groups)):
        raise ValueError('Duplicate book account identity')
    if any(not re.fullmatch(r'[a-z_][a-z0-9_-]*', name) for name in (*users, *group_names)):
        raise ValueError('Unexpected account name')
    if (users.get('root') != 'root:x:0:0:root:/root:/bin/bash'.split(':')
            or group_names.get('root') != ['root', 'x', '0', '']
            or 'tester' in users or 'tester' in group_names):
        raise ValueError('Unexpected root or builder test account')
    for row in passwd:
        if not row[2].isdigit() or not row[3].isdigit() or row[3] not in {group[2] for group in groups}:
            raise ValueError('Unresolved numeric account identity')
        if row[0] != 'root' and (int(row[2]) == 0 or row[6] != '/usr/bin/false'):
            raise ValueError('Unexpected privileged or interactive service account')
    for row in groups:
        if not row[2].isdigit():
            raise ValueError('Unresolved numeric group identity')
        if any(name not in users for name in row[3].split(',') if name):
            raise ValueError('Unresolved group membership')
    # No inherited hashes, age/expiry state or per-user sub-ID allocations.
    # A locked root is compatible with a separately reviewed live-console
    # policy; this component enables no login service or password bypass.
    return {
        'etc/passwd': (baseline['passwd'], 0o644),
        'etc/group': (baseline['group'], 0o644),
        'etc/shadow': (''.join(row[0] + ':!:::::::\n' for row in passwd), 0o600),
        'etc/gshadow': (''.join(row[0] + ':!::' + row[3] + '\n' for row in groups), 0o600),
        'etc/subuid': ('', 0o644), 'etc/subgid': ('', 0o644),
        'etc/machine-id': ('', 0o444),
    }, len(users), len(groups)


def stage_accounts(root, baseline=None):
    root = Path(root)
    if root.resolve() != root or not root.is_dir():
        raise ValueError('Fresh image stage must be a canonical existing directory')
    if os.geteuid() != 0:
        raise ValueError('Fresh image account ownership requires disposable-guest root')
    baseline = json.loads(BASELINE.read_text()) if baseline is None else baseline
    files, users, groups = account_data(baseline)
    # Refuse old state instead of overwriting or sanitizing inherited secrets.
    forbidden = [*files, 'var/lib/dbus/machine-id', 'etc/.pwd.lock',
                 'etc/passwd-', 'etc/group-', 'etc/shadow-', 'etc/gshadow-',
                 'home/tester', 'root/.ssh', 'root/.gnupg']
    for relative in forbidden:
        path = root / relative
        if path.exists() or path.is_symlink() or path.parent.resolve() != path.parent:
            raise ValueError('Image account input already exists or redirects: ' + relative)
    home = root / 'root'
    if home.exists() and (home.is_symlink() or not home.is_dir() or any(home.iterdir())):
        raise ValueError('Live root home must be empty; preserve unexpected state')
    for relative, (data, mode) in files.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('x') as stream:
            stream.write(data)
        path.chmod(mode)
        os.chown(path, 0, 0)
    if not home.exists():
        home.mkdir()
    home.chmod(0o700)
    os.chown(home, 0, 0)
    return {'users': users, 'groups': groups, 'passwords_locked': True,
            'builder_account_included': False, 'machine_id_empty': True,
            'baseline_sha256': hashlib.sha256(json.dumps(baseline, sort_keys=True).encode()).hexdigest(),
            'generated_paths': sorted(files), 'live_login_verified': False}
