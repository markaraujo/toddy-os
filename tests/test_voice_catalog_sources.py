"""Pure generated data fixtures; no native execution or audit acceptance."""
import copy
import hashlib
import importlib.util
import json
import subprocess
import tempfile
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('voice_catalog_sources_fixture',ROOT/'scripts/build/phase2/voice_catalog_sources.py')
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)

def sha(data):return hashlib.sha256(data).hexdigest()
def encoded(value):return json.dumps(value,sort_keys=True).encode()

def fixture():
    pins={role:'a'*64 for role in v.SCRIPT_ROLES};pins.update(producer=v.PRODUCER,install_recipe=v.RECIPE,frozen_driver=v.bridge.FROZEN_DRIVER)
    files={name:'b'*64 for name in ('process.py','child.py','artifacts.py','session.py')}
    transport={role:'c'*64 for role in ('capture','playback','device-list','pw-cat')}
    process={'tests_run':4,'errors':0,'failures':0,'skipped':0,'files':files,
        'file_sessions':{locale:{'transcript':'UNQUALIFIED SOURCE FIXTURE','word_error_rate':0} for locale in ('en','pt-BR')},
        'native_engine_stop':{'code':'canceled'},'transport':{role:{'sha256':digest} for role,digest in transport.items()}}
    docs={name:b'UNQUALIFIED SOURCE FIXTURE' for name in v.DOCUMENTS}
    records={name:'a'*64 for name in ('pipewire','wireplumber','toddy-voice','whisper-cpp','espeak-ng','toddy-voice-model-base','pipewire-audio-tools')}
    records['pipewire']=v.bridge.OLD_PIPEWIRE_RECORD
    old={name:'b'*64 for name in ('exit_sha256','marker_sha256','log_sha256')}
    docs['process-qualified.json']=encoded(process)
    docs['process-retry-validation.json']=encoded({'kind':'actual-native2-process-retry-v1','producer_pins':pins,'records':records,'old_failed_process':old,'process_sha256':sha(docs['process-qualified.json'])})
    docs['catalog.json']=encoded({'voice_catalog_version':1,'status':'native-qualified','native_dependencies':{name:{'component_record_sha256':records[name]} for name in ('pipewire','wireplumber','whisper-cpp','espeak-ng')},
        'process_control':{'evidence_sha256':sha(docs['process-qualified.json']),'runner_sha256':files['process.py'],'launcher_sha256':files['child.py'],'pw_cat_sha256':transport['pw-cat']},
        'artifacts':{role:{'sha256':transport[role]} for role in ('capture','playback','device-list')}})
    docs['qualification.json']=encoded({'kind':'reconciled-native-voice-catalog-v1','producer_pins':pins,'records':records,'old_failed_process':old,'native_write_audit_sha256':'d'*64,'catalog_sha256':sha(docs['catalog.json']),'process_evidence_sha256':sha(docs['process-qualified.json']),'process_validation_sha256':sha(docs['process-retry-validation.json'])})
    for name,(_,version,_,_) in v.bridge.frozen.COMPONENTS.items():docs[name+'-qualified.json']=encoded({'component':name,'version':version,'legal_documents':{'NOTICE':'a'*64}})
    docs['copyright']=docs['MIT']+b'\nQualification documentation:\n'+docs['CC-BY-4.0']
    payload={(v.CATALOG if name=='catalog.json' else v.DOC+name):{'sha256':sha(data),'mode':0o100644} for name,data in docs.items()}
    component=dict(name=v.bridge.PACKAGE,version=v.bridge.VERSION,architecture='all',depends='',archive_sha256='e'*64,component_record_sha256='f'*64,recipe_sha256=v.RECIPE,sources=[],copyright={},source_notices_index={})
    record={'source_kind':'book-derived-versioned-recipe','sources':[],'recipe_sha256':v.RECIPE,'payload':payload,'supporting_build_scripts':{'files':{name:pins[role] for role,name in v.SCRIPT_ROLES.items()}}}
    attestation={'version':1,'kind':'native-voice-catalog-source-export-v1','component':component,'producer_pins':pins,'owned_files':{path:row['sha256'] for path,row in payload.items()},'catalog_write_audit_sha256':'d'*64,'catalog_package_write_audit_sha256':'a'*64,'native_package_check_sha256':'b'*64}
    attestation['native_transport']={'failed_revision2_sha256':'a'*64,'failed_revision2_archive_sha256':v.bridge.FAILED_PIPEWIRE_ARCHIVE,'restore':{'success_sha256':'b'*64,'manifest_sha256':'c'*64},'tools':{'success_sha256':'d'*64,'manifest_sha256':'e'*64},'restore_receipt_sha256':'a'*64,'tools_receipt_sha256':'b'*64,'record_sha256':records['pipewire-audio-tools'],'base_record_sha256':records['pipewire']}
    projection={'schema_version':1,'offline_base':False,'iso_inclusion':False,'available':False,'components':[component],'native_catalog_package_check_sha256':'b'*64}
    return component,record,docs,attestation,projection


