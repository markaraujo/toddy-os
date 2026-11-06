"""Check a prepared core/QA pair against its complete own predecessor payload.

The caller must verify archive bytes, control fields and record provenance.
This check grants no installation permission and changes no package state.
"""
from python_qa_handoff import is_qa, qa_dependencies


def validate(donor, core, qa, *, donor_record_sha256, controls):
    if (donor.get('name') != 'python' or donor.get('installed') is not True
            or core.get('name') != 'python' or qa.get('name') != 'python-test-support'):
        raise ValueError('Expected an installed own Python predecessor and a core/QA pair')
    version = core['version']
    if not version or version == donor['version'] or qa['version'] != version:
        raise ValueError('Core and QA must share a distinct successor version')
    if not donor['sources'] or not (donor['sources'] == core['sources'] == qa['sources']):
        raise ValueError('Source provenance differs across the ownership transfer')
    expected_qa = {path: row for path, row in donor['payload'].items() if is_qa(path)}
    expected_core = {path: row for path, row in donor['payload'].items() if not is_qa(path)}
    if not expected_qa or core['payload'] != expected_core:
        raise ValueError('Runtime replacement must be exactly its predecessor minus QA')
    actual_qa = {path: row for path, row in qa['payload'].items() if is_qa(path)}
    if actual_qa != expected_qa:
        raise ValueError('QA replacement must preserve the complete original regression payload')
    parents = {'/usr', '/usr/lib', '/usr/lib/python3.14', '/usr/lib/python3.14/idlelib',
               '/usr/lib/python3.14/tkinter', '/usr/share', '/usr/share/doc'}
    notice = '/usr/share/doc/python-test-support'
    for path, row in qa['payload'].items():
        if path in expected_qa or path == notice or path.startswith(notice + '/'):
            continue
        if (path not in parents or row != {'mode': 0o40755, 'uid': 0, 'gid': 0, 'directory': True}):
            raise ValueError('QA replacement contains unrelated payload: ' + path)
    files = sorted(path for path, row in expected_qa.items() if not row.get('directory'))
    handoff = qa['prepared_ownership_handoff']
    required = {'kind': 'python-qa-archive-only', 'predecessor': 'python',
                'predecessor_version': donor['version'], 'successor_version': version,
                'predecessor_archive_sha256': donor['archive_sha256'],
                'predecessor_record_sha256': donor_record_sha256,
                'transferred_paths': files, 'transferred_path_count': len(files),
                'installation_authorized': False}
    if any(handoff.get(key) != value for key, value in required.items()) or not files:
        raise ValueError('Prepared handoff identity or complete file list differs')
    # These fields must be read from hash-verified actual native archives by
    # the caller, not inferred from record names or supplied CLI metadata.
    old_control, core_control, qa_control = controls
    for record, control in zip((donor, core, qa), controls):
        if control['Package'] != record['name'] or control['Version'] != record['version']:
            raise ValueError('Native archive identity differs from its own record')
        if control['Architecture'] != old_control['Architecture']:
            raise ValueError('Ownership transfer changed native architecture')
    if core_control.get('Depends', '') != old_control.get('Depends', ''):
        raise ValueError('Runtime replacement changed its dependency contract')
    if qa_control.get('Depends') != qa_dependencies(version):
        raise ValueError('QA dependency contract is incomplete')
    return {'version': version, 'transferred_files': len(files),
            'retained_runtime_files': sum(not row.get('directory') for row in expected_core.values()),
            'runtime_payload_unchanged': True, 'qa_payload_unchanged': True,
            'installation_authorized': False}
