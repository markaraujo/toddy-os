"""Capture native ACLs for restoration before live services start (ADR-0048)."""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat

SIDECAR = 'usr/share/toddy/live-root.acl'


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def decode_name(encoded):
    """Decode precisely the filename quoting emitted by frozen ACL 2.4.0."""
    result = bytearray()
    index = 0
    while index < len(encoded):
        if encoded[index:index + 1] != b'\\':
            result.append(encoded[index]); index += 1
        elif encoded[index:index + 2] == b'\\\\':
            result.append(92); index += 2
        elif encoded[index:index + 4] in (b'\\012', b'\\015'):
            result.append(int(encoded[index + 1:index + 4], 8)); index += 4
        else:
            raise ValueError('Unreviewed ACL filename escape')
    name = os.fsdecode(bytes(result))
    relative = name[2:] if name.startswith('./') else name
    path = PurePosixPath(relative)
    if (not relative or '\0' in relative or path.is_absolute() or '..' in path.parts
            or path.as_posix() != relative):
        raise ValueError('ACL filename is not canonical relative image data')
    return relative


def metadata(root):
    """Inspect physical metadata without reading user-file contents."""
    names = ['.']
    for parent, directories, files in os.walk(root, followlinks=False):
        for name in directories + files:
            path = Path(parent) / name
            if path.lstat().st_dev != root.stat().st_dev:
                raise ValueError('ACL image tree crosses a filesystem')
            names.append(path.relative_to(root).as_posix())
    result = {}
    for name in names:
        path = root / name
        info = path.lstat()
        if (name != '.' and path.parent.resolve() != path.parent
                or not (stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode) or stat.S_ISLNK(info.st_mode))):
            raise ValueError('ACL image tree has a redirected parent or special node')
        result[name] = {'mode': info.st_mode, 'uid': info.st_uid, 'gid': info.st_gid,
                        'inode': info.st_ino, 'links': info.st_nlink,
                        'xattrs': {key: hashlib.sha256(os.getxattr(path, key, follow_symlinks=False)).hexdigest()
                                   for key in os.listxattr(path, follow_symlinks=False)}}
    return result


def validate_stream(data, expected):
    records = []
    for block in data.split(b'\n\n'):
        if not block:
            continue
        lines = block.split(b'\n')
        if len(lines) < 6 or not lines[0].startswith(b'# file: '):
            raise ValueError('Unexpected native ACL record')
        name = decode_name(lines[0][8:])
        if name not in expected or stat.S_ISLNK(expected[name]['mode']) or name in records:
            raise ValueError('ACL record names an absent, redirected or duplicate path')
        row = expected[name]
        if lines[1:3] != [('# owner: ' + str(row['uid'])).encode(), ('# group: ' + str(row['gid'])).encode()]:
            raise ValueError('ACL stream numeric owner/group differs')
        flags = ''.join(value if row['mode'] & bit else '-'
                        for bit, value in ((stat.S_ISUID, 's'), (stat.S_ISGID, 's'), (stat.S_ISVTX, 't')))
        actual_flags = [line for line in lines if line.startswith(b'# flags: ')]
        if actual_flags != ([] if flags == '---' else [('# flags: ' + flags).encode()]):
            raise ValueError('ACL stream special-mode flags differ')
        records.append(name)
    required = {name for name, row in expected.items()
                if 'system.posix_acl_access' in row['xattrs'] or 'system.posix_acl_default' in row['xattrs']}
    if set(records) != required:
        raise ValueError('Native ACL stream does not cover the image extended ACLs exactly')
    return records


def stage_acl(backend, image, records_directory=Path('/var/log/toddy/packages')):
    image = Path(image)
    if (not backend.native or os.geteuid() != 0 or image.resolve() != image or not image.is_dir()
            or not any(image.is_relative_to(backend.target / area) for area in ('tmp', 'sources/stage'))):
        raise ValueError('ACL capture requires a fresh private native image')
    destination = image / SIDECAR
    partial = destination.with_name('.live-root.acl.part')
    if (destination.parent.resolve() != destination.parent or not destination.parent.is_dir()
            or destination.exists() or destination.is_symlink() or partial.exists() or partial.is_symlink()):
        raise ValueError('Preserve existing, redirected or interrupted ACL sidecar')
    tools = {}
    for package, programs in (('acl', ('getfacl', 'setfacl')), ('bash', ('bash',))):
        version, architecture, state = backend.run('dpkg-query', '-W', '-f=${Version}\t${Architecture}\t${Status}',
                                                   package, capture_output=True, text=True).stdout.split('\t')
        record = json.loads((Path(records_directory) / f'{package}_{version}_{architecture}.json').read_text())
        if state != 'install ok installed' or not record['installed'] or record['name'] != package or record['version'] != version:
            raise ValueError('ACL tool provider is not accepted/configured')
        for program in programs:
            virtual = '/usr/bin/' + program
            source = backend.target / virtual[1:]
            if source.parent.resolve() != source.parent or source.is_symlink() or digest(source) != record['payload'][virtual]['sha256']:
                raise ValueError('Native ACL tool bytes/provenance differ')
            tools[program] = {'version': version, 'archive_sha256': record['archive_sha256'], 'sha256': digest(source)}
    before = metadata(image)
    def capture():
        result = backend.run('bash', '--noprofile', '--norc', '-c',
            'cd -- "$1" && exec /usr/bin/getfacl -R -P -p -n --skip-base --one-file-system .',
            'toddy-acl-capture', '/' + str(image.relative_to(backend.target)), capture_output=True, timeout=120)
        if result.stderr:
            raise ValueError('Native ACL capture produced diagnostics')
        return result.stdout
    stream = capture()
    names = validate_stream(stream, before)
    if metadata(image) != before:
        raise ValueError('Image metadata changed during ACL capture')
    with partial.open('xb') as output:
        output.write(stream)
        output.flush()
        # This generated public metadata file must not inherit an extended ACL
        # from its parent and recursively become part of its own capture.
        if 'system.posix_acl_access' in os.listxattr(partial):
            os.removexattr(partial, 'system.posix_acl_access')
        os.fchmod(output.fileno(), 0o644)
        os.fchown(output.fileno(), 0, 0)
        os.fsync(output.fileno())
    partial.replace(destination)
    descriptor = os.open(destination.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    after = metadata(image)
    generated = after.pop(SIDECAR)
    if (after != before or generated['mode'] != stat.S_IFREG | 0o644
            or generated['uid'] != 0 or generated['gid'] != 0 or generated['xattrs']
            or destination.read_bytes() != stream or capture() != stream):
        raise ValueError('ACL sidecar readback or source metadata differs')
    return {'path': '/' + SIDECAR, 'bytes': len(stream), 'sha256': digest(destination),
            'acl_paths': names, 'image_entries_inspected': len(before), 'native_tools': tools,
            'physical_numeric_capture': True,
            'source_permissions_ownership_xattrs_and_links_unchanged': True,
            'squashfs_overlay_or_native_boot_verified': False}
