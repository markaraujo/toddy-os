#!/usr/bin/env python3
"""Read finalized generation9 Dconf only through a disposable native overlay.

The fixed builder wrapper supplies its protected stage view and exclusive FD9.
No image file, original snapshot or assembly receipt is written by this helper.
"""
from contextlib import contextmanager
from dataclasses import dataclass
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parents[2])]
import image_media as media
import live_profile
from runtime.installer.composition import SOURCES, source_path, secured, validate_finalizer_report

TARGET = Path('/mnt/lfs')
WORK = TARGET / 'sources/stage/toddy-mvp-live-image-9-reviewed'
IMAGE = WORK / 'mvp-live-root-2'
VIRTUAL = '/sources/stage/toddy-mvp-live-image-9-reviewed/mvp-live-root-2'
QUERIES = (
    ('/org/gnome/desktop/lockdown/disable-lock-screen', 'true'),
    ('/org/gnome/desktop/screensaver/lock-enabled', 'false'),
    ('/org/gnome/desktop/session/idle-delay', 'uint32 0'),
)
DATABASE = 'etc/dconf/db/toddy-live'
SOURCE = 'etc/dconf/db/toddy-live.d/00-session'
PROFILE = 'etc/dconf/profile/user'


def run(argv, **kwargs):
    return subprocess.run(argv, check=True, **kwargs)


def digest(path):
    return media.p.digest(secured(path))


def root_pin(image=IMAGE, work=WORK):
    """Bind the same root inode and private same-device work directory."""
    if image.resolve() != image or work.resolve() != work or image.parent != work:
        raise ValueError('Dconf observer root redirects')
    parent, root = work.lstat(), image.lstat()
    if (not stat.S_ISDIR(parent.st_mode) or not stat.S_ISDIR(root.st_mode)
            or parent.st_uid or parent.st_gid or root.st_uid or root.st_gid
            or stat.S_IMODE(parent.st_mode) != 0o700
            or stat.S_IMODE(root.st_mode) != 0o755
            or parent.st_dev != root.st_dev or root.st_dev != TARGET.stat().st_dev
            or os.path.ismount(image)):
        raise ValueError('Dconf observer root custody')
    return [root.st_dev, parent.st_ino, root.st_ino]


def receipt_binding(journal, live, finalized, pin, source_sha):
    """A receipt is usable only for the same completed fixed generation."""
    if (live.get('state') != 'source-attributed-live-profile-candidate'
            or finalized.get('state') != 'native-finalizer-verified'
            or live.get('root') != VIRTUAL or finalized.get('root') != VIRTUAL
            or live.get('assembly_pin') != pin or finalized.get('assembly_pin') != pin
            or live.get('base_image_manifest_sha256') != finalized.get('image_manifest_sha256')
            or live.get('source_sha256') != source_sha
            or journal.get('media_id') != live.get('media_id')
            or journal.get('payload_manifest_sha256') != finalized.get('payload_manifest_sha256')
            or live.get('production_ready') is not False
            or live.get('native_boot_verified') is not False
            or live.get('native_login_verified') is not False):
        raise ValueError('Dconf observer actual live/finalizer binding differs')
    checks = finalized.get('checks', {})
    if set(checks) != media.p.CHECKS or any(
            row.get('passed') is not True or type(row.get('exit_status')) is not int
            or row['exit_status'] != 0 for row in checks.values()):
        raise ValueError('Dconf observer completed finalizer required')


def dconf_contract(image, expected, live):
    """Check selected file bytes and metadata without executing inside image."""
    delta = live['attributed_delta']
    for relative in (DATABASE, SOURCE, PROFILE):
        path = secured(image / relative)
        info = path.lstat()
        row = expected['entries'].get(relative, {})
        after = delta.get('/' + relative, {}).get('after', {})
        if (info.st_nlink != 1 or not stat.S_ISREG(info.st_mode)
                or info.st_uid or info.st_gid or stat.S_IMODE(info.st_mode) != 0o644
                or info.st_dev != image.stat().st_dev
                or row.get('mode') != stat.S_IFREG | 0o644
                or row.get('uid') != 0 or row.get('gid') != 0
                or digest(path) != row.get('sha256') or row['sha256'] != after.get('sha256')):
            raise ValueError('Dconf observer attributed file custody differs')
    if (image / SOURCE).read_bytes() != live_profile.DCONF.encode():
        raise ValueError('Dconf observer session source content differs')
    profile = (image / PROFILE).read_text().splitlines()
    if (profile[:2] != ['user-db:user', 'system-db:toddy-live']
            or any(not media.re.fullmatch(r'(user-db:user|system-db:[a-zA-Z0-9_-]+)', line)
                   for line in profile)
            or profile.count('system-db:toddy-live') != 1):
        raise ValueError('Dconf observer user profile content differs')
    tool = secured(image / 'usr/bin/dconf')
    if digest(tool) != live.get('native_dconf_tool_sha256'):
        raise ValueError('Dconf observer native tool source differs')
    if os.path.lexists(image / 'etc/dconf/db/ibus'):
        raise ValueError('Dconf observer unexpected IBus database')


