"""Current closure generation fixtures; no native VM/image execution."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[1]/'scripts/build/phase2/image_projection.py'
spec = importlib.util.spec_from_file_location('image_projection', SOURCE)
p = importlib.util.module_from_spec(spec); spec.loader.exec_module(p)


def fixture():
    profile = {'retained_foundation_packages':['base'], 'desktop_roots':['desktop'],
        'excluded_product_roots':['toddy-assistant','qtbase','toddy-agent']}
    names = {'base','desktop','support','qtbase'} | p.ADDITIONS | p.LIVE
    rows = {n:dict(name=n,version='1',architecture='amd64',depends='',pre_depends='') for n in names}
    rows['desktop']['depends']='support (>= 1)'
    rows['toddy-installer']['depends']='qtbase (= 1), calamares'
    raw=''.join('\t'.join([n,'1','amd64','install ok installed',r['depends'],''])+'\n' for n,r in sorted(rows.items()))
    return profile, rows, raw


class ProjectionTests(unittest.TestCase):
    def test_split_uses_actual_versioned_closure_and_mandatory_additions(self):
        profile, rows, raw=fixture()
        base,live=p.select(profile,rows)
        self.assertTrue(p.ADDITIONS <= base)
        self.assertNotIn('qtbase',base)
        self.assertIn('qtbase',live)
        documents=p.documents(json.dumps(profile).encode(),raw,{n:rows[n] for n in live})
        projection=json.loads(documents['projection.json'])
        self.assertFalse(p.ADDITIONS & {x['name'] for x in projection['components']})
        self.assertEqual(len(json.loads(documents['additional-components.json'])),2)
        live_profile=json.loads(documents['live-profile.json'])
        self.assertNotIn('qtbase',live_profile['excluded_product_roots'])
        self.assertFalse(json.loads(documents['split.json'])['configured_image'])

    def test_acquired_dependency_fails_instead_of_silent_filter(self):
        profile,rows,_=fixture()
        rows['toddy-agent']=dict(name='toddy-agent',version='1',architecture='all',depends='')
        rows['desktop']['depends']='toddy-agent'
        with self.assertRaisesRegex(ValueError,'leaked'):
            p.select(profile,rows)

    def test_mvp_is_explicit_archive_closure_and_live_policy_remains_consistent(self):
        profile, rows, _ = fixture()
        roots = p.payload.MVP_ROOTS
        profile.update(delivery_class=p.payload.MVP_CLASS, g2_eligible=False,
            automatic_activation=False, desktop_roots=['desktop', *sorted(roots)],
            excluded_product_roots=['toddy-assistant', 'qtbase'])
        for name in roots:
            rows[name] = dict(name=name, version='1', architecture='amd64', depends='', pre_depends='')
        base, live = p.select(profile, rows)
        self.assertTrue(roots <= base)
        raw = ''.join('\t'.join([n, '1', 'amd64', 'install ok installed', r['depends'], ''])+'\n'
            for n, r in sorted(rows.items()))
        docs = p.documents(json.dumps(profile).encode(), raw, {n: rows[n] for n in live})
        live_profile = json.loads(docs['live-profile.json'])
        self.assertEqual(p.payload.delivery_policy(live_profile)[0], p.payload.MVP_CLASS)
        self.assertFalse(json.loads(docs['projection.json'])['g2_eligible'])
        self.assertFalse(roots & set(live_profile['excluded_product_roots']))
        profile['g2_eligible'] = True
        with self.assertRaises(p.payload.PayloadError): p.select(profile, rows)

    def test_version_mismatch_and_missing_live_root_fail(self):
        profile,rows,_=fixture()
        rows['desktop']['depends']='support (>> 2)'
        with self.assertRaises(p.payload.PayloadError):p.select(profile,rows)
        rows['desktop']['depends']=''; del rows['toddy-installer']
        with self.assertRaises(p.payload.PayloadError):p.select(profile,rows)

    def test_inventory_rejects_partial_duplicate_and_wrong_architecture(self):
        _,_,raw=fixture()
        self.assertTrue(p.installed_rows(raw))
        for value in (raw+raw, raw.replace('install ok installed','install ok unpacked'),
                      raw.replace('amd64','arm64'), 'bad\n'):
            with self.assertRaises(ValueError):p.installed_rows(value)

    def test_archive_control_dependency_is_not_replaced_by_inventory(self):
        _,rows,_=fixture()
        with patch.object(p.payload,'component_from_record',return_value={'depends':'different'}):
            with self.assertRaisesRegex(ValueError,'dependencies differ'):
                p.collect({'base'},rows)

    def test_empty_sources_require_exact_historical_original_record(self):
        with tempfile.TemporaryDirectory() as directory:
            repository=Path(directory); evidence=repository/'docs/evidence';evidence.mkdir(parents=True)
            component={'name':'toddy-base-config','component_record_sha256':'a'*64}
            approved={'name':'toddy-base-config','component_record_sha256':'a'*64,'sources':[]}
            for name in ('B02-desktop-runtime-manifest.json','H11-components.json'):
                (evidence/name).write_text(json.dumps({'components':[approved]}))
            record={'source_kind':'book-derived-versioned-recipe'}
            self.assertEqual(p.original_source_provenance(component,record,repository=repository),'committed-original-record')
            with self.assertRaisesRegex(ValueError,'Foreign package'):
                p.original_source_provenance(component,{'source_kind':'upstream-archives-and-versioned-recipe'},repository=repository)
            component['component_record_sha256']='b'*64
            with self.assertRaisesRegex(ValueError,'Unreviewed original'):
                p.original_source_provenance(component,record,repository=repository)

    def test_new_original_needs_owned_manifest_and_complete_recipe_binding(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);repository=root/'repo';target=root/'target'
            evidence=repository/'docs/evidence';evidence.mkdir(parents=True)
            for name in ('B02-desktop-runtime-manifest.json','H11-components.json'):
                (evidence/name).write_text('{"components":[]}')
            virtual='/usr/share/doc/toddy-assistant/source-manifest.json'
            manifest=target/virtual.lstrip('/');manifest.parent.mkdir(parents=True)
            manifest.write_text(json.dumps({'package':'toddy-assistant','source_inputs':{'runtime/ui/app.py':'c'*64}}))
            files={'recipe.py':'a'*64,'stage_package.py':'b'*64}
            component={'name':'toddy-assistant','component_record_sha256':'d'*64,'recipe_sha256':'a'*64}
            record={'source_kind':'book-derived-versioned-recipe','packager_sha256':'b'*64,
                'supporting_build_scripts':{'files':files,'sha256':p.hashlib.sha256(json.dumps(files,sort_keys=True,separators=(',',':')).encode()).hexdigest()},
                'payload':{virtual:{'sha256':p.payload.digest(manifest)}}}
            self.assertEqual(p.original_source_provenance(component,record,repository=repository,target=target),'owned-original-source-manifest')
            # Exact new defaults identity follows the same strict original-source
            # manifest path/hash/recipe checks; foreign package policy is unchanged.
            defaults_virtual='/usr/share/doc/toddy-desktop-defaults/source-manifest.json'
            defaults_manifest=target/defaults_virtual.lstrip('/');defaults_manifest.parent.mkdir(parents=True)
            defaults_manifest.write_text(json.dumps({'package':'toddy-desktop-defaults','source_inputs':{'scripts/build/phase2/desktop_background_upgrade.py':'c'*64}}))
            component['name']='toddy-desktop-defaults';record['payload']={defaults_virtual:{'sha256':p.payload.digest(defaults_manifest)}}
            self.assertEqual(p.original_source_provenance(component,record,repository=repository,target=target),'owned-original-source-manifest')
            record['supporting_build_scripts']['sha256']='f'*64
            with self.assertRaisesRegex(ValueError,'closure integrity'):
                p.original_source_provenance(component,record,repository=repository,target=target)

    def test_generation_is_private_durable_hash_bound_and_never_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory)/'new'
            p.save_generation(output,{'projection.json':b'{"fixture":true}'})
            complete=json.loads((output/'complete.json').read_bytes())
            self.assertEqual(complete['files']['projection.json'],p.payload.digest(output/'projection.json'))
            self.assertEqual(output.stat().st_mode&0o777,0o700)
            self.assertEqual((output/'projection.json').stat().st_mode&0o777,0o600)
            with self.assertRaises(FileExistsError):p.save_generation(output,{})


if __name__=='__main__':unittest.main()
