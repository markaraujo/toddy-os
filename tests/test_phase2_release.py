"""Disposable source custody fixtures; never public/native release acceptance."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('phase2_release_fixture',ROOT/'scripts/phase2_release.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)


def save(path,value):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,sort_keys=True))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


class ReleaseCustodyTests(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory();self.addCleanup(self.temporary.cleanup)
        self.base=Path(self.temporary.name);self.root=self.base/'fixture-repository';self.root.mkdir()
        self.artifacts=self.base/'artifacts';self.artifacts.mkdir();self.downloads=self.base/'independent-downloads';self.downloads.mkdir()
        subprocess.run(['git','init','-q',str(self.root)],check=True)
        self.git('config','user.email','source-fixture@example.invalid');self.git('config','user.name','Unqualified source fixture')
        (self.root/'fixture.txt').write_text('Source fixtures are not native evidence or published releases.\n')
        self.commit();self.source=self.git('rev-parse','HEAD');self.tag='v0.2.0-phase2.fixture';self.git('tag',self.tag)
        self.iso=self.artifacts/'fixture.iso';self.iso.write_bytes(b'Unqualified source fixture'.ljust(32769,b'\0')+b'CD001'+b'fixture')
        self.pins={'sha256':sha(self.iso),'bytes':self.iso.stat().st_size}
        component={'name':'source-fixture-only','version':'1','archive_sha256':'a'*64,'component_record_sha256':'b'*64,'recipe_sha256':'c'*64,'sources':[]}
        self.inventory=self.artifacts/'components.json';save(self.inventory,{'components':[component]})
        inventory_evidence=self.root/'docs/evidence/fixture-components.json';inventory_evidence.parent.mkdir(parents=True);shutil.copyfile(self.inventory,inventory_evidence)
        guard=self.root/'scripts/qualification/native_acquisition_release_guard.py';guard.parent.mkdir(parents=True);shutil.copyfile(ROOT/'scripts/qualification/native_acquisition_release_guard.py',guard)
        native={}
        for check in r.CHECKS:
            path=self.root/'docs/evidence'/(check+'.json')
            value={'scope':'UNQUALIFIED SOURCE FIXTURE ONLY','final_iso':self.pins,'source_commit':self.source,'native_guest':True,'all_required_checks_passed':True}
            if check in ('bios-installed-detached-boot','uefi-installed-detached-boot'):value.update(firmware=check.split('-')[0],installed_boot=True,installation_media_detached=True)
            if check=='native-acquisition-full-flow':value['native_acquisition_guard']={'script_sha256':sha(guard),'exit':0,'result':{'all_advertised_entries_full_flow':True,'expected_public_trust_matched':True}}
            save(path,value)
            native[check]={'state':'passed','path':path.relative_to(self.root).as_posix(),'sha256':sha(path)}
        self.g2_path=self.root/'docs/evidence/G2-fixture.json'
        self.g2={'version':1,'gate':'G2','state':'technical-passed-delivery-pending','source_commit':self.source,'iso':self.pins,'native_checks':native,'physical_validation':'pending','experimental_preview':True,'native_package_manifest':{'path':'docs/evidence/fixture-components.json','sha256':sha(inventory_evidence)}}
        save(self.g2_path,self.g2)
        self.status={'gates':{'G2':'pending'},'owner_review':{'phase_2_approved':True},'milestones':[{'id':'B%02d'%i,'status':'in_progress' if i==13 else 'completed','evidence':['docs/evidence/G2-fixture.json'] if i==13 else []} for i in range(1,14)]}
        save(self.root/'status.json',self.status)
        files={'iso':self.iso,'inventory':self.inventory}
        for role in ('source','guide','build-guide','recovery','licenses'):
            file=self.artifacts/(role+'.txt');file.write_text('Unqualified fixture '+role);files[role]=file
        checksums=self.artifacts/'SHA256SUMS';checksums.write_text(''.join(sha(file)+'  '+file.name+'\n' for file in files.values()));files['checksums']=checksums
        self.request={'version':1,'tag':self.tag,'source_commit':self.source,'release_url':r.BASE+'tag/'+self.tag,'g2_evidence':{'path':'docs/evidence/G2-fixture.json','sha256':sha(self.g2_path)},'artifacts':[{'role':role,'path':str(file),'url':r.BASE+'download/'+self.tag+'/'+file.name} for role,file in files.items()]}
        self.commit()

    def git(self,*args):return r.git(self.root,*args)
    def commit(self):self.git('add','.');self.git('commit','-qm','Unqualified source fixture')
    def prepared(self):return r.prepare(self.root,self.request)
    def publication_fixture(self,prepared):
        response={'id':1,'draft':False,'prerelease':True,'tag_name':self.tag,'html_url':self.request['release_url'],'scope':'UNQUALIFIED SOURCE FIXTURE ONLY','assets':[{'name':row['name'],'size':row['bytes'],'state':'uploaded','digest':'sha256:'+row['sha256'],'browser_download_url':row['url']} for row in prepared['artifacts']]}
        path=self.root/'docs/evidence/github-fixture.json';save(path,response);self.commit()
        for row in prepared['artifacts']:shutil.copyfile(row['path'],self.downloads/row['name'])
        return path,response

    def test_absent_public_metadata_preserves_foundation_exactly(self):
        template=(ROOT/'dashboard/template.html').read_text()
        self.assertEqual(r.portal(self.root,template),template)
        self.assertFalse((ROOT/r.PUBLIC).exists())

    def test_prepare_binds_files_checksum_and_tag_without_available_release(self):
        prepared=self.prepared()
        self.assertEqual(prepared['state'],'prepared-publication-unverified')
        self.assertEqual(next(row for row in prepared['artifacts'] if row['role']=='iso')['sha256'],sha(self.iso))
        self.assertFalse((self.root/r.PUBLIC).exists())
        self.git('tag','-d',self.tag)
        with self.assertRaises(subprocess.CalledProcessError):self.prepared()

    def test_corrupt_checksum_or_unreviewed_asset_set_rejected(self):
        checksum=next(Path(row['path']) for row in self.request['artifacts'] if row['role']=='checksums');checksum.write_text('0'*64+'  fixture.iso\n')
        with self.assertRaisesRegex(ValueError,'SHA256SUMS'):self.prepared()
        request=copy.deepcopy(self.request);request['artifacts'][0]['url']='https://example.invalid/unreviewed.iso'
        with self.assertRaisesRegex(ValueError,'identity/hash/URL'):r.prepare(self.root,request)

    def test_pending_status_or_old_iso_native_evidence_cannot_be_promoted(self):
        self.status['milestones'][5]['status']='in_progress';save(self.root/'status.json',self.status);self.commit()
        with self.assertRaisesRegex(ValueError,'completed B01-B12'):self.prepared()
        self.status['milestones'][5]['status']='completed';save(self.root/'status.json',self.status)
        key='bios-installed-detached-boot';row=self.g2['native_checks'][key];path=self.root/row['path'];value=json.loads(path.read_text());value['final_iso']={'sha256':'d'*64,'bytes':1};save(path,value);row['sha256']=sha(path)
        save(self.g2_path,self.g2);self.request['g2_evidence']['sha256']=sha(self.g2_path);self.commit()
        with self.assertRaisesRegex(ValueError,'this final ISO/source'):self.prepared()

    def test_component_only_acquisition_cannot_satisfy_final_native_guard(self):
        row=self.g2['native_checks']['native-acquisition-full-flow'];path=self.root/row['path']
        value=json.loads(path.read_text());value['native_acquisition_guard']['result']['all_advertised_entries_full_flow']=False
        save(path,value);row['sha256']=sha(path);save(self.g2_path,self.g2)
        self.request['g2_evidence']['sha256']=sha(self.g2_path);self.commit()
        with self.assertRaisesRegex(ValueError,'full-flow native acquisition'):self.prepared()

    def test_public_assets_require_nondraft_digests_and_independent_downloads(self):
        prepared=self.prepared();path,response=self.publication_fixture(prepared)
        response['draft']=True;save(path,response);self.commit()
        with self.assertRaisesRegex(ValueError,'public GitHub prerelease'):r.promote(self.root,prepared,path,self.downloads)
        response['draft']=False;response['assets'][0]['digest']='sha256:'+'0'*64;save(path,response);self.commit()
        with self.assertRaisesRegex(ValueError,'size/digest/URL'):r.promote(self.root,prepared,path,self.downloads)
        response['assets'][0]['digest']='sha256:'+prepared['artifacts'][0]['sha256'];save(path,response);self.commit()
        (self.downloads/'fixture.iso').write_bytes(b'broken download')
        with self.assertRaisesRegex(ValueError,'Independent public-route'):r.promote(self.root,prepared,path,self.downloads)
        with self.assertRaisesRegex(ValueError,'Independent public-route'):r.promote(self.root,prepared,path,self.artifacts)

    def test_verified_metadata_renders_current_links_and_keeps_foundation_and_limits(self):
        prepared=self.prepared();path,response=self.publication_fixture(prepared)
        public=r.promote(self.root,prepared,path,self.downloads)
        self.assertNotIn('path',public['artifacts'][0]);self.assertEqual(public['pages_handoff'],'pending-deployment-verification')
        save(self.root/r.PUBLIC,public)
        page=r.portal(self.root,(ROOT/'dashboard/template.html').read_text())
        self.assertIn(self.tag,page);self.assertIn('Physical hardware validation pending.',page)
        self.assertIn('v0.1.0-foundation.1',page);self.assertNotIn('GNOME and the assistant are not included yet.',page)
        for row in public['artifacts']:self.assertIn(row['url'],page)
        # Render validates retained public digest evidence again, not arbitrary JSON claims.
        public['artifacts'][0]['sha256']='e'*64;save(self.root/r.PUBLIC,public)
        with self.assertRaisesRegex(ValueError,'Candidate-bound'):r.portal(self.root,page)

    def test_delivery_does_not_require_false_B13_completion_and_finished_metadata_is_immutable(self):
        self.assertEqual(r.acceptance_state(self.root,self.request['g2_evidence']),'delivery-in-progress')
        prepared=self.prepared();path,response=self.publication_fixture(prepared)
        public=r.promote(self.root,prepared,path,self.downloads);save(self.root/r.PUBLIC,public);self.commit()
        before=(self.root/r.PUBLIC).read_bytes()
        self.status['milestones'][-1]['status']='completed';self.status['gates']['G2']='passed'
        save(self.root/'status.json',self.status);self.commit()
        self.assertEqual(r.acceptance_state(self.root,self.request['g2_evidence']),'finished-release')
        self.assertEqual(r.public_metadata(self.root),public)
        with self.assertRaisesRegex(ValueError,'finished release is immutable'):self.prepared()
        with self.assertRaisesRegex(ValueError,'finished release is immutable'):r.promote(self.root,prepared,path,self.downloads)
        self.assertEqual((self.root/r.PUBLIC).read_bytes(),before)

    def test_canonical_G2_cannot_pass_early_or_replace_missing_native_proofs(self):
        self.status['gates']['G2']='passed';save(self.root/'status.json',self.status);self.commit()
        with self.assertRaisesRegex(ValueError,'state must remain consistent'):self.prepared()
        self.status['gates']['G2']='pending';save(self.root/'status.json',self.status)
        self.g2['state']='passed';save(self.g2_path,self.g2);self.request['g2_evidence']['sha256']=sha(self.g2_path);self.commit()
        with self.assertRaisesRegex(ValueError,'Candidate-bound'):self.prepared()

    def test_dormant_release_copy_has_all_five_translation_columns(self):
        source=(ROOT/'ui/translations.js').read_text().split('/* Dormant Phase 2 release copy;',1)[1]
        block=source.split('Object.assign(window.TODDY_TRANSLATIONS, ',1)[1].rsplit(');',1)[0]
        catalog=json.loads(block)
        for key in ('Phase 2 preview ISO ↗','Corresponding source ↗','Component inventory ↗','Owner guide ↗','Build guide ↗','Recovery guide ↗','Licenses ↗','Native validation evidence ↗','Release notes ↗','Final native guest checks passed. Physical hardware validation pending.'):
            self.assertEqual(len(catalog[key]),5)
            self.assertTrue(all(isinstance(text,str) and text.strip() for text in catalog[key]))

    def test_experimental_only_and_outputs_never_overwrite(self):
        request=copy.deepcopy(self.request);request['tag']='v1.0.0';request['release_url']=r.BASE+'tag/v1.0.0'
        with self.assertRaisesRegex(ValueError,'experimental tag'):r.prepare(self.root,request)
        path=self.base/'new.json';r.write_new(path,{'scope':'source fixture'});self.assertEqual(path.stat().st_mode&0o777,0o600)
        with self.assertRaises(FileExistsError):r.write_new(path,{})


if __name__=='__main__':unittest.main()
