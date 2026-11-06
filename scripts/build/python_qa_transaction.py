"""Execute an ownership transfer with durable intent and native postconditions.

Only the gated production entry point chooses the installed target. Private
probes may use another explicit directory inside the designated build guest.
No package archive or record is synthesized by this executor.
"""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

from prepare_python_qa import read_control
from python_qa_bundle import validate
from python_qa_transfer import INSTALLED, next_action
from stage_package import digest, payload


def atomic_json(path, value):
    if path.is_symlink() or path.parent.resolve() != path.parent:
        raise ValueError('Transaction record path redirects')
    fd, temporary = tempfile.mkstemp(prefix=path.name + '.', dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as stream:
            stream.write(json.dumps(value, indent=2) + '\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def installed_owners(target):
    owners = {}
    for listing in (target / 'var/lib/dpkg/info').glob('*.list'):
        for path in listing.read_text().splitlines():
            owners.setdefault(path.rstrip('/'), set()).add(listing.stem.split(':')[0])
    return owners


def verify_payload(target, record, owners):
    count = 0
    for virtual, expected in record['payload'].items():
        if not virtual.startswith('/') or '..' in Path(virtual).parts:
            raise ValueError('Unexpected payload path')
        if expected.get('directory'):
            continue
        path = target / virtual.lstrip('/')
        if path.parent.resolve() != path.parent:
            raise ValueError('Installed payload parent redirects: ' + virtual)
        info = path.lstat()
        if (info.st_mode, info.st_uid, info.st_gid) != (expected['mode'], expected['uid'], expected['gid']):
            raise ValueError('Installed payload metadata differs: ' + virtual)
        if 'sha256' in expected:
            if digest(path) != expected['sha256']:
                raise ValueError('Installed payload bytes differ: ' + virtual)
        elif path.readlink().as_posix() != expected['symlink']:
            raise ValueError('Installed payload link differs: ' + virtual)
        if owners.get(virtual) != {record['name']}:
            raise ValueError('Installed payload has missing/ambiguous ownership: ' + virtual)
        count += 1
    return count


def execute(backend, target, records, archives, journal, *, donor_record_sha256):
    """Verify all ingredients, advance bounded native actions and verify again.

    records/archives are ordered predecessor, successor core, successor QA.
    The return does not update provenance records: the production caller does
    that only after this complete verification, with its own durable writes.
    """
    target, journal = Path(target), Path(journal)
    if (not backend.native or target.resolve() != target or not target.is_dir() or not target.is_relative_to(backend.target)
            or journal.is_symlink() or journal.parent.resolve() != journal.parent or not journal.parent.is_relative_to(backend.target)
            or not journal.parent.is_dir()):
        raise ValueError('Transfer requires an explicit native guest target and private journal directory')
    if journal.parent.stat().st_uid != os.geteuid() or journal.parent.stat().st_mode & 0o022:
        raise ValueError('Transaction directory must not be writable by other users')
    lock_path = journal.with_suffix('.lock')
    lock_fd = os.open(lock_path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return _execute_locked(backend, target, records, archives, journal, donor_record_sha256)
    finally:
        os.close(lock_fd)


def _execute_locked(backend, target, records, archives, journal, donor_record_sha256):
    def virtual(path):
        path = Path(path)
        if path.resolve() != path or not path.is_relative_to(backend.target):
            raise ValueError('Archive/target path redirects or leaves the native guest')
        return '/' + str(path.relative_to(backend.target))

    if len(records) != 3 or len(archives) != 3:
        raise ValueError('Exactly one predecessor and two successors are required')
    donor, core, qa = records
    controls = []
    extracted = Path(tempfile.mkdtemp(prefix='verified-archives-', dir=journal.parent))
    try:
        for index, (record, archive) in enumerate(zip(records, archives)):
            virtual(archive)
            if digest(archive) != record['archive_sha256']:
                raise ValueError('Transfer archive hash differs from its own record')
            controls.append(read_control(backend, Path(archive)))
            stage = extracted / str(index)
            backend.run('dpkg-deb', '--raw-extract', virtual(archive), virtual(stage))
            control = stage / 'DEBIAN'
            if any(path.name not in {'control', 'conffiles', 'md5sums'} for path in control.iterdir()):
                raise ValueError('Unexpected control program in ownership transfer')
            entries = {path: row for path, row in payload(stage).items()
                       if path != '/DEBIAN' and not path.startswith('/DEBIAN/')}
            if entries != record['payload']:
                raise ValueError('Extracted transfer archive differs from recorded complete payload')
        conffiles = []
        for index in range(3):
            path = extracted / str(index) / 'DEBIAN/conffiles'
            conffiles.append(path.read_bytes() if path.exists() else b'')
        if conffiles[0] != conffiles[1] or conffiles[2]:
            raise ValueError('Ownership transfer changed the runtime conffile contract')
        checked = validate(donor, core, qa, donor_record_sha256=donor_record_sha256, controls=controls)
    except BaseException:
        print('Preserved transfer archive inspection:', extracted, flush=True)
        raise
    else:
        shutil.rmtree(extracted)
    backend.run('dpkg', '--compare-versions', core['version'], 'gt', donor['version'])
    # installed is a mutable bookkeeping flag. All other provenance bytes are
    # bound to this transaction; actual package state is queried independently.
    identities = [hashlib.sha256(json.dumps({key: value for key, value in record.items() if key != 'installed'},
                  sort_keys=True).encode()).hexdigest() for record in records]
    identity = {'target': str(target), 'archive_sha256': [record['archive_sha256'] for record in records],
                'record_identities': identities, 'predecessor_record_sha256': donor_record_sha256}
    database = virtual(target / 'var/lib/dpkg')

    def states():
        text = backend.run('dpkg-query', '--admindir=' + database, '-W',
                           '-f=${Package}\t${Version}\t${Status}\n', capture_output=True, text=True).stdout
        rows = [line.split('\t') for line in text.splitlines()]
        return {name: (version, state) for name, version, state in rows}

    current = states()
    if journal.exists():
        transaction = json.loads(journal.read_text())
        if transaction.get('identity') != identity or transaction.get('schema_version') != 1:
            raise ValueError('Existing transaction belongs to different verified ingredients')
    else:
        if current.get('python') != (donor['version'], INSTALLED) or 'python-test-support' in current:
            raise ValueError('Unrecorded ownership transfer or incomplete predecessor requires diagnosis')
        verify_payload(target, donor, installed_owners(target))
        transaction = {'schema_version': 1, 'identity': identity, 'actions': [], 'complete': False}
        atomic_json(journal, transaction)
    root_option = [] if target == backend.target else ['--root=' + virtual(target)]
    for _ in range(8):
        current = states()
        action = next_action(donor['version'], core['version'], current.get('python'),
                             current.get('python-test-support'), transaction_started=True)
        if action == 'verify_complete':
            owners = installed_owners(target)
            verified = {record['name']: verify_payload(target, record, owners) for record in (core, qa)}
            audit = backend.run('dpkg', *root_option, '--audit', capture_output=True, text=True)
            if audit.stdout.strip() or audit.stderr.strip():
                raise ValueError('Native Dpkg audit is not clean after transfer')
            runtime = subprocess.run(['/usr/sbin/chroot', str(target), '/usr/bin/env', '-i',
                'PATH=/usr/bin:/usr/sbin', 'LC_ALL=C', '/usr/bin/python3', '-I', '-B', '-c',
                'import ssl,sqlite3,test.support; ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT); '
                'db=sqlite3.connect(":memory:"); assert db.execute("select 6*7").fetchone()==(42,); '
                'print("PYTHON_QA_RUNTIME_OK",ssl.OPENSSL_VERSION)'], check=True, capture_output=True, text=True)
            if not runtime.stdout.startswith('PYTHON_QA_RUNTIME_OK '):
                raise ValueError('Native runtime postcondition is missing')
            transaction.update(complete=True, verification={'bundle': checked, 'files': verified,
                               'dpkg_audit_clean': True, 'runtime_stdout': runtime.stdout})
            atomic_json(journal, transaction)
            return transaction
        if action == 'install_qa':
            owners = installed_owners(target)
            for path in qa['prepared_ownership_handoff']['transferred_paths']:
                present = target / path.lstrip('/')
                if owners.get(path, set()) - {'python-test-support'}:
                    raise ValueError('Original/other owner has not released QA path: ' + path)
                if not owners.get(path) and (present.exists() or present.is_symlink()):
                    raise ValueError('Unowned QA file requires preservation/review: ' + path)
        attempt = {'action': action, 'before': current, 'exit': None}
        transaction['actions'].append(attempt)
        transaction['complete'] = False
        atomic_json(journal, transaction)  # Durable intent before any Dpkg mutation.
        log = journal.parent / ('action-' + str(len(transaction['actions'])) + '.log')
        if action.startswith('install_'):
            archive = archives[1 if action == 'install_core' else 2]
            arguments = ['--force-confold', '--force-confdef', '--install', virtual(archive)]
        else:
            arguments = ['--configure', 'python' if action == 'configure_core' else 'python-test-support']
        try:
            with log.open('x') as output:
                backend.run('dpkg', *root_option, *arguments, stdout=output, stderr=subprocess.STDOUT, text=True)
                output.flush()
                os.fsync(output.fileno())
        except subprocess.CalledProcessError as error:
            attempt['exit'] = error.returncode
            atomic_json(journal, transaction)
            raise
        attempt['exit'] = 0
        attempt['after'] = states()
        atomic_json(journal, transaction)
        if attempt['after'] == current:
            raise ValueError('Native transfer action returned success without state progress')
    raise ValueError('Ownership transfer exceeded its bounded action count')
