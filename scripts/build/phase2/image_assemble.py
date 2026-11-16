"""Fixed source-only first native archive assembly; never production readiness.

Run inside the coordinator's guarded native target chroot, under its build lock.
No disks are partitioned, existing roots resumed, or production gates bypassed.
The resulting root is a candidate for independent generated-resource review.
"""
import fcntl
import json
import os
from pathlib import Path
import stat
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT), str(Path(__file__).resolve().parent)]
from runtime.installer.composition import bundle_namespace, secured
from runtime.installer.linux_disk import LinuxDisk
from runtime.installer.native_finalizer import payload_module

STAGE = Path('/sources/stage')
GENERATIONS = {'base': ('toddy-offline-image-1', 'toddy-installer-native-inputs'),
               'live': ('toddy-live-image-1', 'toddy-live-native-inputs')}
RESERVE = 16 * 1024**3


def private_directory(path, mode):
    path = Path(path)
    info = path.lstat()
    if (path.resolve() != path or not stat.S_ISDIR(info.st_mode) or info.st_uid or
            info.st_gid or stat.S_IMODE(info.st_mode) != mode):
        raise ValueError('Native assembly directory custody')
    return info


def native_guard(system):
    system.require_root()
    node = Path('/dev/vdb4').stat()
    if not stat.S_ISBLK(node.st_mode) or Path('/').stat().st_dev != node.st_rdev:
        raise ValueError('Assembly requires designated native target root, not builder/host root')
    if system.run(['/usr/bin/lsblk', '-dn', '-o', 'SERIAL', '/dev/vdb']) != 'TODDY-LFS-TARGET':
        raise ValueError('Assembly target serial')
    if system.run(['/usr/sbin/blkid', '-s', 'LABEL', '-o', 'value', '/dev/vdb4']) != 'TODDY_LFS':
        raise ValueError('Assembly target label')


def write(path, value):
    p = payload_module()
    with Path(path).open('xb') as stream:
        os.fchmod(stream.fileno(), 0o600)
        stream.write(p.encoded(value)); stream.flush(); os.fsync(stream.fileno())


class AssemblyRoot:
    """One fixed, new same-filesystem generation; inode-pinned across commands."""
    def __init__(self, kind, manifest):
        if kind not in GENERATIONS:
            raise ValueError('Unknown fixed image profile')
        self.work = STAGE/GENERATIONS[kind][0]
        self.root = self.work/'root'
        parent = STAGE.lstat()
        if (STAGE.resolve() != STAGE or not stat.S_ISDIR(parent.st_mode) or parent.st_uid or
                parent.st_gid or parent.st_mode & 0o022 or parent.st_dev != Path('/').stat().st_dev):
            raise ValueError('Native assembly stage custody')
        if os.path.lexists(self.work):
            raise ValueError('Preserve existing/uncertain native assembly generation')
        installed = sum(row['installed_bytes'] for row in manifest['components'])
        if installed <= 0:
            raise ValueError('Native assembly size is unknown')
        # Root + later full extraction + compression bound, preserving the floor.
        self.required = RESERVE + 3*installed + 512*1024**2
        space = os.statvfs(STAGE)
        if space.f_bavail*space.f_frsize < self.required:
            raise ValueError('Native assembly capacity requires16GiB plus3xpayload plus512MiB')
        self.work.mkdir(mode=0o700); self.root.mkdir(mode=0o755)
        self.pin = self.identity()

    def identity(self):
        work = private_directory(self.work, 0o700)
        root = private_directory(self.root, 0o755)
        if root.st_dev != work.st_dev or root.st_dev != STAGE.stat().st_dev or os.path.ismount(self.root):
            raise ValueError('Native assembly redirected/cross-device root')
        return (work.st_dev, work.st_ino, root.st_ino)

    def recheck(self):
        if self.identity() != self.pin:
            raise ValueError('Native assembly root identity changed')


