"""Remove optional QA from a private image through native package operations.

The gated assembler must supply verified own records/archives and a fresh image.
This component never changes the installed builder or silently deletes payload.
Any failed/interrupted attempt remains a partial image to preserve and rebuild.
"""
import json
import os
from pathlib import Path
import stat
import subprocess

from python_qa_handoff import QA_ROOTS, is_qa
from python_qa_transaction import atomic_json, installed_owners, verify_payload
from stage_package import digest

PACKAGE = 'python-test-support'
QUERY = '${Package}\t${Version}\t${Architecture}\t${Status}\n'


def removable_document(path, row, core):
    """Only exact copies of the runtime's retained legal metadata may leave."""
    prefix = '/usr/share/doc/python-test-support/'
    if not path.startswith(prefix) or not row.get('sha256'):
        return False
    suffix = path[len(prefix):]
    if suffix != 'copyright' and not (suffix.startswith('source-notices/')
            and '/' not in suffix[len('source-notices/'):]):
        return False
    return row == core['payload'].get('/usr/share/doc/python/' + suffix)


def remove_image_qa(backend, image, core, qa, journal):
    image, journal = Path(image), Path(journal)
    if (not backend.native or os.geteuid() != 0 or image.resolve() != image or not image.is_dir()
            or not any(image.is_relative_to(backend.target / area) for area in ('tmp', 'sources/stage'))):
        raise ValueError('QA removal requires a private native image, never the installed target')
    if (journal.parent.resolve() != journal.parent or not journal.parent.is_dir()
            or not any(journal.parent.is_relative_to(backend.target / area) for area in ('tmp', 'sources/stage'))
            or journal.is_relative_to(image) or journal.parent.stat().st_uid != 0
            or journal.parent.stat().st_mode & 0o022):
        raise ValueError('QA removal requires a protected journal outside the image')
    log = journal.with_suffix('.dpkg.log')
    if any(path.exists() or path.is_symlink() for path in (journal, log)):
        raise ValueError('Preserve prior QA removal evidence; use a fresh image attempt')
    if (core.get('name') != 'python' or qa.get('name') != PACKAGE
            or core.get('version') != qa.get('version') or not qa.get('payload')
            or not core.get('sources') or core['sources'] != qa.get('sources')):
        raise ValueError('Expected the verified matching native Python core/QA pair')
    if any(is_qa(path) for path in core['payload']):
        raise ValueError('Runtime still owns QA paths; complete the ownership transfer first')
    for path, row in qa['payload'].items():
        if not row.get('directory') and not (is_qa(path) or removable_document(path, row, core)):
            raise ValueError('QA record contains an unexpected removable payload: ' + path)
    if not any(is_qa(path) and not row.get('directory') for path, row in qa['payload'].items()):
        raise ValueError('An empty QA record is not release exclusion evidence')
    database = image / 'var/lib/dpkg'
    if database.resolve() != database or (database / 'info').resolve() != database / 'info':
        raise ValueError('Image package metadata redirects')
    for path in (database / 'info').glob(PACKAGE + '.*'):
        if path.name not in {PACKAGE + '.list', PACKAGE + '.md5sums'}:
            raise ValueError('Unexpected QA maintainer program or configuration: ' + path.name)
        info = path.lstat()
        if not stat.S_ISREG(info.st_mode) or info.st_uid != 0 or info.st_mode & 0o022:
            raise ValueError('Image QA metadata is not protected regular data')
    native_image = '/' + str(image.relative_to(backend.target))
    native_database = native_image + '/var/lib/dpkg'
    def identities():
        raw = backend.run('dpkg-query', '--admindir=' + native_database, '-W', '-f=' + QUERY,
                          capture_output=True, text=True).stdout
        rows = {}
        for line in raw.splitlines():
            name, version, architecture, state = line.split('\t')
            if name in rows or state != 'install ok installed':
                raise ValueError('Image contains an incomplete package state: ' + name)
            rows[name] = {'version': version, 'architecture': architecture, 'state': state}
        return rows
    before = identities()
    for record in (core, qa):
        if before.get(record['name'], {}).get('version') != record['version']:
            raise ValueError('Image package version differs from the verified pair')
    owners = installed_owners(image)
    listed = {path for path, names in owners.items() if PACKAGE in names} - {'/.', '/', ''}
    if listed != set(qa['payload']):
        raise ValueError('Native QA file list differs from the verified removable payload')
    core_files = verify_payload(image, core, owners)
    qa_files = verify_payload(image, qa, owners)
    source_status = backend.target / 'var/lib/dpkg/status'
    source_before = digest(source_status)
    report = {'complete': False, 'image': str(image), 'package': PACKAGE,
              'version': qa['version'], 'qa_files_before': qa_files,
              'runtime_files_verified': core_files,
              'image_status_before_sha256': digest(database / 'status'),
              'builder_status_before_sha256': source_before, 'native_exit': None,
              'whole_image_or_boot_accepted': False}
    atomic_json(journal, report)
    try:
        with log.open('x') as output:
            os.fchmod(output.fileno(), 0o600)
            result = backend.run('dpkg', '--root=' + native_image, '--purge', PACKAGE,
                                 stdout=output, stderr=subprocess.STDOUT)
        report['native_exit'] = result.returncode
        atomic_json(journal, report)
        after = identities()
        if after != {name: row for name, row in before.items() if name != PACKAGE}:
            raise ValueError('Native QA removal changed unrelated package identities')
        after_owners = installed_owners(image)
        if any(PACKAGE in names for names in after_owners.values()):
            raise ValueError('QA ownership remains in the image database')
        for path, row in qa['payload'].items():
            actual = image / path[1:]
            if not row.get('directory') and (actual.exists() or actual.is_symlink()):
                raise ValueError('QA file remains after native removal: ' + path)
        for path in QA_ROOTS:
            actual = image / path[1:]
            if actual.exists() or actual.is_symlink():
                raise ValueError('QA tree contains residual data after removal: ' + path)
        if verify_payload(image, core, after_owners) != core_files:
            raise ValueError('Python runtime changed during QA removal')
        audit = backend.run('dpkg', '--admindir=' + native_database, '--audit', capture_output=True, text=True)
        if audit.stdout or audit.stderr:
            raise ValueError('Image package database audit is not clean after QA removal')
        if digest(source_status) != source_before:
            raise ValueError('Installed builder package state changed during private removal')
        report.update(complete=True, packages_retained=len(after),
                      image_status_after_sha256=digest(database / 'status'),
                      builder_status_unchanged=True, runtime_payload_and_ownership_unchanged=True,
                      qa_payload_and_ownership_absent=True, native_database_audit_clean=True)
        return report
    except BaseException as error:
        if isinstance(error, subprocess.CalledProcessError):
            report['native_exit'] = error.returncode
        report['error'] = str(error)
        raise
    finally:
        if log.exists():
            report['native_log_sha256'] = digest(log)
        atomic_json(journal, report)
