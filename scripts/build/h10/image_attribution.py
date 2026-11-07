"""Declare image origins and reject undeclared or changed physical entries.

Owned records and the verified initial copy manifest are inputs, never discovered
permission grants. This is not dependency, secret-content or boot acceptance.
"""
import hashlib
import os
from pathlib import Path, PurePosixPath
import re
import stat

from copy_selected_root import snapshot, tree_names
from fresh_directories import APT_DIRECTORIES
from live_accounts import account_data
from live_configuration import DEFAULT_LINKS, LIVE_FSTAB
from live_console import profile_files, UNITS
import package_database
from root_inventory import FRESH_DIRECTORIES, MUTABLE_TREES

UNIT_PREFIX = '/usr/lib/systemd/system/'
SERVICE_LINKS = {
    'default.target': 'multi-user.target',
    'dbus-org.freedesktop.resolve1.service': 'systemd-resolved.service',
    'dbus-org.freedesktop.timesync1.service': 'systemd-timesyncd.service',
    'dbus-org.freedesktop.network1.service': 'systemd-networkd.service',
    'multi-user.target.wants/systemd-networkd.service': 'systemd-networkd.service',
    'sysinit.target.wants/systemd-resolved.service': 'systemd-resolved.service',
    'sysinit.target.wants/systemd-timesyncd.service': 'systemd-timesyncd.service',
    'sysinit.target.wants/systemd-network-generator.service': 'systemd-network-generator.service',
    **{'sockets.target.wants/' + name: name for name in (
        'systemd-networkd-resolve-hook.socket', 'systemd-resolved-monitor.socket',
        'systemd-networkd.socket', 'systemd-networkd-varlink-metrics.socket',
        'systemd-networkd-varlink.socket', 'systemd-resolved-varlink.socket')},
    'systemd-networkd-wait-online.service': None,
}
ARTIFACTS = {'loader-cache': 'etc/ld.so.cache', 'info-index': 'usr/share/info/dir',
             'acl-sidecar': 'usr/share/toddy/live-root.acl'}


def directory(mode=0o755, uid=0, gid=0):
    return {'mode': stat.S_IFDIR | mode, 'uid': uid, 'gid': gid, 'xattrs': {}}


def regular(text, mode=0o644):
    data = text.encode()
    return {'mode': stat.S_IFREG | mode, 'uid': 0, 'gid': 0, 'xattrs': {},
            'sha256': hashlib.sha256(data).hexdigest(), 'size': len(data)}


def symlink(target):
    return {'mode': stat.S_IFLNK | 0o777, 'uid': 0, 'gid': 0, 'xattrs': {}, 'symlink': target}


def add(plan, name, row, origin, *, transform=False):
    parsed = PurePosixPath(name)
    if (not name or parsed.is_absolute() or '..' in parsed.parts or parsed.as_posix() != name
            or '\0' in name or '\n' in name or not origin):
        raise ValueError('Noncanonical image attribution entry')
    if not {'mode', 'uid', 'gid', 'xattrs'} <= row.keys():
        raise ValueError('Incomplete image attribution metadata')
    if not any(test(row['mode']) for test in (stat.S_ISDIR, stat.S_ISREG, stat.S_ISLNK)):
        raise ValueError('Special nodes are not declared image payload')
    if stat.S_ISREG(row['mode']) and not re.fullmatch(r'[0-9a-f]{64}', row.get('sha256', '')):
        raise ValueError('Generated regular files require exact bytes')
    if stat.S_ISLNK(row['mode']) and not isinstance(row.get('symlink'), str):
        raise ValueError('Generated links require their exact target')
    previous = plan.get(name)
    if previous:
        if not transform and any(previous['expected'].get(key) != value for key, value in row.items()
                                 if key in previous['expected']):
            raise ValueError('Conflicting image attribution: ' + name)
        if not transform and not stat.S_ISDIR(row['mode']) and origin.startswith('package:'):
            raise ValueError('Duplicate native image file ownership: ' + name)
        previous['expected'] = dict(previous['expected'], **row)
        previous['origins'] = sorted(set(previous['origins']) | {origin})
    else:
        plan[name] = {'expected': dict(row), 'origins': [origin]}
    parent = parsed.parent.as_posix()
    if name != '.' and parent not in plan:
        add(plan, parent, directory(), 'generated-parent:' + origin)
    elif name != '.' and not stat.S_ISDIR(plan[parent]['expected']['mode']):
        raise ValueError('Declared image parent is not a physical directory')