@dataclass
class Inputs:
    pin: list
    expected: dict
    hashes: dict
    database_sha256: str
    media_id: str


def inputs():
    media.configure_mvp()
    if media.IMAGE != IMAGE or media.JOURNAL != WORK / 'evidence/assembly.json':
        raise ValueError('Dconf observer requires fixed generation9 media route')
    journal, manifest, expected = media.assembly_input()
    pin = root_pin()
    paths = {'journal': media.JOURNAL, 'manifest': manifest,
             'live': WORK / 'live-profile-receipt.json', 'finalized': WORK / 'finalized.json',
             'live-manifest': WORK / 'live-image-manifest.json',
             'live-source': HERE / 'live_profile.py', 'assembler': HERE / 'image_assemble.py',
             'observer-source': Path(__file__)}
    hashes = {str(path): digest(path) for path in paths.values()}
    live = media.p.strict(secured(paths['live']).read_bytes())
    finalized = media.p.strict(secured(paths['finalized']).read_bytes())
    if (journal.get('live_profile_receipt_sha256') != hashes[str(paths['live'])]
            or journal.get('native_finalizer_receipt_sha256') != hashes[str(paths['finalized'])]
            or live.get('live_image_manifest_sha256') != hashes[str(paths['live-manifest'])]):
        raise ValueError('Dconf observer receipt hash custody differs')
    receipt_binding(journal, live, finalized, pin, hashes[str(paths['live-source'])])
    if set(finalized.get('source_sha256', {})) != SOURCES:
        raise ValueError('Dconf observer complete finalizer sources required')
    for name, sha in finalized['source_sha256'].items():
        path = source_path(name)
        if digest(path) != sha:
            raise ValueError('Dconf observer finalizer source changed')
        hashes[str(path)] = sha
    for name, binding in finalized['checks'].items():
        native = Path('/run/toddy-installer/finalization-mvp-live-root-2') / (name + '.json')
        if binding.get('report') != str(native):
            raise ValueError('Dconf observer finalizer report path differs')
        path = TARGET / native.relative_to('/')
        if digest(path) != binding.get('report_sha256'):
            raise ValueError('Dconf observer finalizer report hash differs')
        validate_finalizer_report(media.p.strict(secured(path).read_bytes()), name, finalized)
        hashes[str(path)] = binding['report_sha256']
    dconf_contract(IMAGE, expected, live)
    if media.live_identity() != live['media_id']:
        raise ValueError('Dconf observer image media identity differs')
    return Inputs(pin, expected, hashes, expected['entries'][DATABASE]['sha256'], live['media_id'])


def unchanged(bound):
    if root_pin() != bound.pin:
        raise ValueError('Dconf observer lower root inode changed')
    if any(digest(Path(name)) != sha for name, sha in bound.hashes.items()):
        raise ValueError('Dconf observer inputs changed')
    if media.snapshot(IMAGE, media.tree_names(IMAGE)) != bound.expected:
        raise ValueError('Dconf observer lower image changed')


def mount_id(path):
    """Require a unique exact mount point; never accept a parent mount."""
    result = run(['/usr/bin/findmnt', '-rn', '-o', 'ID', '--mountpoint', str(path)],
                 capture_output=True, text=True, timeout=30)
    value = result.stdout.strip()
    if not value.isdecimal():
        raise ValueError('Dconf observer exact mount identity required')
    return value


def mount_profile(path, filesystem, required, *, forbidden=(), values=None):
    """Read actual kernel mount topology; requested options are not proof."""
    result = run(['/usr/bin/findmnt', '-rn', '-o', 'FSTYPE,OPTIONS', '--mountpoint', str(path)],
                 capture_output=True, text=True, timeout=30)
    lines = result.stdout.strip().splitlines()
    fields = lines[0].split(None, 1) if len(lines) == 1 else []
    if len(fields) != 2 or fields[0] != filesystem:
        raise ValueError('Dconf observer actual mount filesystem differs')
    options = fields[1].split(',')
    if (not set(required) <= set(options) or set(forbidden) & set(options)
            or len(options) != len(set(options))):
        raise ValueError('Dconf observer actual mount options differ')
    for name, expected in (values or {}).items():
        observed = [option[len(name) + 1:] for option in options if option.startswith(name + '=')]
        if observed != [str(expected)]:
            raise ValueError('Dconf observer actual overlay topology differs')


def lower_identity(lower, image=IMAGE):
    actual, expected = lower.stat(), image.stat()
    if (actual.st_dev, actual.st_ino) != (expected.st_dev, expected.st_ino):
        raise ValueError('Dconf observer lower mount is not the fixed image inode')


