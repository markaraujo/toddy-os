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