def owned_plan(records, copied):
    root = copied['entries']['.']
    plan = {}
    add(plan, '.', {key: root[key] for key in ('mode', 'uid', 'gid', 'xattrs')}, 'verified-copy-root')
    if not records:
        raise ValueError('Empty native ownership cannot declare an image')
    for name, record in sorted(records.items()):
        if (record['name'] != name or record.get('installed') is not True
                or not re.fullmatch(r'[a-z0-9][a-z0-9+.-]+', name)):
            raise ValueError('Unaccepted native image record')
        for virtual, row in sorted(record['payload'].items(), key=lambda pair: (len(PurePosixPath(pair[0]).parts), pair[0])):
            package_database.canonical_path(virtual)
            relative = virtual[1:]
            if not relative:
                raise ValueError('Native record must not own the image root')
            source = copied['entries'].get(relative)
            if source is None and not (row.get('directory') and any(
                    relative == base or relative.startswith(base + '/') for base in (*FRESH_DIRECTORIES, *MUTABLE_TREES))):
                raise ValueError('Owned path lacks verified copy provenance: ' + virtual)
            expected = {key: row[key] for key in ('mode', 'uid', 'gid', 'sha256', 'symlink') if key in row}
            expected['xattrs'] = source['xattrs'] if source else {}
            add(plan, relative, expected, 'package:' + name)
    return plan


def declare_accounts(plan, baseline):
    files, _, _ = account_data(baseline)
    for name, (text, mode) in files.items():
        if name in plan:
            raise ValueError('Fresh account state must not inherit package payload')
        add(plan, name, regular(text, mode), 'fresh-accounts')
    if 'root' in plan and not stat.S_ISDIR(plan['root']['expected']['mode']):
        raise ValueError('Root home cannot replace a native file')
    add(plan, 'root', directory(0o700), 'fresh-accounts', transform=True)


def declare_fresh(plan, report):
    rows = report['directories']
    for name, mode in FRESH_DIRECTORIES.items():
        if rows.get(name) != {'mode': mode, 'uid': 0, 'gid': 0}:
            raise ValueError('Fresh runtime declaration differs from foundation policy')
    for name, metadata in APT_DIRECTORIES.items():
        if rows.get(name) != dict(zip(('mode', 'uid', 'gid'), metadata)):
            raise ValueError('Fresh APT declaration differs from foundation policy')
    for name, row in rows.items():
        if (not any(name == base or name.startswith(base + '/') for base in (*FRESH_DIRECTORIES, *MUTABLE_TREES))
                or name in plan and not stat.S_ISDIR(plan[name]['expected']['mode'])):
            raise ValueError('Unreviewed fresh directory declaration')
        add(plan, name, directory(**row), 'fresh-runtime', transform=True)


def declare_database(plan, state):
    modes = {'lock': 0o640, 'lock-frontend': 0o640, 'triggers/Lock': 0o600, 'triggers/Unincorp': 0o644}
    add(plan, 'var/lib/dpkg', directory(), 'native-database')
    for name, row in state.items():
        if stat.S_ISDIR(row['mode']):
            if name not in package_database.DIRECTORIES:
                raise ValueError('Unreviewed generated database directory')
            expected = directory()
        else:
            if name not in {'status', 'status-old', *modes} and not (name.startswith('info/') and name.count('/') == 1):
                raise ValueError('Unreviewed generated database file')
            expected = {'mode': stat.S_IFREG | modes.get(name, 0o644), 'uid': 0, 'gid': 0,
                        'xattrs': {}, 'sha256': row['sha256'], 'size': row['size']}
        if any(row[key] != expected[key] for key in ('mode', 'uid', 'gid')):
            raise ValueError('Generated database mode/ownership differs')
        add(plan, 'var/lib/dpkg/' + name, expected, 'native-database')


