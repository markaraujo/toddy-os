#!/usr/bin/env python3
"""Verify exact npm archives and installed bytes; retain declared license evidence."""
import base64
from concurrent.futures import ThreadPoolExecutor
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import tarfile
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / '.local/sources'
TREE = ROOT / '.local/phase2/pi-source'
NOTICES = ROOT / '.local/phase2/engine-notices'


def inspect(item):
    location, row = item
    assert row['resolved'].startswith('https://registry.npmjs.org/')
    algorithm, expected = row['integrity'].split('-', 1)
    assert algorithm == 'sha512'
    expected = base64.b64decode(expected, validate=True)
    archive = CACHE / ('npm-' + expected.hex() + '.tgz')
    if not archive.exists():
        with urllib.request.urlopen(row['resolved'], timeout=60) as response:
            data = response.read(64 * 1024 * 1024 + 1)
        assert len(data) <= 64 * 1024 * 1024
        assert hashlib.sha512(data).digest() == expected, 'npm integrity mismatch'
        part = archive.with_suffix('.tgz.part')
        part.write_bytes(data)
        part.replace(archive)
    data = archive.read_bytes()
    assert hashlib.sha512(data).digest() == expected, 'cached npm integrity mismatch'
    package = TREE / location
    metadata = json.loads((package / 'package.json').read_text())
    assert metadata['version'] == row['version'] and metadata['license'] == row['license']
    notices = []
    metadata_bytes = (package / 'package.json').read_bytes()
    metadata_sha = hashlib.sha256(metadata_bytes).hexdigest()
    (NOTICES / metadata_sha).write_bytes(metadata_bytes)
    payload = {}
    duplicate_members = []
    with tarfile.open(fileobj=io.BytesIO(data), mode='r:gz') as source:
        members = source.getmembers()
        assert len(members) <= 20000 and sum(m.size for m in members) <= 128 * 1024 * 1024
        roots = {PurePosixPath(m.name).parts[0] for m in members}
        assert len(roots) == 1 and not roots.intersection({'.', '..', ''})
        archive_root = next(iter(roots))
        for member in members:
            path = PurePosixPath(member.name)
            assert not path.is_absolute() and '..' not in path.parts and path.parts[0] == archive_root
            if member.isdir():
                continue
            assert member.isfile(), 'npm archive special/link payload needs review'
            relative = Path(*path.parts[1:])
            installed = package / relative
            assert installed.resolve().is_relative_to(package.resolve()) and not installed.is_symlink()
            content = source.extractfile(member).read()
            sha = hashlib.sha256(content).hexdigest()
            assert installed.read_bytes() == content, 'npm extracted bytes changed: ' + str(installed)
            if relative.as_posix() in payload:
                assert payload[relative.as_posix()] == sha, 'conflicting normalized npm archive members'
                duplicate_members.append({'path': member.name, 'sha256': sha})
                continue
            payload[relative.as_posix()] = sha
            name = relative.name.lower()
            legal = name.split('.')[0] in ('license', 'licence', 'copying', 'copyright', 'notice')
            readme_grant = name.startswith('readme') and b'Permission is hereby granted' in content
            if legal or readme_grant:
                destination = NOTICES / sha
                if not destination.exists():
                    destination.write_bytes(content)
                notices.append({'path': relative.as_posix(), 'sha256': sha, 'bytes': len(content)})
    return {'name': metadata['name'], 'version': row['version'], 'location': location,
        'url': row['resolved'], 'integrity': row['integrity'], 'archive_sha256': hashlib.sha256(data).hexdigest(),
        'archive_bytes': len(data), 'archive_root': archive_root, 'license': row['license'], 'author': metadata.get('author'),
        'repository': metadata.get('repository'), 'package_metadata_sha256': metadata_sha, 'retained_notices': notices,
        'verified_files': len(payload), 'identical_duplicate_members': duplicate_members, 'file_manifest_sha256': hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(',', ':')).encode()).hexdigest(),
        'lifecycle_scripts_executed': False, 'declared_install_script': bool(row.get('hasInstallScript'))}


if __name__ == '__main__':
    lock = ROOT / 'runtime/engine/package-lock.json'
    rows = json.loads(lock.read_text())['packages']
    NOTICES.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=4) as pool:
        components = list(pool.map(inspect, ((p, row) for p, row in rows.items() if p)))
    notice_lock = ROOT / 'config/phase2/engine-notices.lock.json'
    for notice in json.loads(notice_lock.read_text())['supplemental_notices']:
        path = NOTICES / notice['sha256']
        if not path.exists():
            data = urllib.request.urlopen(notice['url'], timeout=30).read()
            assert hashlib.sha256(data).hexdigest() == notice['sha256']
            path.write_bytes(data)
        assert hashlib.sha256(path.read_bytes()).hexdigest() == notice['sha256']
        for component in components:
            if component['name'] in notice['packages']:
                component['supplemental_notice'] = notice
    result = {'scope': 'exact npm archive/extracted byte and notice audit; native runtime proof separate',
              'lock_sha256': hashlib.sha256(lock.read_bytes()).hexdigest(),
              'notice_lock_sha256': hashlib.sha256(notice_lock.read_bytes()).hexdigest(),
              'components': components,
              'missing_archive_notices': [r['name'] for r in components if not r['retained_notices']],
              'missing_reviewed_terms': [r['name'] for r in components if not r['retained_notices'] and not r.get('supplemental_notice')]}
    assert not result['missing_reviewed_terms']
    output = ROOT / '.local/phase2/engine-inventory.json'
    part = output.with_suffix('.json.part')
    part.write_text(json.dumps(result, indent=2) + '\n')
    part.replace(output)
    print(json.dumps({'verified_packages': len(components),
        'verified_files': sum(r['verified_files'] for r in components),
        'missing_archive_notices': result['missing_archive_notices']}))
