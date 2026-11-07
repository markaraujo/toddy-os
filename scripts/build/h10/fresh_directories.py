"""Recreate empty runtime/cache directories in a private image stage.

Run after explicit payload copy and before accounts, generated caches or service
configuration. Never repair or empty an existing directory in place.
"""
import os
from pathlib import Path, PurePosixPath
import stat

from live_accounts import account_data
from root_inventory import FRESH_DIRECTORIES, MUTABLE_TREES

APT_DIRECTORIES = {
    'var/cache/apt': (0o755, 0, 0),
    'var/cache/apt/archives': (0o755, 0, 0),
    'var/cache/apt/archives/partial': (0o700, 100, 0),
    'var/lib/apt': (0o755, 0, 0),
    'var/lib/apt/lists': (0o755, 0, 0),
    'var/lib/apt/lists/partial': (0o700, 100, 0),
    'var/lib/apt/lists/auxfiles': (0o755, 100, 0),
}


def stage_directories(backend, image, fresh, baseline):
    image = Path(image)
    if (not backend.native or os.geteuid() != 0 or image.resolve() != image or not image.is_dir()
            or not any(image.is_relative_to(backend.target / area) for area in ('tmp', 'sources/stage'))):
        raise ValueError('Fresh directories require a private native image stage')
    account_data(baseline)
    users = {int(row.split(':')[2]) for row in baseline['passwd'].splitlines()}
    groups = {int(row.split(':')[2]) for row in baseline['group'].splitlines()}
    plan = {}
    for name, row in fresh.items():
        parsed = PurePosixPath(name)
        if (not name or name == '.' or parsed.is_absolute() or parsed.as_posix() != name
                or '..' in parsed.parts or '\0' in name
                or not any(name == base or name.startswith(base + '/')
                           for base in (*FRESH_DIRECTORIES, *MUTABLE_TREES))):
            raise ValueError('Unreviewed fresh directory path: ' + name)
        if (set(row) != {'mode', 'uid', 'gid', 'directory'} or row['directory'] is not True
                or not stat.S_ISDIR(row['mode']) or row['mode'] != stat.S_IFDIR | stat.S_IMODE(row['mode'])
                or row['uid'] not in users or row['gid'] not in groups):
            raise ValueError('Unreviewed fresh directory metadata: ' + name)
        plan[name] = (stat.S_IMODE(row['mode']), row['uid'], row['gid'])
    for name, mode in FRESH_DIRECTORIES.items():
        if plan.get(name) != (mode, 0, 0):
            raise ValueError('Required runtime directory policy differs: ' + name)
    if 'var/cache' not in plan:
        raise ValueError('Owned cache directory is required before APT setup')
    # Runtime ownership deliberately overrides package-time directory ownership.
    # APT 3.0.4 acquire.cc uses the sandbox UID and ROOT_GROUP, not _apt's GID.
    overrides = {name: {'packaged': plan[name], 'generated': metadata}
                 for name, metadata in APT_DIRECTORIES.items() if name in plan and plan[name] != metadata}
    plan.update(APT_DIRECTORIES)
    device = image.stat().st_dev
    ordered = sorted(plan, key=lambda name: (len(PurePosixPath(name).parts), name))
    for name in ordered:
        path = image / name
        if path.exists() or path.is_symlink():
            raise ValueError('Preserve existing fresh directory input: ' + name)
        for parent in path.parents:
            if parent == image:
                break
            relative = parent.relative_to(image).as_posix()
            if relative in plan:
                continue
            if (parent.resolve() != parent or not parent.is_dir() or parent.stat().st_dev != device
                    or parent.stat().st_uid != 0 or parent.stat().st_gid != 0):
                raise ValueError('Fresh directory parent missing, redirected or unreviewed: ' + relative)
    # Preflight all paths before the first mutation. Interrupted stages remain
    # intact and must be rebuilt fresh, never merged with a partial attempt.
    for name in ordered:
        path = image / name
        path.mkdir(mode=0o700)
        for attribute in ('system.posix_acl_access', 'system.posix_acl_default'):
            if attribute in os.listxattr(path):
                os.removexattr(path, attribute)
        mode, uid, gid = plan[name]
        os.chown(path, uid, gid)
        path.chmod(mode)
    for name in ordered:
        path = image / name
        info = path.stat()
        mode, uid, gid = plan[name]
        if ((info.st_mode, info.st_uid, info.st_gid, info.st_dev) != (stat.S_IFDIR | mode, uid, gid, device)
                or os.listxattr(path)
                or any(child.relative_to(image).as_posix() not in plan for child in path.iterdir())):
            raise ValueError('Fresh directory postcondition failed; preserve stage: ' + name)
    for path in sorted({image / name for name in plan} | {(image / name).parent for name in plan}):
        descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    return {'directories': {name: {'mode': mode, 'uid': uid, 'gid': gid}
                            for name, (mode, uid, gid) in sorted(plan.items())},
            'runtime_ownership_overrides': overrides, 'builder_directory_metadata_copied': False,
            'apt_acquisition_verified': False, 'whole_image_or_boot_verified': False}
