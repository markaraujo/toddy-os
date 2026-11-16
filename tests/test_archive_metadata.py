"""Unsigned export source fixtures. No signing/private keys/APT/install/VM use."""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
def module(name):
    spec=importlib.util.spec_from_file_location(name,ROOT/'scripts/build/phase2'/(name+'.py'))
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value

metadata=module('archive_metadata');decl=module('acquisition_declarations');p=metadata.p


@unittest.skipUnless(shutil.which('dpkg-deb'),'Native archive reader unavailable')
class ArchiveMetadataTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        self.records=self.root/'records';self.archives=self.root/'archives';self.records.mkdir();self.archives.mkdir()
    def fixture(self,*,extra_control='',copyright=True,name='fixture',notices=None):
        stage=self.root/('stage-'+name);(stage/'DEBIAN').mkdir(parents=True)
        (stage/'DEBIAN/control').write_text('Package: '+name+'\nVersion: 1.0-1\nArchitecture: all\nMaintainer: Source Fixture <fixture@example.invalid>\nDescription: Explicit synthetic archive, not native package acceptance\n'+extra_control)
        directory=stage/'usr/share/doc'/name;directory.mkdir(parents=True)
        if copyright:(directory/'copyright').write_text('Synthetic source fixture; no native qualification.\n')
        if notices is not None:
            (directory/'source-notices').mkdir();(directory/'source-notices/index.json').write_bytes(notices)
        archive=self.archives/(name+'_1.0-1_all.deb')
        subprocess.run(['/usr/bin/dpkg-deb','--root-owner-group','--build',str(stage),str(archive)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        control,payload,_=p.archive_contents(archive)
        record={'name':name,'version':'1.0-1','installed':True,'archive_sha256':p.digest(archive),
            'recipe_sha256':'a'*64,'sources':[{'name':'synthetic-fixture','url':'https://example.invalid/source','sha256':'b'*64}],
            'payload':payload}
        path=self.records/(name+'_1.0-1_all.json');path.write_bytes(p.encoded(record))
        if not copyright:return archive,None
        component=p.component_from_record(path,self.archives)
        projection=self.root/(name+'-projection.json');projection.write_bytes(p.encoded({'schema_version':1,'components':[component]}))
        return archive,projection
    def trust(self):return {'fingerprint':'A'*40,'keyring_sha256':hashlib.sha256(b'public parser fixture').hexdigest(),'bytes':b'public parser fixture','created_unix':900,'expires_unix':5000}
    def test_actual_deb_control_payload_legal_flat_index_and_finite_release(self):
        _,projection=self.fixture();verified,inputs=metadata.collect([projection],None,[],self.records,self.archives)
        documents,inventory=metadata.documents(verified,self.trust(),1000,2000,now=1100)
        self.assertEqual(documents,metadata.documents(verified,self.trust(),1000,2000,now=1100)[0])
        index=p.deb822(documents['Packages'].decode())
        self.assertEqual(index['Filename'],'fixture_'+inventory[0]['archive_sha256']+'.deb')
        self.assertNotIn('/',index['Filename']);self.assertIn(b'Valid-Until:',documents['Release'])
        self.assertFalse(any(name.startswith(('InRelease','Release.gpg','releases.json')) for name in documents))
        with patch.object(metadata.shutil,'disk_usage',return_value=type('Space',(),{'free':200*1024**3})()):
            receipt=metadata.export(self.root/'export',verified,inputs,self.trust(),1000,2000,now=1100)
        self.assertFalse(receipt['signed']);self.assertFalse(receipt['qualification_created'])
        with self.assertRaisesRegex(ValueError,'New canonical'):metadata.export(self.root/'export',verified,inputs,self.trust(),1000,2000,now=1100)
    def test_same_actual_legal_bytes_share_asset_but_distinct_notices_remain(self):
        first,first_projection=self.fixture(name='fixture-a',notices=b'[]\n')
        second,second_projection=self.fixture(name='fixture-b',notices=b'{"scope":"unqualified distinct notice fixture"}\n')
        third,third_projection=self.fixture(name='fixture-c',notices=b'[]\n')
        verified,_=metadata.collect([first_projection,second_projection,third_projection],None,[],self.records,self.archives)
        documents,inventory=metadata.documents(verified,self.trust(),1000,2000,now=1100)
        a,b,c=inventory
        self.assertEqual(a['copyright']['sha256'],b['copyright']['sha256'])
        self.assertNotEqual(a['copyright']['path'],b['copyright']['path'])
        self.assertEqual(a['legal_assets']['copyright'],b['legal_assets']['copyright'])
        self.assertNotEqual(a['legal_assets']['source_notices_index'],b['legal_assets']['source_notices_index'])
        self.assertEqual(a['legal_assets']['source_notices_index'],c['legal_assets']['source_notices_index'])
        self.assertEqual(a['legal_assets']['copyright'],c['legal_assets']['copyright'])
        self.assertEqual(len([name for name in documents if name.startswith('copyright_')]),1)
        self.assertEqual(len([name for name in documents if name.startswith('source-notices_')]),2)
        for row in inventory:
            for kind,name in row['legal_assets'].items():
                self.assertEqual(hashlib.sha256(documents[name]).hexdigest(),row[kind]['sha256'])
        # Identical notice indexes, including empty ones, deduplicate too.
        result={};metadata.merge_legal_assets(result,{'source-notices_'+hashlib.sha256(b'[]\n').hexdigest()+'.json':b'[]\n'})
        metadata.merge_legal_assets(result,dict(result));self.assertEqual(len(result),1)
    def test_conflicting_same_legal_identity_fails_even_if_hash_function_collides(self):
        name='copyright_'+('a'*64)+'.txt';result={name:b'first unqualified fixture'}
        fake=type('Digest',(),{'hexdigest':lambda self:'a'*64})()
        with patch.object(metadata.hashlib,'sha256',return_value=fake):
            with self.assertRaisesRegex(ValueError,'Conflicting'):metadata.merge_legal_assets(result,{name:b'different unqualified fixture'})
        self.assertEqual(result[name],b'first unqualified fixture')
        with self.assertRaises(ValueError):metadata.merge_legal_assets({}, {'Packages':b'not legal metadata'})

    def test_changed_archive_or_repository_authority_in_control_refused(self):
        archive,projection=self.fixture(extra_control='filename: attacker.deb\n')
        with self.assertRaisesRegex(ValueError,'repository authority'):metadata.collect([projection],None,[],self.records,self.archives)
        archive.write_bytes(archive.read_bytes()+b'changed')
        with self.assertRaises(ValueError):metadata.collect([projection],None,[],self.records,self.archives)
    def test_missing_copyright_and_expired_or_unbounded_release_fail(self):
        archive,_=self.fixture(copyright=False)
        with self.assertRaises(ValueError):p.component_from_record(self.records/'fixture_1.0-1_all.json',self.archives)
        for issued,expires in ((1000,1000),(1000,1100),(1000,1000+32*86400),(800,2000),(1000,5001)):
            with self.assertRaisesRegex(ValueError,'validity'):metadata.valid_window(issued,expires,self.trust(),now=1100)
    def test_valid_signature_for_different_cleartext_is_refused(self):
        _,projection=self.fixture();verified,inputs=metadata.collect([projection],None,[],self.records,self.archives)
        with patch.object(metadata.shutil,'disk_usage',return_value=type('Space',(),{'free':200*1024**3})()):
            metadata.export(self.root/'signed-fixture',verified,inputs,self.trust(),1000,2000,now=1100)
        directory=self.root/'signed-fixture'
        for name in ('Release.gpg','InRelease'):(directory/name).write_bytes(b'synthetic signature fixture only')
        def different(argv,**kwargs):
            Path(argv[argv.index('--output')+1]).write_bytes(b'different signed Release')
            return subprocess.CompletedProcess(argv,0)
        with patch.object(decl,'signature',return_value='A'*40),patch.object(decl.subprocess,'run',side_effect=different):
            with self.assertRaisesRegex(ValueError,'detached Release differ'):decl.verified_repository(directory,self.trust(),now=1100)
        self.assertFalse((directory/'releases.json').exists())

    def test_capacity_refusal_precedes_output_creation(self):
        _,projection=self.fixture();verified,inputs=metadata.collect([projection],None,[],self.records,self.archives)
        with patch.object(metadata.shutil,'disk_usage',return_value=type('Space',(),{'free':metadata.HOST_RESERVE})()):
            with self.assertRaisesRegex(ValueError,'capacity'):metadata.export(self.root/'blocked',verified,inputs,self.trust(),1000,2000,now=1100)
        self.assertFalse((self.root/'blocked').exists())


class DeclarationTests(unittest.TestCase):
    def rows(self):
        from runtime.setup.runtime_compat import RUNTIME_VERSION,RUNTIME_ARCHIVE_SHA256
        rows=[]
        for name in decl.ORDER:
            rows.append({'name':name,'version':RUNTIME_VERSION if name=='llama-cpp' else '1.0-1','architecture':'amd64',
                'archive_bytes':100,'installed_bytes':200,'archive_sha256':RUNTIME_ARCHIVE_SHA256 if name=='llama-cpp' else 'a'*64,
                'copyright':{'path':'/usr/share/doc/'+name+'/copyright','sha256':'b'*64},'source_notices_index':None,
                'sources':[{'url':'https://example.invalid/synthetic','sha256':'c'*64}],
                'legal_assets':{'copyright':'copyright-'+name+'_'+('b'*64)+'.txt'},
                'postconditions':{path:'d'*64 for path,owner in decl.POSTCONDITIONS.items() if owner==name}})
        return rows
    def test_all_three_exact_curated_declarations_have_no_qualification(self):
        for release_id,names in decl.RELEASE_PACKAGES.items():
            row,terms=decl.release_declaration(release_id,[row for row in self.rows() if row['name'] in names],1)
            self.assertEqual({package['name'] for package in row['packages']},names)
            self.assertFalse(row['auto_activate']);self.assertNotIn('qualification_sha256',row)
            self.assertEqual(hashlib.sha256(terms).hexdigest(),row['terms_sha256'])
    def test_unqualified_local_archive_and_changed_curated_set_refused(self):
        rows=self.rows();local=next(row for row in rows if row['name']=='llama-cpp');local['archive_sha256']='f'*64
        with self.assertRaisesRegex(ValueError,'runtime_profile_changed'):decl.release_declaration('agent-local',rows,1)
        with self.assertRaisesRegex(ValueError,'Exact curated'):decl.release_declaration('agent-backend',rows,1)
    def test_no_credential_url_arbitrary_file_or_nested_source_asset(self):
        for origin in ('http://example.invalid/','https://user:password@example.invalid/','file:/tmp/repository','https://example.invalid/x?token=secret','https://example.invalid/\nextra'):
            with self.assertRaises(ValueError):decl.source_line(origin)
        self.assertIn(b' ./\n',decl.source_line('https://example.invalid/releases/download/explicit-tag'))
    def test_missing_parent_signatures_fail_without_creating_any_catalog(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);(root/'archive-export.json').write_bytes(p.encoded({'version':1,'kind':'unsigned-flat-native-archive-export',
                'public_fingerprint':'A'*40,'public_keyring_sha256':'b'*64,'producer_sha256':p.digest(metadata.__file__),'files':{},'issued_unix':1000,'expires_unix':2000}))
            with self.assertRaises(ValueError):decl.verified_repository(root,{'fingerprint':'A'*40,'keyring_sha256':'b'*64,'created_unix':900,'expires_unix':5000},now=1100)
            self.assertEqual({path.name for path in root.iterdir()},{'archive-export.json'})
    def test_synthetic_secret_packet_refused_before_any_public_gpg_operation(self):
        # Three bytes only: packet-tag parser fixture, never an actual secret key.
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);key=root/'key.gpg';key.write_bytes(b'\xc5\x01\x04')
            pins=root/'trust.json';pins.write_bytes(p.encoded({'version':1,'public_keyring':'config/phase2/archive-public-key.gpg','algorithm':'Ed25519',
                'public_keyring_sha256':p.digest(key),'fingerprint':'A'*40}))
            with patch.object(metadata.subprocess,'run',side_effect=AssertionError('No GPG on nonpublic packet')):
                with self.assertRaises(ValueError):metadata.public_trust(key,pins)


class OriginalProvenanceTests(unittest.TestCase):
    def test_optional_executor_requires_owned_original_manifest_not_foreign_fallback(self):
        from image_projection import original_source_provenance
        with tempfile.TemporaryDirectory() as temporary:
            target=Path(temporary);path=target/'usr/share/doc/toddy-executor/source-manifest.json';path.parent.mkdir(parents=True)
            path.write_bytes(p.encoded({'package':'toddy-executor','source_inputs':{'runtime/executor/service.py':{'sha256':'c'*64,'bytes':5}}}))
            files={'packager.py':'a'*64,'recipe.py':'b'*64}
            component={'name':'toddy-executor','component_record_sha256':'f'*64,'recipe_sha256':'b'*64}
            record={'source_kind':'book-derived-versioned-recipe','supporting_build_scripts':{'files':files,'sha256':hashlib.sha256(json.dumps(files,sort_keys=True,separators=(',',':')).encode()).hexdigest()},
                'packager_sha256':'a'*64,'payload':{'/usr/share/doc/toddy-executor/source-manifest.json':{'sha256':p.digest(path)}}}
            self.assertEqual(original_source_provenance(component,record,repository=ROOT,target=target),'owned-original-source-manifest')
            path.write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError,'ownership differs'):original_source_provenance(component,record,repository=ROOT,target=target)
            with self.assertRaisesRegex(ValueError,'Unreviewed original'):original_source_provenance({**component,'name':'foreign-package'},record,repository=ROOT,target=target)
