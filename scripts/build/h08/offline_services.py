"""Configure/check the foundation's native units without contacting a manager."""
import hashlib
import json
from pathlib import Path
import stat
import subprocess
import sys

ENABLED = ('systemd-networkd.service', 'systemd-resolved.service', 'systemd-timesyncd.service')
WAIT_ONLINE = 'systemd-networkd-wait-online.service'
VENDOR_DBUS = '/usr/lib/systemd/system/sockets.target.wants/dbus.socket'


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def configure_services(backend, image, records_directory, *, check_only=False):
    image = Path(image)
    if (not backend.native or image.resolve() != image or not image.is_dir()
            or not (image == backend.target or any(image.is_relative_to(backend.target / area)
                                                   for area in ('tmp', 'sources/stage')))):
        raise ValueError('Offline services require the native target or its private image staging')
    system = image / 'etc/systemd/system'
    if system.resolve() != system:
        raise ValueError('Systemd configuration directory redirects')
    units, records = {}, {}
    for name in ('systemd', 'dbus'):
        version, architecture, state = backend.run('dpkg-query', '-W', '-f=${Version}\t${Architecture}\t${Status}',
                                                   name, capture_output=True, text=True).stdout.split('\t')
        record = json.loads((Path(records_directory) / f'{name}_{version}_{architecture}.json').read_text())
        if state != 'install ok installed' or not record['installed'] or record['name'] != name or record['version'] != version:
            raise ValueError('Native unit provider is not accepted/configured')
        records[name] = record
        for virtual, row in record['payload'].items():
            if not virtual.startswith('/usr/lib/systemd/system/'):
                continue
            path = image / virtual[1:]
            if path.parent.resolve() != path.parent:
                raise ValueError('Native unit parent redirects: ' + virtual)
            actual = path.lstat()
            if (actual.st_mode, actual.st_uid, actual.st_gid) != (row['mode'], row['uid'], row['gid']):
                raise ValueError('Native unit metadata changed: ' + virtual)
            if 'sha256' in row and digest(path) != row['sha256']:
                raise ValueError('Native unit bytes changed: ' + virtual)
            if 'symlink' in row and path.readlink().as_posix() != row['symlink']:
                raise ValueError('Native unit link changed: ' + virtual)
            units[virtual] = row
    if (digest(backend.target / 'usr/bin/systemctl') != records['systemd']['payload']['/usr/bin/systemctl']['sha256']
            or units.get(VENDOR_DBUS) != {'mode': stat.S_IFLNK | 0o777, 'uid': 0, 'gid': 0, 'symlink': '../dbus.socket'}):
        raise ValueError('Native Systemctl or DBus vendor activation differs')
    def checked_links():
        # Resolve generated links inside the selected image, not against the guest's
        # /usr. A valid name alone does not establish an owned unit target.
        from audit_native_elf import target_resolve
        links = {}
        for path in system.rglob('*'):
            if not path.is_symlink():
                continue
            virtual = '/' + str(path.relative_to(image))
            if (virtual == '/etc/systemd/system/' + WAIT_ONLINE and path.readlink().as_posix() == '/dev/null'
                    and path.lstat().st_uid == path.lstat().st_gid == 0):
                links[virtual] = {'symlink': '/dev/null', 'owned_unit': '/usr/lib/systemd/system/' + WAIT_ONLINE,
                                  'policy': 'Explicit foundation offline-startup mask'}
                continue
            actual, canonical = target_resolve(image, virtual)
            info = path.lstat()
            if (canonical not in units or 'sha256' not in units[canonical] or not actual.is_file()
                    or info.st_uid != 0 or info.st_gid != 0):
                raise ValueError('Generated unit link lacks native ownership: ' + virtual)
            links[virtual] = {'symlink': path.readlink().as_posix(), 'owned_target': canonical}
        return links

    # Refuse unowned/redirected existing links before changing any enablement.
    checked_links()
    virtual_root = '/' if image == backend.target else '/' + str(image.relative_to(backend.target))
    operations = []
    def run(*args, non_enabled=False):
        try:
            result = backend.run('systemctl', '--root=' + virtual_root, *args, capture_output=True, text=True)
            code, stdout, stderr = result.returncode, result.stdout, result.stderr
        except subprocess.CalledProcessError as error:
            if not (non_enabled and error.returncode == 1 and error.stdout.strip() in {'disabled', 'masked'}):
                print(error.stdout, error.stderr, file=sys.stderr)
                raise
            code, stdout, stderr = error.returncode, error.stdout, error.stderr
        operations.append({'arguments': list(args), 'exit': code, 'stdout': stdout, 'stderr': stderr})
        return stdout.strip()
    if not check_only:
        # DBus is a static socket pulled in by its *owned vendor* wants link.
        # It deliberately has no [Install] section and must not be enabled or
        # given a synthetic administrator-owned substitute for that link.
        run('--no-reload', 'enable', *ENABLED)
        run('--no-reload', 'disable', WAIT_ONLINE)
        # Native preset-all re-adds wait-online through networkd's Also= even
        # when a higher-priority preset says disable. Preserve offline startup
        # with this one explicit, owner-reversible mask (ADR-0060).
        run('--no-reload', 'mask', WAIT_ONLINE)
        run('set-default', 'multi-user.target')
    states = {name: run('is-enabled', name) for name in ENABLED}
    states['dbus.socket'] = run('is-enabled', 'dbus.socket')
    states[WAIT_ONLINE] = run('is-enabled', WAIT_ONLINE, non_enabled=True)
    if states != {**{name: 'enabled' for name in ENABLED}, 'dbus.socket': 'static', WAIT_ONLINE: 'masked'}:
        raise ValueError('Unexpected native offline unit states: ' + json.dumps(states))
    default = run('get-default')
    if default != 'multi-user.target':
        raise ValueError('Unexpected native default target')
    links = checked_links()
    return {'states': states, 'default_target': default, 'dbus_vendor_activation': VENDOR_DBUS,
            'unit_providers': {name: {'version': record['version'], 'archive_sha256': record['archive_sha256']}
                               for name, record in records.items()},
            'native_unit_paths_verified': len(units), 'generated_links': links,
            'operations': operations, 'check_only': check_only,
            'manager_contacted': False, 'boot_or_network_operation_verified': False}


def main():
    from require_gate import require_gate
    project = Path(__file__).resolve().parents[3]
    require_gate(project, Path('/var/log/toddy/build'))
    subprocess.run(['bash', '-c', 'source /opt/toddy-build/scripts/build/target.sh; guard_target'], check=True)
    sys.path.insert(0, str(project / 'scripts/build'))
    from package_backend import PackageBackend
    if sys.argv[1:] not in ([], ['--check']):
        raise SystemExit('Usage: offline_services.py [--check]')
    report = configure_services(PackageBackend(), Path('/mnt/lfs'), Path('/var/log/toddy/packages'),
                                check_only=sys.argv[1:] == ['--check'])
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
