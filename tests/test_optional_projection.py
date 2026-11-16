"""Source custody fixtures only; never native component or acquisition acceptance."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts/build/phase2' / (name + '.py'))
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module
p = load('optional_projection')
c = load('voice_catalog_provenance')


class OptionalTests(unittest.TestCase):
    def test_exact_set_no_offline_or_available_claim(self):
        rows = {name: {'name': name} for name in p.NAMES}
        value = p.document(rows, 'SOURCE FIXTURE')
        self.assertEqual(len(value['components']), 6)
        self.assertFalse(value['offline_base']); self.assertFalse(value['iso_inclusion'])
        self.assertFalse(value['available']); self.assertTrue(value['explicit_owner_acquisition_required'])
        for changed in (dict(rows, arbitrary={'name':'arbitrary'}), {name:row for name,row in rows.items() if name!='toddy-voice'}):
            with self.assertRaisesRegex(ValueError,'Exact six'): p.document(changed, '')

    def test_generated_catalog_cannot_qualify_from_portable_or_self_declared_data(self):
        with self.assertRaisesRegex(ValueError, 'designated-builder evidence'):
            c.verify_catalog_provenance({}, {}, repository=ROOT, target=Path('/tmp/source-fixture'))
        with patch.object(c.bridge, 'producer_pins', side_effect=AssertionError('Do not inspect before identity')):
            with self.assertRaisesRegex(ValueError, 'identity'):
                c.verify_catalog_provenance({'name':'unreviewed','version':c.bridge.VERSION,'architecture':'all'}, {}, repository=c.bridge.R, target=c.bridge.T)

    def test_export_attestation_requires_actual_builder_audit_validator_first(self):
        with patch.object(c, 'verify_catalog_provenance', side_effect=ValueError('Actual proof missing')) as verify:
            with self.assertRaisesRegex(ValueError, 'Actual proof missing'):
                c.export_attestation({}, {})
            verify.assert_called_once_with({}, {}, repository=c.bridge.R, target=c.bridge.T)

    def test_owned_generated_proofs_must_equal_retained_bytes_and_exclude_code(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); payload={}; expected={}
            for name in {c.CATALOG} | {c.DOC+name for name in c.DOCUMENTS}:
                path=root/name.lstrip('/');path.parent.mkdir(parents=True,exist_ok=True)
                path.write_text('UNQUALIFIED SOURCE FIXTURE '+name)
                payload[name]={'sha256':c.bridge.digest(path)}; expected[name]=path
            record={'payload':payload}
            # Fixture paths are intentionally not root-custody native proof.
            # Only bypass path ownership to exercise this pure byte/closure check.
            with patch.object(c.bridge.frozen, 'regular'):
                c.verify_owned(record,expected,root)
                changed=copy.deepcopy(record); changed['payload']['/usr/bin/foreign']={'sha256':'a'*64}
                with self.assertRaisesRegex(ValueError,'closure'):c.verify_owned(changed,expected,root)
                changed=copy.deepcopy(record);changed['payload']['/usr/bin']={'symlink':'unsafe'}
                with self.assertRaisesRegex(ValueError,'cannot own'):c.verify_owned(changed,expected,root)
                receipt=root/'retained.json';receipt.write_text('DIFFERENT UNQUALIFIED FIXTURE')
                wrong=dict(expected);wrong[c.DOC+'qualification.json']=receipt
                with self.assertRaisesRegex(ValueError,'retained actual'):c.verify_owned(record,wrong,root)
                (root/c.CATALOG.lstrip('/')).write_text('tampered')
                with self.assertRaisesRegex(ValueError,'bytes changed'):c.verify_owned(record,expected,root)

    def test_two_original_packages_retain_owned_manifest_and_recipe_rules(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); evidence=root/'repo/docs/evidence'; evidence.mkdir(parents=True)
            for name in ('B02-desktop-runtime-manifest.json','H11-components.json'):
                (evidence/name).write_text('{"components":[]}')
            files={'recipe.py':'a'*64,'packager.py':'b'*64}
            import hashlib
            closure=hashlib.sha256(json.dumps(files,sort_keys=True,separators=(',',':')).encode()).hexdigest()
            for name in ('toddy-voice','toddy-integrations'):
                virtual='/usr/share/doc/'+name+'/source-manifest.json'
                manifest=root/'target'/virtual.lstrip('/');manifest.parent.mkdir(parents=True)
                manifest.write_text(json.dumps({'package':name,'source_inputs':{'runtime/data.py':'c'*64}}))
                component={'name':name,'component_record_sha256':'d'*64,'recipe_sha256':'a'*64}
                record={'source_kind':'book-derived-versioned-recipe','packager_sha256':'b'*64,
                    'supporting_build_scripts':{'files':files,'sha256':closure},'payload':{virtual:{'sha256':p.projection.payload.digest(manifest)}}}
                self.assertEqual(p.projection.original_source_provenance(component,record,repository=root/'repo',target=root/'target'),'owned-original-source-manifest')
                manifest.write_text('{}')
                with self.assertRaisesRegex(ValueError,'ownership differs'):
                    p.projection.original_source_provenance(component,record,repository=root/'repo',target=root/'target')


if __name__=='__main__':unittest.main()
