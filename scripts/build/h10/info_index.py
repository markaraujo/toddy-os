"""Regenerate the shared Info index from verified native image documents.

The caller must pass the accepted package inventory, after metadata closure has
removed shared-index ownership. No installed-target or existing index is edited.
"""
from contextlib import contextmanager
import hashlib
import os
from pathlib import Path
import stat
import subprocess


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


@contextmanager
def temporary_null(image):
    """Supply only the null device required by native install-info, then remove it."""
    directory = image / 'dev'
    if (directory.resolve() != directory or not directory.is_dir()
            or directory.stat().st_dev != image.stat().st_dev
            or directory.stat().st_uid or directory.stat().st_gid
            or directory.stat().st_mode & 0o022):
        raise ValueError('Info generation requires a protected physical image /dev')
    path = directory / 'null'
    created = None
    if not path.exists() and not path.is_symlink():
        os.mknod(path, stat.S_IFCHR | 0o600, os.makedev(1, 3))
        info = path.lstat()
        created = (info.st_dev, info.st_ino)
    try:
        info = path.lstat()
        if (not stat.S_ISCHR(info.st_mode) or info.st_rdev != os.makedev(1, 3)
                or info.st_uid or info.st_gid or info.st_nlink != 1):
            raise ValueError('Refuse an unexpected image /dev/null')
        if created:
            path.chmod(0o666)
        elif stat.S_IMODE(info.st_mode) != 0o666:
            raise ValueError('Preserve unexpected existing null-device permissions')
        yield created is not None
    finally:
        if created:
            info = path.lstat()
            if ((info.st_dev, info.st_ino) != created or not stat.S_ISCHR(info.st_mode)
                    or info.st_rdev != os.makedev(1, 3)):
                raise ValueError('Temporary null device changed; preserve it for inspection')
            path.unlink()


def generate_info_index(backend, image, entries):
    image = Path(image)
    if (not backend.native or os.geteuid() != 0 or image.resolve() != image or not image.is_dir()
            or not any(image.is_relative_to(backend.target / area) for area in ('tmp', 'sources/stage'))):
        raise ValueError('Info generation requires a fresh private native image')
    prefix = '/usr/share/info/'
    directory = image / prefix[1:]
    if directory.resolve() != directory or not directory.is_dir() or directory.stat().st_dev != image.stat().st_dev:
        raise ValueError('Image Info directory redirects or crosses a filesystem')
    if prefix + 'dir' in entries:
        raise ValueError('Shared Info index still belongs to package payload; finish metadata closure first')
    index = directory / 'dir'
    if index.exists() or index.is_symlink():
        raise ValueError('Preserve existing or interrupted Info index')
    documents = {path: row for path, row in entries.items() if path.startswith(prefix)}
    actual_names = {'/' + str(path.relative_to(image)) for path in directory.rglob('*')}
    if actual_names != set(documents):
        raise ValueError('Info document namespace differs from accepted package inventory')
    if not documents:
        raise ValueError('An empty documentation tree cannot produce the foundation index')
    tools = ('/usr/bin/install-info', '/usr/bin/info')
    selected = {**documents, **{name: entries[name] for name in tools}}

    def verify_inputs():
        for virtual, row in selected.items():
            path = image / virtual[1:]
            if path.parent.resolve() != path.parent:
                raise ValueError('Info input parent redirects: ' + virtual)
            actual = path.lstat()
            if (actual.st_dev != image.stat().st_dev
                    or (actual.st_mode, actual.st_uid, actual.st_gid) != (row['mode'], row['uid'], row['gid'])):
                raise ValueError('Info input metadata differs: ' + virtual)
            if row.get('directory'):
                if not stat.S_ISDIR(actual.st_mode):
                    raise ValueError('Info input directory changed type')
            elif not stat.S_ISREG(actual.st_mode) or 'sha256' not in row or digest(path) != row['sha256']:
                raise ValueError('Info input bytes/type differ: ' + virtual)

    verify_inputs()
    # The frozen set uses uncompressed main .info files, split .info-N parts
    # and images. Do not quietly omit a future compressed source input.
    if any(path.endswith(('.gz', '.xz', '.bz2', '.zst')) for path in documents):
        raise ValueError('Compressed Info input needs an explicit verified decompressor policy')
    primary = sorted(path for path, row in documents.items() if path.endswith('.info') and 'sha256' in row)
    if not primary:
        raise ValueError('No primary Info documents in accepted inventory')
    operations, no_menu_entry = [], []
    environment = {'PATH': '/usr/bin:/usr/sbin', 'LC_ALL': 'C', 'HOME': '/root'}
    # Texinfo 7.3 install-info.c explicitly reopens stdin on NULL_DEVICE.
    # A full image intentionally has an empty /dev until native boot.
    with temporary_null(image) as created_null:
        for virtual in primary:
            result = subprocess.run(['chroot', str(image), '/usr/bin/install-info',
                                     '--dir-file=/usr/share/info/dir', virtual],
                                    env=environment, text=True, capture_output=True, timeout=30, umask=0o022)
            operations.append({'document': virtual, 'exit': result.returncode,
                               'stdout': result.stdout, 'stderr': result.stderr})
            if result.returncode:
                raise ValueError('Native Info generation failed; preserve partial stage: ' + repr(operations[-1]))
            expected_warning = "install-info: warning: no info dir entry in `" + virtual + "'\n"
            if (not result.stdout and result.stderr == expected_warning
                    and b'START-INFO-DIR-ENTRY' not in (image / virtual[1:]).read_bytes()):
                no_menu_entry.append(virtual)
            elif result.stdout or result.stderr:
                raise ValueError('Unclassified native Info diagnostics: ' + repr(operations[-1]))
    verify_inputs()
    if {'/' + str(path.relative_to(image)) for path in directory.rglob('*')} != {*documents, prefix + 'dir'}:
        raise ValueError('Info generation left unexpected or interrupted outputs')
    info = index.lstat()
    if (info.st_mode, info.st_uid, info.st_gid, info.st_nlink) != (stat.S_IFREG | 0o644, 0, 0, 1):
        raise ValueError('Unexpected generated Info index metadata')
    data = index.read_bytes()
    if b'* Menu:' not in data or str(backend.target).encode() in data or str(image).encode() in data:
        raise ValueError('Generated Info index is invalid or contains build paths')
    with index.open('rb') as stream:
        os.fsync(stream.fileno())
    descriptor = os.open(directory, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    return {'generator': '/usr/bin/install-info', 'generator_sha256': entries[tools[0]]['sha256'],
            'transient_null_created_and_removed': created_null,
            'input_entries': len(documents), 'primary_documents': len(primary), 'operations': operations,
            'documents_without_menu_entry': no_menu_entry,
            'output': '/usr/share/info/dir', 'sha256': digest(index), 'bytes': len(data),
            'native_package_inputs_unchanged': True, 'package_database_rewritten': False,
            'source_index_copied': False, 'whole_image_or_boot_verified': False}
