"""Unqualified source fixtures only; no actual release/native/signature evidence."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('package_release_fixture',ROOT/'scripts/package_release.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)


class PackageReleaseTests(unittest.TestCase):
    def rows(self):
        names=['Packages','Packages.gz','Release','InRelease','Release.gpg','archive-keyring.gpg','native-trust.json','archive-export.json','source.tar.gz','project.tar.gz','inventory.json','LICENSES.txt','TESTING.md','SHA256SUMS']
        roles=['repository']*8+['source','project-source','inventory','licenses','guide','checksums']
        return [{'role':role,'name':name,'sha256':'a'*64,'bytes':1,'url':r.common.BASE+'download/v0.2.0-preview.1/'+name} for role,name in zip(roles,names)]
    def value(self):
        return {'version':1,'state':'public-package-assets-verified','tag':'v0.2.0-preview.1','source_commit':'b'*40,'release_url':r.common.BASE+'tag/v0.2.0-preview.1','scope':'experimental-native-package-artifacts','limitations':dict(r.PENDING),'artifacts':self.rows(),'repository_pins':{'archive_export_sha256':'a'*64,'inrelease_sha256':'a'*64,'public_keyring_sha256':'a'*64,'public_fingerprint':'B'*40,'packages':[{'name':'unqualified-source-fixture','version':'1','architecture':'all','archive_sha256':'a'*64,'component_record_sha256':'b'*64,'recipe_sha256':'c'*64}]},'source_review':{'path':'docs/evidence/fixture-review.json','sha256':'c'*64},'github_evidence':{'path':'docs/evidence/fixture-github.json','sha256':'d'*64},'pages_handoff':'pending-deployment-verification'}
    def test_absent_metadata_keeps_foundation_and_final_iso_portal_exact(self):
        with tempfile.TemporaryDirectory() as directory:
            template=(ROOT/'dashboard/template.html').read_text()
            self.assertEqual(r.portal(Path(directory),template),template)
        self.assertFalse((ROOT/r.PUBLIC).exists())
    def test_exact_scope_never_awards_iso_g2_or_ready_acquisition(self):
        value=self.value();r.validate(value)
        for field,bad in [('iso','available'),('g2','passed'),('native_acquisition','native-full-flow')]:
            changed=copy.deepcopy(value);changed['limitations'][field]=bad
            with self.assertRaises(ValueError):r.validate(changed)
    def test_media_missing_sources_and_unsafe_asset_urls_are_refused(self):
        for change in ('media','source','url','duplicate'):
            rows=self.rows()
            if change=='media':rows[0]['name']='system.iso';rows[0]['url']=r.common.BASE+'download/v0.2.0-preview.1/system.iso'
            elif change=='source':rows[8]['role']='repository'
            elif change=='url':rows[0]['url']='https://example.invalid/unpublished'
            else:rows.append(dict(rows[0]))
            with self.assertRaises(ValueError):r.assets(rows,'v0.2.0-preview.1')
    def test_checksum_lists_exact_assets(self):
        with tempfile.TemporaryDirectory() as directory:
            rows=self.rows();path=Path(directory)/'SHA256SUMS'
            for row in rows:row['path']=str(Path(directory)/row['name'])
            path.write_text(''.join(row['sha256']+'  '+row['name']+'\n' for row in rows[:-1]))
            r.checksums(rows)
            path.write_text(path.read_text()+'0'*64+'  extra.deb\n')
            with self.assertRaises(ValueError):r.checksums(rows)
    def test_public_github_response_must_match_actual_assets(self):
        value=self.value();response={'id':1,'draft':False,'prerelease':True,'tag_name':value['tag'],'html_url':value['release_url'],'assets':[{'name':row['name'],'size':row['bytes'],'state':'uploaded','digest':'sha256:'+row['sha256'],'browser_download_url':row['url']} for row in value['artifacts']]}
        r.actual_release(response,value)
        for change in ('draft','stable','digest'):
            changed=copy.deepcopy(response)
            if change=='draft':changed['draft']=True
            elif change=='stable':changed['prerelease']=False
            else:changed['assets'][0]['digest']='sha256:'+'f'*64
            with self.assertRaises(ValueError):r.actual_release(changed,value)
    def test_optional_block_preserves_existing_foundation_and_escapes_values(self):
        template=(ROOT/'dashboard/template.html').read_text();value=self.value()
        with patch.object(r,'public_metadata',return_value=value):result=r.portal(ROOT,template)
        self.assertEqual(result[result.index('            <section class="download section-wrap" id="download">'):],template[template.index('            <section class="download section-wrap" id="download">'):])
        self.assertIn('id="package-preview"',result)
        self.assertIn('G2 and installed-user acquisition qualification are pending.',result)
        self.assertNotIn('VM-tested</span>',result[:result.index('id="download"')])
    def test_signature_and_source_review_are_real_required_boundaries(self):
        with patch.object(r.declarations,'verified_repository',side_effect=ValueError('Actual signature absent')),patch.object(r.archive_metadata,'public_trust',return_value={}):
            with self.assertRaisesRegex(ValueError,'signature'):r.repository(Path('/unavailable'),self.rows())
        with patch.object(r.common,'evidence',return_value={'reviewed':True}):
            with self.assertRaisesRegex(ValueError,'source/legal'):r.source_review(ROOT,{'path':'docs/evidence/f.json','sha256':'a'*64},self.rows(),{'packages':[]},'b'*40)
    def test_independent_public_pin_change_refuses_existing_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);path=root/r.PUBLIC;path.parent.mkdir(parents=True)
            path.write_text(json.dumps(self.value()))
            (root/'config/phase2/archive-public-trust.json').write_text(json.dumps({'fingerprint':'F'*40,'public_keyring_sha256':'a'*64}))
            with self.assertRaisesRegex(ValueError,'independent pins'):r.public_metadata(root)
    def test_all_six_languages_have_exact_pending_scope_copy(self):
        text=(ROOT/'ui/translations.js').read_text()
        block=text.split('/* Dormant package-artifact',1)[1].split('/* Dormant Phase 2',1)[0]
        catalog=json.loads(block.split('Object.assign(window.TODDY_TRANSLATIONS, ',1)[1].rsplit(');',1)[0])
        for translations in catalog.values():
            self.assertEqual(len(translations),5)
            self.assertTrue(all(isinstance(value,str) and value.strip() for value in translations))
        for source in ('Experimental package artifacts','Native packages for qualification.','Package repository artifacts only. Desktop ISO, G2 and installed-user acquisition qualification are pending.','Package testing guide ↗','Package release notes ↗','For disposable Toddy test systems. Downloading packages does not activate AI or grant administration.'):
            self.assertIn('"'+source+'": [',text)