class GeneratedSourcesTests(unittest.TestCase):
    def test_exact_reviewed_unexecuted_reconciliation_source_pin(self):
        self.assertEqual(sha((ROOT/'scripts/build/phase2/voice_process_reconcile.py').read_bytes()),v.PRODUCER)

    def test_public_data_check_has_no_private_builder_path_bypass(self):
        values=fixture();inputs=v.verify(*values)
        self.assertEqual(set(inputs),{'LICENSE','LICENSES/CC-BY-4.0.txt','tests/fixtures/voice/human/manifest.json','tests/fixtures/voice/human/README.md'})
        # This pure fixture pass is solely a source-byte consistency check.
        # It cannot construct or satisfy actual builder native audit validators.
        self.assertFalse(hasattr(v,'native_write_audit'))

    def test_other_identity_executable_foreign_or_missing_data_rejected(self):
        for case in ('identity','recipe','executable','link','extra','missing'):
            values=copy.deepcopy(fixture());component,record,docs,attestation,projection=values
            if case=='identity':component['name']='other'
            elif case=='recipe':component['recipe_sha256']='a'*64
            elif case=='executable':record['payload'][v.CATALOG]['mode']=0o100755
            elif case=='link':record['payload'][v.CATALOG]['symlink']='/private'
            elif case=='extra':record['payload']['/usr/bin/engine']={'sha256':'a'*64,'mode':0o100755}
            else:del docs['process-qualified.json']
            with self.subTest(case=case),self.assertRaises(ValueError):v.verify(*values)

    def test_real_tiny_deb_keeps_every_owned_generated_document_as_source(self):
        spec=importlib.util.spec_from_file_location('generated_package_sources_fixture',ROOT/'scripts/build/phase2/package_sources.py')
        source=importlib.util.module_from_spec(spec);spec.loader.exec_module(source)
        component,record,docs,attestation,projection=fixture()
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);stage=root/'stage';control=stage/'DEBIAN';control.mkdir(parents=True)
            (control/'control').write_text('Package: '+v.bridge.PACKAGE+'\nVersion: '+v.bridge.VERSION+'\nArchitecture: all\nMaintainer: Unqualified source fixture <fixture@example.invalid>\nDescription: Source data fixture only\n')
            for name,data in docs.items():
                path=stage/(v.CATALOG if name=='catalog.json' else v.DOC+name).lstrip('/')
                path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
            archive=root/'fixture.deb'
            subprocess.run(['dpkg-deb','--build','--root-owner-group',str(stage),str(archive)],check=True,stdout=subprocess.DEVNULL)
            _,body,_=source.p.archive_contents(archive)
            self.assertEqual(source.package_documents(archive,v.bridge.PACKAGE,body),docs)
            v.owned_files(body)
            receipt={'packages':[{'name':v.bridge.PACKAGE}]}
            with self.assertRaisesRegex(ValueError,'explicit builder'):
                source.collect(root,receipt,root,None,None,None)
            att=root/'attestation.json';att.write_bytes(encoded(attestation))
            proj=root/'projection.json';proj.write_bytes(encoded(projection))
            with self.assertRaisesRegex(ValueError,'digest chain'):
                source.collect(root,receipt,root,None,None,None,att,proj)

    def test_attestation_owned_hash_producer_audit_and_process_bindings_required(self):
        for case in ('owned','producer','audit','check','process','license','available'):
            values=copy.deepcopy(fixture());component,record,docs,attestation,projection=values
            if case=='owned':attestation['owned_files'][v.CATALOG]='a'*64
            elif case=='producer':attestation['producer_pins']['producer']='a'*64
            elif case=='audit':attestation['catalog_write_audit_sha256']='a'*64
            elif case=='check':projection['native_catalog_package_check_sha256']='c'*64
            elif case=='process':docs['process-qualified.json']=b'{}'
            elif case=='license':docs['MIT']=b'different license'
            else:projection['available']=True
            with self.subTest(case=case),self.assertRaises(ValueError):v.verify(*values)


if __name__=='__main__':unittest.main()
