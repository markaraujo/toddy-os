"""Copy an explicit live-root inventory with native Tar and verify metadata.

Selection/provenance and milestone guards belong to the assembly caller. This
component never discovers extra files to include or follows a source symlink.
"""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def checked_names(names):
    names = list(names)
    if any(not isinstance(name, str) for name in names):
        raise ValueError('Image inventory paths must be strings')
    selected = set(names)
    if not names or len(names) != len(selected) or '.' not in selected:
        raise ValueError('A unique explicit inventory including its root is required')
    for name in names:
        path = PurePosixPath(name)
        if (not name or '\0' in name or path.is_absolute()
                or '..' in path.parts or path.as_posix() != name):
            raise ValueError('Noncanonical relative image path')
        if name != '.' and path.parent.as_posix() not in selected:
            raise ValueError('Every inventory parent directory must be explicit')
    return sorted(names, key=os.fsencode)


def snapshot(root, names):
    root = Path(root)
    if root.resolve() != root or not root.is_dir():
        raise ValueError('Source/stage root must be a canonical directory')
    names = checked_names(names)
    entries, links = {}, {}
    device = root.stat().st_dev
    for name in names:
        path = root if name == '.' else root / name
        if name != '.' and path.parent.resolve() != path.parent:
            raise ValueError('Selected parent redirects: ' + name)
        info = path.lstat()
        if info.st_dev != device:
            raise ValueError('Selected path crosses a filesystem boundary: ' + name)
        entry = {'mode': info.st_mode, 'uid': info.st_uid, 'gid': info.st_gid,
                 'mtime_ns': info.st_mtime_ns}
        if stat.S_ISREG(info.st_mode):
            entry.update(sha256=digest(path), size=info.st_size)
        elif stat.S_ISLNK(info.st_mode):
            entry['symlink'] = path.readlink().as_posix()
        elif not stat.S_ISDIR(info.st_mode):
            raise ValueError('Selected special node is not image payload: ' + name)
        entry['xattrs'] = {key: hashlib.sha256(os.getxattr(path, key, follow_symlinks=False)).hexdigest()
                          for key in sorted(os.listxattr(path, follow_symlinks=False))}
        entries[name] = entry
        if not stat.S_ISDIR(info.st_mode):
            links.setdefault((info.st_dev, info.st_ino), []).append(name)
    groups = sorted(sorted(group) for group in links.values() if len(group) > 1)
    return {'entries': entries, 'hardlink_groups': groups}


def tree_names(root):
    names = ['.']
    for base, dirs, files in os.walk(root, followlinks=False):
        names.extend(str((Path(base) / name).relative_to(root)) for name in dirs + files)
    return names


def copy_selected(backend, source, destination, work, names, records=Path('/var/log/toddy/packages')):
    source, destination, work = map(Path, (source, destination, work))
    if not backend.native:
        raise ValueError('Live-root copy requires accepted native tools')
    for path in (source, destination, work):
        if path.resolve() != path or not path.is_relative_to(backend.target):
            raise ValueError('Live-root copy paths must stay in the explicit native guest')
    if (destination.exists() or work.exists() or destination.is_symlink() or work.is_symlink()
            or destination.is_relative_to(work) or work.is_relative_to(destination)
            or source.is_relative_to(destination) or source.is_relative_to(work)):
        raise ValueError('Copy needs fresh disjoint stage/work directories outside source ancestors')
    names = checked_names(names)
    for name in names:
        selected = source / name
        if selected.is_relative_to(destination) or selected.is_relative_to(work):
            raise ValueError('The source inventory includes its own output')
    expected = snapshot(source, names)
    identity = backend.run('dpkg-query', '-W', '-f=${Version}\t${Architecture}\t${Status}',
                           'tar', capture_output=True, text=True).stdout.split('\t')
    version, architecture, status = identity
    record = json.loads((records / f'tar_{version}_{architecture}.json').read_text())
    executable = backend.target / 'usr/bin/tar'
    if (status != 'install ok installed' or not record['installed'] or record['name'] != 'tar'
            or digest(executable) != record['payload']['/usr/bin/tar']['sha256']):
        raise ValueError('Native archive tool provenance differs')
    tool_version = backend.run('tar', '--version', capture_output=True, text=True).stdout.splitlines()[0]
    if tool_version != 'tar (GNU tar) 1.35':
        raise ValueError('Unexpected native Tar version')
    work.mkdir(mode=0o700)
    destination.mkdir(mode=0o700)
    # Preserve the already inspected source generation, including ACL/xattr
    # hashes, so final image attribution need not trust a later source read.
    input_manifest = work / 'input-manifest.json'
    with input_manifest.open('x') as stream:
        json.dump(expected, stream, indent=2, sort_keys=True)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    listing = b'\0'.join(os.fsencode(name) for name in names) + b'\0'
    (work / 'selected-paths.nul').write_bytes(listing)
    def virtual(path):
        return '/' + str(path.relative_to(backend.target))
    archive = work / 'selected-root.tar'
    with (work / 'create.log').open('xb') as log:
        backend.run('tar', '--create', '--file=' + virtual(archive), '--format=pax',
                    '--acls', '--xattrs', '--xattrs-include=*', '--numeric-owner', '--sparse',
                    '--no-recursion', '--null', '--verbatim-files-from',
                    '--directory=' + virtual(source), '--files-from=-', input=listing, stdout=log, stderr=log)
    if snapshot(source, names) != expected:
        raise ValueError('Selected source changed during archive creation')
    with (work / 'extract.log').open('xb') as log:
        backend.run('tar', '--extract', '--file=' + virtual(archive), '--directory=' + virtual(destination),
                    '--acls', '--xattrs', '--xattrs-include=*', '--numeric-owner', '--same-owner',
                    '--same-permissions', '--delay-directory-restore', stdout=log, stderr=log)
    actual = snapshot(destination, tree_names(destination))
    if actual != expected:
        (work / 'expected.json').write_text(json.dumps(expected, indent=2) + '\n')
        (work / 'actual.json').write_text(json.dumps(actual, indent=2) + '\n')
        raise ValueError('Copied image bytes, metadata, hardlinks or inventory differ')
    if snapshot(source, names) != expected:
        raise ValueError('Selected source changed during copy verification')
    report = {'entries': len(names), 'regular_files': sum('sha256' in row for row in expected['entries'].values()),
              'hardlink_groups': expected['hardlink_groups'], 'exact_inventory_and_metadata': True,
              'archive_sha256': digest(archive), 'inventory_sha256': hashlib.sha256(listing).hexdigest(),
              'input_manifest': input_manifest.name, 'input_manifest_sha256': digest(input_manifest),
              'native_tar': {'version': tool_version, 'sha256': digest(executable),
                             'own_archive_sha256': record['archive_sha256']},
              'root_image_or_boot_verified': False}
    (work / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    return report
