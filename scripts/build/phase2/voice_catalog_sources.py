"""Public data/source verification for the exact native2 generated voice catalog.

This does not rerun private native audits or grant runtime permission. The actual
builder export attestation, archive-export input pins and owner-reviewed signed
source metadata retain that trust boundary explicitly.
"""
import hashlib
from pathlib import Path
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent)]
import offline_payload as p
from voice_catalog_provenance import CATALOG, DOC, DOCUMENTS
import voice_process_reconcile as bridge

PRODUCER = '418b933c884acb32f754f86ab008dec3924afeeb3f9924b296fe344786d20322'
RECIPE = '0ab6bbe4a9b890a28e6a69d2c56729349950b6b3685d419e0c056194998cf4d2'
COMPONENT_KEYS = ('name','version','architecture','depends','archive_sha256',
    'component_record_sha256','recipe_sha256','sources','copyright','source_notices_index')
SCRIPT_ROLES = {'producer':'phase2/voice_process_reconcile.py',
    'frozen_driver':'phase2/voice_native.py','job':'phase2/job.py',
    'harness':'phase2/isolated.sh','install_recipe':'phase2/voice_reconcile_install.sh'}


def identity(component):
    if (component.get('name'), component.get('version'), component.get('architecture'),
            component.get('recipe_sha256'), component.get('sources')) != (bridge.PACKAGE, bridge.VERSION, 'all', RECIPE, []):
        raise ValueError('Exact generated catalog source identity/recipe required')


def owned_files(body):
    allowed = {CATALOG} | {DOC+name for name in DOCUMENTS}
    if {name for name,row in body.items() if 'sha256' in row} != allowed:
        raise ValueError('Exact generated data-only source closure required')
    parents = {str(parent) for name in allowed for parent in Path(name).parents}
    for name,row in body.items():
        if name in allowed:
            if type(row.get('mode')) is not int or row['mode'] & 0o111 or row.get('symlink') is not None:
                raise ValueError('Generated source cannot contain executable/link data')
        elif name not in parents or row.get('directory') is not True:
            raise ValueError('Generated source cannot contain foreign payload')
    return {name:body[name]['sha256'] for name in allowed}