def declare_live_profile(plan):
    if plan.get('etc/fstab', {}).get('origins') != ['package:toddy-base-config']:
        raise ValueError('Live fstab transformation lacks native base ownership')
    add(plan, 'etc/fstab', regular(LIVE_FSTAB), 'live-settings', transform=True)
    for name, target in DEFAULT_LINKS.items():
        add(plan, name, symlink(target), 'live-settings')
    for name, target in SERVICE_LINKS.items():
        unit = UNIT_PREFIX + (target or name)
        if 'sha256' not in plan.get(unit[1:], {}).get('expected', {}):
            raise ValueError('Generated service declaration lacks an owned unit')
        add(plan, 'etc/systemd/system/' + name, symlink(UNIT_PREFIX + target if target else '/dev/null'), 'offline-services')
    for name, text in profile_files().items():
        add(plan, name, regular(text), 'live-console')
    for unit, template in UNITS.items():
        if 'sha256' not in plan.get((UNIT_PREFIX + template)[1:], {}).get('expected', {}):
            raise ValueError('Console declaration lacks its owned template')
        add(plan, 'etc/systemd/system/getty.target.wants/' + unit, symlink(UNIT_PREFIX + template), 'live-console')


def declare_artifact(plan, kind, report):
    name = ARTIFACTS[kind]
    if (report.get('output', report.get('path')) != '/' + name or name in plan
            or type(report['bytes']) is not int or report['bytes'] < 0):
        raise ValueError('Generated artifact identity conflicts with declared image state')
    add(plan, name, {'mode': stat.S_IFREG | 0o644, 'uid': 0, 'gid': 0, 'xattrs': {},
                    'sha256': report['sha256'], 'size': report['bytes']}, kind)
    if kind == 'loader-cache':
        if 'var/cache/ldconfig' in plan and not stat.S_ISDIR(plan['var/cache/ldconfig']['expected']['mode']):
            raise ValueError('Loader cache cannot replace an owned file')
        add(plan, 'var/cache/ldconfig', directory(0o700), 'loader-cache', transform=True)


def audit(backend, image, plan, copied_hardlinks):
    image = Path(image)
    if (not backend.native or os.geteuid() != 0 or image.resolve() != image or not image.is_dir()
            or not any(image != backend.target / area and image.is_relative_to(backend.target / area)
                       for area in ('tmp', 'sources/stage'))):
        raise ValueError('Attribution audit requires a private native image')
    captured = snapshot(image, tree_names(image))
    actual = captured['entries']
    expected_hardlinks = sorted(sorted(name for name in group if name in plan)
                               for group in copied_hardlinks if sum(name in plan for name in group) > 1)
    hardlinks_match = captured['hardlink_groups'] == expected_hardlinks
    missing, unknown = sorted(set(plan) - set(actual)), sorted(set(actual) - set(plan))
    changed = []
    for name in sorted(set(plan) & set(actual)):
        fields = [key for key, value in plan[name]['expected'].items() if actual[name].get(key) != value]
        if fields:
            changed.append({'path': '/' + name if name != '.' else '/', 'origins': plan[name]['origins'], 'fields': fields})
    return {'scope': 'Declared physical image namespace, bytes, metadata and extended attributes',
            'declared_entries': len(plan), 'actual_entries': len(actual), 'missing': missing, 'unknown': unknown,
            'changed': changed, 'hardlink_groups_match': hardlinks_match,
            'attribution_check_passed': not (missing or unknown or changed) and hardlinks_match,
            'arbitrary_secret_contents_audited': False, 'dependency_or_boot_accepted': False}
