"""Authorize only an unchanged, complete Python QA archive preparation.

No install operation is permitted by this plan. The real installer must still
observe that the predecessor released every transferred path.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import stat

# h11 is also the name of an unrelated third-party HTTP package. Load the
# project-owned layout by its explicit path rather than namespace resolution.
_layout_spec = importlib.util.spec_from_file_location(
    'toddy_python_qa_layout', Path(__file__).resolve().parent / 'h11/python_qa.py')
_layout = importlib.util.module_from_spec(_layout_spec)
_layout_spec.loader.exec_module(_layout)
QA_ROOTS = _layout.QA_ROOTS


def qa_dependencies(version):
    # Frozen QA executable fixtures use /bin/bash and /usr/bin/env python3.
    # Keep direct providers explicit even when Python also depends on them.
    return f'python (= {version}), bash, coreutils'


def is_qa(path):
    return any(path == root or path.startswith(root + '/') for root in QA_ROOTS)


def plan(entries, ownership, donor, *, name, version, architecture, donor_architecture,
         depends, sources, install, native):
    if install or not native or name != 'python-test-support':
        raise ValueError('Python QA handoff is native archive-only preparation for python-test-support')
    if donor.get('name') != 'python' or donor.get('installed') is not True:
        raise ValueError('Python QA requires an installed native Python predecessor')
    if architecture != donor_architecture or depends != qa_dependencies(version):
        raise ValueError('QA architecture, exact Python successor and direct interpreter providers must match')
    if sorted(sources) != sorted(row['filename'] for row in donor['sources']):
        raise ValueError('QA must retain the complete predecessor source set')
    expected = {path: value for path, value in donor['payload'].items() if is_qa(path)}
    actual = {path: value for path, value in entries.items() if is_qa(path)}
    if not expected or actual != expected:
        raise ValueError('QA payload must exactly match the complete predecessor tree')
    required_roots = {root for root in QA_ROOTS if root in expected}
    if QA_ROOTS[0] not in required_roots:
        raise ValueError('Frozen main Python test tree is missing')
    doc = '/usr/share/doc/python-test-support'
    allowed_parents = {'/usr', '/usr/lib', '/usr/lib/python3.14',
                       '/usr/lib/python3.14/idlelib', '/usr/lib/python3.14/tkinter',
                       '/usr/share', '/usr/share/doc'}
    files = []
    for path, entry in entries.items():
        if path not in expected and not (path == doc or path.startswith(doc + '/')):
            if path not in allowed_parents or not entry.get('directory'):
                raise ValueError('Unrelated payload in QA handoff: ' + path)
            if (entry['mode'], entry['uid'], entry['gid']) != (stat.S_IFDIR | 0o755, 0, 0):
                raise ValueError('Unexpected shared parent directory metadata')
        if entry.get('directory'):
            continue
        owners = ownership.get(path, set())
        if path in expected:
            if owners not in ({'python'}, {'python:' + donor_architecture}):
                raise ValueError('QA handoff path lacks its unique predecessor owner: ' + path)
            files.append(path)
        elif owners:
            raise ValueError('QA notice would overwrite an existing owned path: ' + path)
    if not files:
        raise ValueError('Empty QA ownership handoff')
    return {'kind': 'python-qa-archive-only', 'predecessor': 'python',
            'predecessor_version': donor['version'], 'successor_version': version,
            'predecessor_archive_sha256': donor['archive_sha256'],
            'transferred_paths': sorted(files), 'transferred_path_count': len(files),
            'installation_authorized': False,
            'installation_requirement': 'Every transferred path must first be released by its old owner; configured dependencies and postchecks remain mandatory.'}


def prepare(backend, target, cache, records, entries, ownership, stage, args):
    if not backend.native or args.install or args.name != 'python-test-support':
        raise ValueError('Python QA handoff cannot install or use bootstrap tools')
    identity = backend.run('dpkg-query', '-W', '-f=${Version}\t${Architecture}\t${Status}',
                           'python', capture_output=True, text=True).stdout
    version, architecture, status = identity.split('\t')
    if status != 'install ok installed':
        raise ValueError('Native Python predecessor is not configured')
    backend.run('dpkg', '--compare-versions', args.version, 'gt', version)
    record_path = records / f'python_{version}_{architecture}.json'
    donor = json.loads(record_path.read_text())
    if donor.get('version') != version:
        raise ValueError('Python predecessor version record differs')
    archive = cache / f'python_{version}_{architecture}.deb'
    with archive.open('rb') as stream:
        if hashlib.file_digest(stream, 'sha256').hexdigest() != donor['archive_sha256']:
            raise ValueError('Python predecessor archive differs')
    result = plan(entries, ownership, donor, name=args.name, version=args.version,
                  architecture=args.architecture, donor_architecture=architecture,
                  depends=args.depends, sources=args.source, install=args.install, native=backend.native)
    # Refuse to move a modified installed payload silently into an old archive.
    # No installed or staged files are changed by this verification.
    for virtual in result['transferred_paths']:
        current = target / virtual.lstrip('/')
        staged = stage / virtual.lstrip('/')
        expected = donor['payload'][virtual]
        if current.parent.resolve() != current.parent:
            raise ValueError('Installed QA parent redirects: ' + virtual)
        info = current.lstat()
        if (info.st_mode, info.st_uid, info.st_gid) != (expected['mode'], expected['uid'], expected['gid']):
            raise ValueError('Installed QA metadata changed: ' + virtual)
        if info.st_mtime_ns != staged.lstat().st_mtime_ns:
            raise ValueError('Staged QA timestamp differs from installed predecessor: ' + virtual)
        if 'sha256' in expected:
            with current.open('rb') as stream:
                if hashlib.file_digest(stream, 'sha256').hexdigest() != expected['sha256']:
                    raise ValueError('Installed QA bytes changed: ' + virtual)
        elif current.readlink().as_posix() != expected['symlink']:
            raise ValueError('Installed QA link changed: ' + virtual)
    result['predecessor_record_sha256'] = hashlib.sha256(record_path.read_bytes()).hexdigest()
    return result