@contextmanager
def disposable_overlay():
    """All writable state belongs to one bounded fresh private tmpfs."""
    base = Path(tempfile.mkdtemp(prefix='toddy-live-dconf9-', dir='/run'))
    initial = base.stat(); tmpfs = lower_mount = overlay_mount = None
    try:
        run(['/usr/bin/mount', '-t', 'tmpfs', '-o', 'size=128m,mode=0700,nosuid,nodev',
             'toddy-live-dconf9', str(base)], timeout=30)
        tmpfs = mount_id(base)
        mount_profile(base, 'tmpfs', {'rw', 'nosuid', 'nodev'}, forbidden={'ro'})
        for name in ('lower', 'upper', 'work', 'root'):
            (base / name).mkdir(mode=0o700)
        run(['/usr/bin/mount', '--bind', str(IMAGE), str(base / 'lower')], timeout=30)
        lower_mount = mount_id(base / 'lower')
        run(['/usr/bin/mount', '-o', 'remount,bind,ro,nosuid,nodev', str(base / 'lower')], timeout=30)
        mount_profile(base / 'lower', 'ext4', {'ro', 'nosuid', 'nodev'}, forbidden={'rw'})
        lower_identity(base / 'lower')
        run(['/usr/bin/mount', '-t', 'overlay', 'overlay', '-o',
             f'lowerdir={base}/lower,upperdir={base}/upper,workdir={base}/work,nosuid,nodev',
             str(base / 'root')], timeout=30)
        overlay_mount = mount_id(base / 'root')
        mount_profile(base / 'root', 'overlay', {'rw', 'nosuid', 'nodev'}, forbidden={'ro'},
                      values={'lowerdir': base / 'lower', 'upperdir': base / 'upper',
                              'workdir': base / 'work'})
        lower_identity(base / 'lower')
        yield base / 'root', base / 'upper'
    finally:
        # Mount IDs must still name our exact mounts. Never lazy-unmount or
        # recurse through the persistent image; failed cleanup is a failure.
        for name, identifier in (('root', overlay_mount), ('lower', lower_mount)):
            if identifier is not None:
                if mount_id(base / name) != identifier:
                    raise ValueError('Dconf observer mount changed before cleanup')
                run(['/usr/bin/umount', str(base / name)], timeout=30)
        if tmpfs is not None:
            if mount_id(base) != tmpfs:
                raise ValueError('Dconf observer tmpfs changed before cleanup')
            run(['/usr/bin/umount', str(base)], timeout=30)
        actual = base.lstat()
        if (actual.st_dev, actual.st_ino) != (initial.st_dev, initial.st_ino) or base.is_symlink():
            raise ValueError('Dconf observer workspace changed before cleanup')
        base.rmdir()


def isolated_reads(view, upper):
    values = {}
    for key, expected in QUERIES:
        command = ['/usr/sbin/chroot', str(view), '/usr/bin/env', '-i',
                   'PATH=/usr/bin:/usr/sbin', 'HOME=/root', 'LC_ALL=C', 'DCONF_PROFILE=user',
                   '/usr/bin/dconf', 'read', key]
        result = run(command, capture_output=True, text=True, timeout=30)
        if result.stdout.strip() != expected or result.stderr:
            raise ValueError('Dconf observer native query differs')
        values[key] = result.stdout.strip()
    names = sorted(media.tree_names(upper))
    if len(names) > 256 or any('etc/dconf/db/ibus' == name for name in names):
        raise ValueError('Dconf observer unexpected disposable output')
    # Known native side effects such as /run/user/0/dconf/user are deliberately
    # retained in this upper inventory, then discarded with the whole tmpfs.
    return values, names


def observe(bound):
    unchanged(bound)
    try:
        with disposable_overlay() as (view, upper):
            values, names = isolated_reads(view, upper)
    finally:
        # Even a native failure must not hide a lower/input mutation.
        unchanged(bound)
    return {'version': 1, 'state': 'disposable-native-live-dconf-verified',
            'root': str(IMAGE), 'assembly_pin': bound.pin, 'media_id': bound.media_id,
            'database_sha256': bound.database_sha256, 'values': values,
            'disposable_upper_paths': names, 'lower_full_snapshot_unchanged': True,
            'input_hashes_unchanged': True, 'input_sha256': bound.hashes,
            'producer_sha256': digest(Path(__file__)), 'native_boot_verified': False,
            'native_login_verified': False, 'release_accepted': False, 'g2_eligible': False}


def main():
    if (sys.argv[1:] or os.getuid() != 0 or os.geteuid() != 0
            or Path(__file__).resolve() != Path('/opt/toddy-build/scripts/build/phase2/verify_live_dconf.py')):
        raise ValueError('Fixed root Dconf observer command required')
    os.umask(0o077)
    run(['/usr/bin/bash', '-c', 'source /opt/toddy-build/scripts/build/target.sh; guard_target'], timeout=30)
    media.inherited_media_lease()
    if Path('/proc/self/ns/mnt').readlink() == Path('/proc/1/ns/mnt').readlink():
        raise ValueError('Dconf observer requires private mount namespace')
    if list(media.BUILD.glob('*.running.json')) or (media.BUILD / 'input-sync.running').exists():
        raise ValueError('Dconf observer preserves active native work')
    result = observe(inputs())
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
