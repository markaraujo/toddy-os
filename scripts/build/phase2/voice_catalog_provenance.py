"""Exact generated optional catalog provenance; no empty-source general exemption."""
from pathlib import Path
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent)]
import voice_process_reconcile as bridge

DOC = '/usr/share/doc/toddy-voice-native-catalog/'
CATALOG = '/usr/share/toddy/voice/catalog.json'
DOCUMENTS = frozenset(('qualification.json', 'process-qualified.json',
    'process-retry-validation.json', 'whisper-cpp-qualified.json',
    'espeak-ng-qualified.json', 'toddy-voice-model-base-qualified.json',
    'human-sample-attribution.json', 'human-samples.md', 'MIT', 'CC-BY-4.0',
    'copyright', 'source-notices/index.json'))


def verify_owned(record, expected, target):
    """Owned metadata bytes only; private native audits are independently required."""
    allowed = {CATALOG} | {DOC + name for name in DOCUMENTS}
    entries = record['payload']
    regulars = {path for path, row in entries.items() if 'sha256' in row}
    if regulars != allowed:
        raise ValueError('Exact generated catalog metadata closure required')
    parents = {str(parent) for name in allowed for parent in Path(name).parents}
    for path, row in entries.items():
        if path not in allowed and (path not in parents or row.get('directory') is not True):
            raise ValueError('Generated catalog cannot own code/model/foreign data')
    for path in allowed:
        actual = target / path.lstrip('/')
        bridge.frozen.regular(actual)
        if bridge.digest(actual) != entries[path]['sha256']:
            raise ValueError('Owned generated catalog bytes changed')
    for path, source in expected.items():
        if path not in allowed or bridge.digest(source) != entries[path]['sha256']:
            raise ValueError('Owned catalog proof differs from retained actual evidence')


def export_attestation(component, record):
    """Produce only after actual builder validators pass; never source-fixture proof."""
    verify_catalog_provenance(component, record, repository=bridge.R, target=bridge.T)
    catalog = bridge.read(bridge.file('catalog.json'))
    installed = bridge.read(bridge.file('catalog-package-installed.json'))
    return {'version': 1, 'kind': 'native-voice-catalog-source-export-v1',
        'component': component, 'producer_pins': bridge.producer_pins(),
        'native_transport': bridge.context()[0]['bindings']['pipewire-transport'],
        'owned_files': {name: row['sha256'] for name, row in record['payload'].items() if 'sha256' in row},
        'catalog_write_audit_sha256': catalog['native_write_audit_sha256'],
        'catalog_package_write_audit_sha256': installed['native_write_audit_sha256'],
        'native_package_check_sha256': bridge.digest(bridge.file('catalog-package-checked.json')),
        'scope': 'Actual builder audit-validated data/source export; no GUI/PTT/device/release acceptance'}


def verify_catalog_provenance(component, record, *, repository, target):
    # This verifier needs the designated builder's retained native evidence.
    # An extracted archive or a self-declared qualification.json cannot qualify it.
    if Path(repository).resolve() != bridge.R or Path(target).resolve() != bridge.T:
        raise ValueError('Generated catalog requires actual designated-builder evidence')
    if (component['name'], component['version'], component['architecture']) != (bridge.PACKAGE, bridge.VERSION, 'all'):
        raise ValueError('Exact generated catalog identity required')
    files = record['supporting_build_scripts']['files']
    pins = bridge.producer_pins()
    expected_scripts = {'phase2/voice_process_reconcile.py': pins['producer'],
        'phase2/voice_native.py': pins['frozen_driver'], 'phase2/job.py': pins['job'],
        'phase2/isolated.sh': pins['harness'],
        'phase2/voice_reconcile_install.sh': pins['install_recipe']}
    if record['recipe_sha256'] != pins['install_recipe'] or any(files.get(name) != sha for name, sha in expected_scripts.items()):
        raise ValueError('Exact generated catalog producer/recipe custody required')
    receipt = bridge.checked_catalog()  # actual native2 install + process + catalog audit
    path, actual = bridge.frozen.native_record(bridge.PACKAGE)
    if actual != record or bridge.digest(path) != component['component_record_sha256']:
        raise ValueError('Actual installed generated catalog record differs')
    installed = bridge.read(bridge.file('catalog-package-installed.json'))
    inputs = {'producer_pins': pins,
        'catalog_receipt_sha256': bridge.digest(bridge.file('catalog.json')),
        'catalog_sha256': receipt['catalog_sha256']}
    audit = bridge.frozen.require_write_audit(bridge.PREFIX, 'catalog-package',
        inputs=inputs, record_sha256=bridge.digest(path))
    if installed != {'record_sha256': bridge.digest(path), 'archive_sha256': record['archive_sha256'],
            'native_write_audit_sha256': audit, 'audit_inputs': inputs, 'producer_pins': pins}:
        raise ValueError('Actual controlled generated catalog installation required')
    checked = bridge.read(bridge.file('catalog-package-checked.json'))
    if checked != {'record_sha256': bridge.digest(path), 'catalog_sha256': receipt['catalog_sha256'],
            'install_audit_sha256': audit,
            'scope': 'Owned optional catalog/process component proof only; GUI/PTT/device/physical evidence still separate'}:
        raise ValueError('Actual independent native catalog package check required')
    expected = {CATALOG: bridge.T / CATALOG.lstrip('/'),
        DOC + 'qualification.json': bridge.file('catalog.json'),
        DOC + 'process-qualified.json': bridge.WORK / 'process-qualified.json',
        DOC + 'process-retry-validation.json': bridge.file('process-validated.json')}
    for name in bridge.frozen.COMPONENTS:
        _, _, prefix, _ = bridge.frozen.prepared(name, bridge.GENERATION)
        expected[DOC + name + '-qualified.json'] = Path(str(prefix) + '.qualified.json')
    for relative, name in (('tests/fixtures/voice/human/manifest.json', 'human-sample-attribution.json'),
            ('tests/fixtures/voice/human/README.md', 'human-samples.md'),
            ('LICENSE', 'MIT'), ('LICENSES/CC-BY-4.0.txt', 'CC-BY-4.0')):
        expected[DOC + name] = bridge.R / relative
    verify_owned(record, expected, bridge.T)
    return 'owned-audited-native-voice-catalog-v1'
