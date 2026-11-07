"""Generate a native loader cache from verified private image inputs.

This foundation policy covers the frozen LFS search directories. Additional
search configuration/tunables require explicit policy expansion, not inheritance.
"""
import hashlib
import os
from pathlib import Path
import re
import stat
import subprocess

CONFIG = '# Begin /etc/ld.so.conf\n/usr/local/lib\n/opt/lib\ninclude /etc/ld.so.conf.d/*.conf\n'
SEARCH = ('usr/lib', 'lib64', 'usr/local/lib', 'opt/lib')


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def generate_loader_cache(backend, image, entries):
    from audit_native_elf import target_resolve
    image = Path(image)
    if (not backend.native or os.geteuid() != 0 or image.resolve() != image or not image.is_dir()
            or not any(image.is_relative_to(backend.target / area) for area in ('tmp', 'sources/stage'))):
        raise ValueError('Loader cache requires a fresh private native image')
    device = image.stat().st_dev
    for relative in ('etc', 'etc/ld.so.conf.d', 'var', 'var/cache'):
        path = image / relative
        if (path.resolve() != path or not path.is_dir() or path.stat().st_dev != device
                or path.stat().st_uid != 0 or path.stat().st_gid != 0):
            raise ValueError('Loader cache parent redirects or has unexpected ownership: ' + relative)
    cache = image / 'etc/ld.so.cache'
    auxiliary = image / 'var/cache/ldconfig'
    if list((image / 'etc').glob('ld.so.cache*')):
        raise ValueError('Preserve existing or partial loader cache')
    if (list((image / 'etc/ld.so.conf.d').iterdir())
            or (image / 'etc/tunables.conf').exists() or (image / 'etc/tunables.conf').is_symlink()):
        raise ValueError('Additional loader search configuration/tunables need explicit review')
    if auxiliary.exists() or auxiliary.is_symlink():
        actual = auxiliary.lstat()
        if (auxiliary.resolve() != auxiliary or actual.st_dev != device
                or (actual.st_mode, actual.st_uid, actual.st_gid) != (stat.S_IFDIR | 0o700, 0, 0)
                or list(auxiliary.iterdir())):
            raise ValueError('Preserve inherited or redirected auxiliary loader cache')
    selected = {'/etc/ld.so.conf', '/usr/sbin/ldconfig', '/lib', '/lib64'}
    path = image / 'lib'
    if not path.is_symlink() or path.readlink().as_posix() != 'usr/lib':
        raise ValueError('Foundation library alias differs')
    # Full LFS has a physical /lib64 with owned loader symlinks. The separately
    # assembled minimal initramfs uses a different, deliberately flattened alias.
    if not (image / 'lib64').is_dir() or (image / 'lib64').is_symlink():
        raise ValueError('Foundation loader directory differs')
    if (image / 'usr/lib64').exists() or (image / 'usr/lib64').is_symlink():
        raise ValueError('Additional library alias requires explicit foundation policy')
    for relative in SEARCH:
        directory = image / relative
        if not directory.exists() and not directory.is_symlink():
            if relative == 'usr/lib':
                raise ValueError('Missing native image library directory')
            continue
        if directory.resolve() != directory or not directory.is_dir():
            raise ValueError('Loader search directory redirects')
        selected.add('/' + relative)
        for parent, directories, files in os.walk(directory, followlinks=False):
            for name in directories + files:
                selected.add('/' + str((Path(parent) / name).relative_to(image)))

    def verify_inputs():
        for virtual in sorted(selected):
            if virtual not in entries:
                raise ValueError('Loader input lacks accepted package ownership: ' + virtual)
            row = entries[virtual]
            path = image / virtual[1:]
            if path.parent.resolve() != path.parent:
                raise ValueError('Loader input parent redirects: ' + virtual)
            actual = path.lstat()
            if (actual.st_dev != device
                    or (actual.st_mode, actual.st_uid, actual.st_gid) != (row['mode'], row['uid'], row['gid'])):
                raise ValueError('Loader input metadata differs: ' + virtual)
            if row.get('directory'):
                if not stat.S_ISDIR(actual.st_mode):
                    raise ValueError('Loader input directory type differs')
            elif 'sha256' in row:
                if not stat.S_ISREG(actual.st_mode) or digest(path) != row['sha256']:
                    raise ValueError('Loader input bytes differ: ' + virtual)
            elif not stat.S_ISLNK(actual.st_mode) or path.readlink().as_posix() != row['symlink']:
                raise ValueError('Loader input link differs: ' + virtual)
        if (image / 'etc/ld.so.conf').read_text() != CONFIG:
            raise ValueError('Loader search policy differs from frozen foundation configuration')

    verify_inputs()
    environment = {'PATH': '/usr/bin:/usr/sbin', 'LC_ALL': 'C', 'HOME': '/root'}
    command = ['chroot', str(image), '/usr/sbin/ldconfig']
    # -X preserves package-owned SONAME links; -i avoids using inode-based
    # auxiliary state. Glibc still writes a fresh auxiliary cache: omit it below.
    result = subprocess.run([*command, '-X', '-i'], env=environment, text=True,
                            capture_output=True, timeout=120, umask=0o022)
    if result.returncode or result.stdout or result.stderr:
        raise ValueError('Native loader cache generation diagnostics; preserve stage: ' +
                         repr((result.returncode, result.stdout, result.stderr)))
    verify_inputs()
    library_namespace = selected - {'/etc/ld.so.conf', '/usr/sbin/ldconfig', '/lib'}
    current_namespace = set()
    for relative in SEARCH:
        directory = image / relative
        if directory.exists():
            current_namespace.add('/' + relative)
            for parent, directories, files in os.walk(directory, followlinks=False):
                current_namespace.update('/' + str((Path(parent) / name).relative_to(image))
                                         for name in directories + files)
    if current_namespace != library_namespace:
        raise ValueError('Native cache generation changed the library namespace')
    if sorted(path.name for path in (image / 'etc').glob('ld.so.cache*')) != ['ld.so.cache']:
        raise ValueError('Interrupted or unexpected loader cache output')
    info = cache.lstat()
    if (info.st_mode, info.st_uid, info.st_gid, info.st_nlink) != (stat.S_IFREG | 0o644, 0, 0, 1):
        raise ValueError('Unexpected generated loader cache metadata')
    result = subprocess.run([*command, '-p'], env=environment, text=True, capture_output=True, timeout=30)
    lines = result.stdout.splitlines()
    if result.returncode or result.stderr or len(lines) < 3:
        raise ValueError('Native loader cache readback failed')
    count = re.fullmatch(r"(\d+) libs found in cache `/etc/ld.so.cache'", lines[0])
    if not count or lines[-1] != 'Cache generated by: ldconfig (GNU libc) stable release version 2.44':
        raise ValueError('Unexpected native loader cache format/version')
    cached = []
    for line in lines[1:-1]:
        match = re.fullmatch(r'\s+(\S+) \(([^)]+)\) => (/\S+)', line)
        if not match:
            raise ValueError('Unclassified loader cache entry: ' + line)
        soname, attributes, virtual = match.groups()
        actual, canonical = target_resolve(image, virtual)
        if canonical not in selected or 'sha256' not in entries[canonical] or digest(actual) != entries[canonical]['sha256']:
            raise ValueError('Cached library lacks verified image provenance: ' + virtual)
        cached.append({'soname': soname, 'attributes': attributes, 'path': virtual, 'owned_path': canonical})
    if not cached or int(count[1]) != len(cached):
        raise ValueError('Native loader cache entry count differs')
    if auxiliary.resolve() != auxiliary or sorted(path.name for path in auxiliary.iterdir()) != ['aux-cache']:
        raise ValueError('Unexpected generated auxiliary cache output')
    aux = auxiliary / 'aux-cache'
    info = aux.lstat()
    if (info.st_mode, info.st_uid, info.st_gid, info.st_nlink) != (stat.S_IFREG | 0o600, 0, 0, 1):
        raise ValueError('Unexpected auxiliary cache metadata')
    aux_sha = digest(aux)
    aux.unlink()
    for path in (cache, cache.parent, auxiliary):
        descriptor = os.open(path, os.O_RDONLY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    return {'generator': '/usr/sbin/ldconfig', 'generator_sha256': entries['/usr/sbin/ldconfig']['sha256'],
            'flags': ['-X', '-i'], 'verified_inputs': len(selected), 'entries': cached,
            'output': '/etc/ld.so.cache', 'sha256': digest(cache), 'bytes': cache.stat().st_size,
            'omitted_fresh_auxiliary_cache_sha256': aux_sha, 'source_cache_copied': False,
            'package_inputs_unchanged': True, 'whole_image_or_boot_verified': False}