def unpack_native(bundle, manifest_sha256, assembly, system):
    """Actual fixed native Dpkg only; produces an explicitly unqualified root.

    A production PreparedPayload target guard is never changed. This developer
    component has its own fixed private stage/inode guard and no disk-plan API.
    """
    p = payload_module(); bundle = Path(bundle)
    prepared = p.PreparedPayload(bundle, manifest_sha256=manifest_sha256,
        runner=None, finalizer=None)
    manifest = prepared._load(); bundle_namespace(bundle, manifest)
    system.require_root(); assembly.recheck()
    if list(assembly.root.iterdir()):
        raise ValueError('Native assembly root must be empty; never replay unpack')
    for name in ('dpkg', 'dpkg-query'):
        virtual = '/usr/bin/'+name
        if p.digest(secured(virtual)) != manifest['ownership']['entries'][virtual]['sha256']:
            raise ValueError('Native package tool differs from selected source-owned closure')
    archives = [str(bundle/'archives'/row['archive']) for row in manifest['components']]
    intent = {'version':1, 'state':'unpack-intended', 'kind':'candidate-unqualified-root',
        'manifest_sha256':manifest_sha256, 'root':str(assembly.root),
        'required_bytes':assembly.required, 'assembly_pin':list(assembly.pin), 'production_ready':False,
        'native_boot_verified':False}
    write(assembly.work/'unpack-intent.json', intent)
    log = '--log='+str(assembly.work/'dpkg.log')
    system.run(['/usr/bin/dpkg', '--root='+str(assembly.root), log, '--unpack', *archives], timeout=1800)
    assembly.recheck()
    system.run(['/usr/bin/dpkg', '--root='+str(assembly.root), log, '--configure', '--pending'], timeout=900)
    assembly.recheck()
    observed = system.run(['/usr/bin/dpkg-query', '--admindir='+str(assembly.root/'var/lib/dpkg'),
        '-W', '-f=${Package}\t${Version}\t${Architecture}\t${Status}\n'])
    rows = [line.split('\t') for line in observed.splitlines()]
    expected = sorted([row['name'],row['version'],row['architecture'],'install ok installed'] for row in manifest['components'])
    if sorted(rows) != expected or system.run(['/usr/bin/dpkg', '--root='+str(assembly.root), log, '--audit']):
        raise ValueError('Native assembly database is not exact/configured')
    if prepared._load() != manifest:
        raise ValueError('Native assembly input changed')
    assembly.recheck()
    result = {**intent, 'state':'native-archives-unpacked-needs-resource-qualification',
        'configured_packages':len(rows), 'dpkg_log_sha256':p.digest(assembly.work/'dpkg.log')}
    write(assembly.work/'unpacked.json', result)
    return result


def adopt_unpacked(kind, manifest, manifest_sha256, system):
    """Continue read-only custody of a completed unpack, never replay its writes."""
    if kind not in GENERATIONS:
        raise ValueError('Unknown fixed image profile')
    p=payload_module();assembly=object.__new__(AssemblyRoot)
    assembly.work=STAGE/GENERATIONS[kind][0];assembly.root=assembly.work/'root'
    intent=p.strict(secured(assembly.work/'unpack-intent.json').read_bytes())
    result=p.strict(secured(assembly.work/'unpacked.json').read_bytes())
    if (intent.get('manifest_sha256')!=manifest_sha256 or result.get('manifest_sha256')!=manifest_sha256 or
            intent.get('root')!=str(assembly.root) or result.get('root')!=str(assembly.root) or
            intent.get('state')!='unpack-intended' or result.get('state')!='native-archives-unpacked-needs-resource-qualification' or
            intent.get('assembly_pin')!=result.get('assembly_pin') or intent.get('required_bytes')!=result.get('required_bytes') or
            type(intent.get('required_bytes')) is not int or intent['required_bytes']<=RESERVE):
        raise ValueError('Native unpack custody is incomplete or mismatched')
    assembly.pin=tuple(intent['assembly_pin']);assembly.required=intent['required_bytes'];assembly.recheck()
    system.require_root()
    query=system.run(['/usr/bin/dpkg-query','--admindir='+str(assembly.root/'var/lib/dpkg'),
        '-W','-f=${Package}\t${Version}\t${Architecture}\t${Status}\n'])
    expected=sorted([row['name'],row['version'],row['architecture'],'install ok installed'] for row in manifest['components'])
    if sorted(line.split('\t') for line in query.splitlines())!=expected or p.digest(secured(assembly.work/'dpkg.log'))!=result.get('dpkg_log_sha256'):
        raise ValueError('Native unpack database/log changed before qualification')
    return assembly


def main():
    if (sys.argv[1:] not in (['base'], ['live'], ['qualify-base'], ['qualify-live']) or
            Path(__file__).resolve() != Path('/opt/toddy-build/scripts/build/phase2/image_assemble.py')):
        raise ValueError('Fixed native source coordinator command required')
    os.umask(0o077); system=LinuxDisk();native_guard(system)
    descriptor = os.open('/run/toddy-image-assembly.lock', os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW, 0o600)
    try:
        info=os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode) or info.st_uid or info.st_gid or info.st_nlink!=1 or stat.S_IMODE(info.st_mode)!=0o600:
            raise ValueError('Native assembly lock custody')
        fcntl.flock(descriptor, fcntl.LOCK_EX|fcntl.LOCK_NB)
        action=sys.argv[1];kind=action.removeprefix('qualify-');bundle=STAGE/GENERATIONS[kind][1]/'payload';p=payload_module()
        sha=p.digest(secured(bundle/'manifest.json'))
        manifest=p.PreparedPayload(bundle,manifest_sha256=sha,runner=None,finalizer=None)._load()
        bundle_namespace(bundle,manifest)
        if action.startswith('qualify-'):
            from resource_recipe import qualify
            from runtime.installer.composition import validate_policy
            policy=p.strict(secured(bundle.parent/'policy.json').read_bytes());validate_policy(policy,manifest)
            assembly=adopt_unpacked(kind,manifest,sha,system)
            result=qualify(assembly,manifest,policy,system)
        else:
            assembly=AssemblyRoot(kind,manifest)
            result=unpack_native(bundle,sha,assembly,system)
        print(json.dumps(result,sort_keys=True))
    finally:
        os.close(descriptor)


if __name__ == '__main__':
    main()