def verify(component, record, documents, attestation, projection):
    identity(component)
    if record.get('source_kind') != 'book-derived-versioned-recipe' or record.get('sources') != [] or record.get('recipe_sha256') != RECIPE:
        raise ValueError('Exact generated original source record required')
    expected_component = {name:component[name] for name in COMPONENT_KEYS}
    if (attestation.get('version') != 1 or type(attestation.get('version')) is not int or
            attestation.get('kind') != 'native-voice-catalog-source-export-v1' or
            attestation.get('component') != expected_component):
        raise ValueError('Actual export attestation/package pins differ')
    files = owned_files(record['payload'])
    if attestation.get('owned_files') != files:
        raise ValueError('Actual export attestation/owned bytes differ')
    expected_documents = DOCUMENTS | {'catalog.json'}
    if set(documents) != expected_documents:
        raise ValueError('Every owned generated proof/license/source byte required')
    for name,data in documents.items():
        path = CATALOG if name == 'catalog.json' else DOC+name
        if hashlib.sha256(data).hexdigest() != files[path]:
            raise ValueError('Generated document byte custody differs')
    if projection.get('schema_version') != 1 or projection.get('offline_base') is not False or projection.get('iso_inclusion') is not False or projection.get('available') is not False or expected_component not in projection.get('components',[]):
        raise ValueError('Actual optional projection/catalog binding required')
    pins = attestation.get('producer_pins',{})
    if set(pins) != set(SCRIPT_ROLES) or any(not isinstance(sha,str) or not p.HASH.fullmatch(sha) for sha in pins.values()) or pins['producer'] != PRODUCER or pins['install_recipe'] != RECIPE or pins['frozen_driver'] != bridge.FROZEN_DRIVER:
        raise ValueError('Exact known generated source producer required')
    fileset = record.get('supporting_build_scripts',{}).get('files',{})
    if any(fileset.get(name) != pins[role] for role,name in SCRIPT_ROLES.items()):
        raise ValueError('Generated producer outside actual recipe closure')
    qualification=p.strict(documents['qualification.json'])
    process=p.strict(documents['process-qualified.json'])
    retry=p.strict(documents['process-retry-validation.json'])
    catalog=p.strict(documents['catalog.json'])
    if qualification.get('kind') != 'reconciled-native-voice-catalog-v1' or qualification.get('producer_pins') != pins or retry.get('producer_pins') != pins or retry.get('kind') != 'actual-native2-process-retry-v1' or retry.get('records') != qualification.get('records'):
        raise ValueError('Generated actual native2 proof identities differ')
    records=qualification.get('records',{})
    if set(records) != {'pipewire','wireplumber','toddy-voice','whisper-cpp','espeak-ng','toddy-voice-model-base','pipewire-audio-tools'} or any(not isinstance(sha,str) or not p.HASH.fullmatch(sha) for sha in records.values()):
        raise ValueError('Exact actual native component record pins required')
    transport=attestation.get('native_transport',{})
    if (set(transport)!={'failed_revision2_sha256','failed_revision2_archive_sha256','restore','tools','restore_receipt_sha256','tools_receipt_sha256','record_sha256','base_record_sha256'} or
            transport['failed_revision2_archive_sha256']!=bridge.FAILED_PIPEWIRE_ARCHIVE or transport['base_record_sha256']!=bridge.OLD_PIPEWIRE_RECORD or records['pipewire']!=transport['base_record_sha256'] or records['pipewire-audio-tools']!=transport['record_sha256']):
        raise ValueError('Exact failed upgrade/restored base/separate tools source bindings required')
    for key in ('restore','tools'):
        row=transport[key]
        if not isinstance(row,dict) or set(row)!={'success_sha256','manifest_sha256'} or any(not isinstance(sha,str) or not p.HASH.fullmatch(sha) for sha in row.values()):raise ValueError('Actual separate transport write audit source bindings required')
    if any(not isinstance(transport[key],str) or not p.HASH.fullmatch(transport[key]) for key in ('failed_revision2_sha256','restore_receipt_sha256','tools_receipt_sha256','record_sha256')):raise ValueError('Actual separate transport receipt source hashes required')
    old=qualification.get('old_failed_process',{})
    if old != retry.get('old_failed_process') or set(old) != {'exit_sha256','marker_sha256','log_sha256'} or any(not isinstance(sha,str) or not p.HASH.fullmatch(sha) for sha in old.values()):
        raise ValueError('Retained original actual failed process pins required')
    hashes={name:hashlib.sha256(data).hexdigest() for name,data in documents.items()}
    if qualification.get('catalog_sha256') != hashes['catalog.json'] or qualification.get('process_evidence_sha256') != hashes['process-qualified.json'] or qualification.get('process_validation_sha256') != hashes['process-retry-validation.json'] or retry.get('process_sha256') != hashes['process-qualified.json']:
        raise ValueError('Generated catalog/process proof bindings differ')
    for name in ('catalog_write_audit_sha256','catalog_package_write_audit_sha256','native_package_check_sha256'):
        if not isinstance(attestation.get(name),str) or not p.HASH.fullmatch(attestation[name]):
            raise ValueError('Retained actual builder audit/check digests required')
    if qualification.get('native_write_audit_sha256') != attestation['catalog_write_audit_sha256'] or projection.get('native_catalog_package_check_sha256') != attestation['native_package_check_sha256']:
        raise ValueError('Actual builder catalog audit/check bindings differ')
    if catalog.get('voice_catalog_version') != 1 or catalog.get('status') != 'native-qualified' or catalog.get('process_control',{}).get('evidence_sha256') != hashes['process-qualified.json']:
        raise ValueError('Generated native catalog data binding differs')
    dependencies=catalog.get('native_dependencies',{})
    if set(dependencies) != {'pipewire','wireplumber','whisper-cpp','espeak-ng'} or any(row.get('component_record_sha256') != records[name] for name,row in dependencies.items()):
        raise ValueError('Native catalog/component record bindings differ')
    runtime=process.get('files',{})
    if set(runtime) != {'process.py','child.py','artifacts.py','session.py'} or any(not isinstance(sha,str) or not p.HASH.fullmatch(sha) for sha in runtime.values()):
        raise ValueError('Generated process source hashes missing')
    artifacts=catalog.get('artifacts',{});control=catalog['process_control']
    transport={role:artifacts.get(role,{}).get('sha256') for role in ('capture','playback','device-list')}
    transport['pw-cat']=control.get('pw_cat_sha256')
    if control.get('runner_sha256') != runtime['process.py'] or control.get('launcher_sha256') != runtime['child.py']:
        raise ValueError('Generated process/catalog runtime binding differs')
    bridge.validate_process(process,runtime_files=runtime,transport_files=transport)
    for name,(_,version,_,_) in bridge.frozen.COMPONENTS.items():
        engine=p.strict(documents[name+'-qualified.json'])
        if engine.get('component') != name or engine.get('version') != version or not engine.get('legal_documents'):
            raise ValueError('Generated component/license proof identity differs')
    if documents['copyright'] != documents['MIT']+b'\nQualification documentation:\n'+documents['CC-BY-4.0']:
        raise ValueError('Exact generated source MIT/documentation license required')
    # The actual source exporter separately checks projection/attestation file
    # digests against export_receipt.inputs before calling this pure verifier.
    return {'LICENSE':hashes['MIT'], 'LICENSES/CC-BY-4.0.txt':hashes['CC-BY-4.0'],
        'tests/fixtures/voice/human/manifest.json':hashes['human-sample-attribution.json'],
        'tests/fixtures/voice/human/README.md':hashes['human-samples.md']}
