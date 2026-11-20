"""Unprivileged synthetic filesystem/tar fixtures; no guest/cache retirement."""
import base64,copy,gzip,hashlib,importlib.util,io,json,os,stat,struct,subprocess,sys,tarfile,tempfile,unittest
from pathlib import Path
from unittest.mock import Mock,patch
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts/build/phase2'),str(ROOT/'scripts/host')]
import candidate_root_archive as a
import candidate_root_custody as guest
import phase2_candidate_root_custody as host


def native_fixture_tar(root):
    result=subprocess.run(['/usr/bin/tar','--create','--file=-','--format=pax',
        '--pax-option=exthdr.name=%d/PaxHeaders/%f,delete=atime,delete=ctime','--acls','--xattrs','--xattrs-include=*',
        '--numeric-owner','--sparse','--no-recursion','--null','--verbatim-files-from','--directory='+str(root),'--files-from=-'],
        input=b'\0'.join(os.fsencode(name) for name in a.names(root))+b'\0',capture_output=True,check=True)
    return result.stdout


class CandidateArchiveTests(unittest.TestCase):
    def test_failed_live1_is_archived_only_with_its_recovery_journals(self):
        guest.configure('mvp-live-failed1');host.configure('mvp-live-failed1')
        try:
            self.assertEqual(guest.WORK.name,'toddy-mvp-live-image-1')
            self.assertEqual(guest.INPUTS.name,'toddy-mvp-live-native-inputs')
            self.assertEqual(host.CONTEXT.name,'mvp-live-failed1-candidate-root-custody-1')
            self.assertIn('custody-mvp-live-failed1-inspect',(ROOT/'scripts/build/phase2/image_native.sh').read_text())
        finally:
            guest.configure('offline');host.configure('offline')

    def test_failed_live3_is_a_distinct_fixed_archival_profile(self):
        guest.configure('mvp-live-failed3');host.configure('mvp-live-failed3')
        try:
            self.assertEqual(guest.ARTIFACT.name,'root')
            self.assertEqual(guest.WORK.name,'toddy-mvp-live-image-3')
            self.assertEqual(host.CONTEXT.name,'mvp-live-failed3-candidate-root-custody-3')
            self.assertNotEqual(guest.PROFILES['mvp-live'][0],guest.PROFILES['mvp-live-failed3'][0])
            self.assertIn('custody-mvp-live-failed3-inspect',(ROOT/'scripts/build/phase2/image_native.sh').read_text())
        finally:
            guest.configure('offline');host.configure('offline')

    def test_failed_live4_is_distinct_from_the_next_candidate(self):
        guest.configure('mvp-live-failed4');host.configure('mvp-live-failed4')
        try:
            self.assertEqual(guest.WORK.name,'toddy-mvp-live-image-4')
            self.assertEqual(guest.INPUTS.name,'toddy-mvp-live-native-inputs-2')
            self.assertEqual(host.CONTEXT.name,'mvp-live-failed4-candidate-root-custody-4')
            self.assertNotEqual(guest.PROFILES['mvp-live'][0],guest.PROFILES['mvp-live-failed4'][0])
            self.assertIn('custody-mvp-live-failed4-inspect',(ROOT/'scripts/build/phase2/image_native.sh').read_text())
        finally:
            guest.configure('offline');host.configure('offline')

    def test_blocked_live5_has_a_fixed_archival_profile(self):
        guest.configure('mvp-live-failed5');host.configure('mvp-live-failed5')
        try:
            self.assertEqual(guest.WORK.name,'toddy-mvp-live-image-5')
            self.assertEqual(guest.INPUTS.name,'toddy-mvp-live-native-inputs-3')
            self.assertEqual(host.CONTEXT.name,'mvp-live-failed5-candidate-root-custody-5')
            self.assertIn('custody-mvp-live-failed5-inspect',(ROOT/'scripts/build/phase2/image_native.sh').read_text())
        finally:
            guest.configure('offline');host.configure('offline')

    def test_partial_live_stage6_has_a_fixed_archival_profile(self):
        guest.configure('mvp-live-stage6');host.configure('mvp-live-stage6')
        try:
            self.assertEqual(guest.ARTIFACT.name,'mvp-live-root-2')
            self.assertEqual(guest.WORK.name,'toddy-mvp-live-image-2')
            self.assertEqual(host.CONTEXT.name,'mvp-live-stage6-candidate-root-custody-6')
            self.assertIn('custody-mvp-live-stage6-inspect',(ROOT/'scripts/build/phase2/image_native.sh').read_text())
        finally:
            guest.configure('offline');host.configure('offline')

    def test_partial_live_stage7_has_a_fixed_archival_profile(self):
        guest.configure('mvp-live-stage7');host.configure('mvp-live-stage7')
        try:
            self.assertEqual(guest.ARTIFACT.name,'mvp-live-root-2')
            self.assertEqual(guest.WORK.name,'toddy-mvp-live-image-7-reviewed')
            self.assertEqual(host.CONTEXT.name,'mvp-live-stage7-candidate-root-custody-7')
            self.assertIn('custody-mvp-live-stage7-inspect',(ROOT/'scripts/build/phase2/image_native.sh').read_text())
        finally:
            guest.configure('offline');host.configure('offline')
    def test_observer_stage8_has_only_its_fixed_archival_context(self):
        guest.configure('mvp-live-stage8');host.configure('mvp-live-stage8')
        try:
            self.assertEqual(guest.ARTIFACT,Path('/mnt/lfs/sources/stage/toddy-mvp-live-image-8-reviewed/mvp-live-root-2'))
            self.assertEqual(guest.CUSTODY.name,'stage8-root-custody-1')
            self.assertFalse(guest.CUSTODY.is_relative_to(guest.ARTIFACT))
            self.assertEqual(host.CONTEXT.name,'mvp-live-stage8-candidate-root-custody-8')
            self.assertEqual(host.ARCHIVE_NAME,'mvp-live-stage8-candidate8-root.tar.gz')
            self.assertTrue(host.command('inspect')[-1].endswith(' custody-mvp-live-stage8-inspect'))
            self.assertIn("main('mvp-live-stage8')",(ROOT/'scripts/host/phase2_mvp_live_stage8_candidate_root_custody.py').read_text())
            self.assertEqual(guest.STAGE8_PIN,[64788,11562326,10943709])
        finally:
            guest.configure('offline');host.configure('offline')

    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.parent=Path(self.temp.name);self.root=self.parent/'root';self.root.mkdir()
        file=self.root/'a';file.write_bytes(b'public source fixture');file.chmod(0o6755);os.utime(file,ns=(1700000000123456789,1700000000123456789))
        os.setxattr(file,'user.binary',b'raw\x00\xffvalue');os.link(file,self.root/'b');(self.root/'c').symlink_to('a');os.link(self.root/'c',self.root/'d',follow_symlinks=False)
        self.image=a.snapshot(self.root);self.tar=native_fixture_tar(self.root)

    def test_complete_gnu_tar_metadata_bytes_links_and_deterministic_stream(self):
        proof=a.verify_tar(io.BytesIO(self.tar),self.image)
        self.assertTrue(proof['xattrs_ACLs_symlinks_hardlink_classes_verified']);self.assertFalse(proof['privileged_extraction_performed'])
        self.assertEqual(self.tar,native_fixture_tar(self.root))
        self.assertEqual(self.image['hardlink_groups'],[['a','b'],['c','d']])
        self.assertEqual(a.snapshot(self.root),self.image)

    def test_ACL_raw_bytes_and_semantics_survive_without_any_restore(self):
        acl=struct.pack('<I',2)+b''.join(struct.pack('<HHI',*row) for row in [(1,7,0xffffffff),(2,4,os.getuid()+1),(4,5,0xffffffff),(16,5,0xffffffff),(32,0,0xffffffff)])
        os.setxattr(self.root,'system.posix_acl_default',acl);os.setxattr(self.root/'a','system.posix_acl_access',acl)
        image=a.snapshot(self.root);raw=native_fixture_tar(self.root)
        self.assertTrue(a.verify_tar(io.BytesIO(raw),image)['xattrs_ACLs_symlinks_hardlink_classes_verified'])
        self.assertIn('user:'+str(os.getuid()+1)+':r--',a.acl_text(acl))
        with self.assertRaises(ValueError):a.acl_text(b'bad ACL')

    def test_sparse_logical_bytes_are_fully_read_in_streaming_proof(self):
        sparse=self.root/'sparse'
        with sparse.open('wb') as stream:stream.seek(4*1024**2);stream.write(b'end')
        image=a.snapshot(self.root);self.assertLess(sparse.stat().st_blocks*512,sparse.stat().st_size)
        self.assertTrue(a.verify_tar(io.BytesIO(native_fixture_tar(self.root)),image)['state'].startswith('all-members'))

    def test_external_hardlinks_and_unknown_nodes_refuse_snapshot(self):
        os.link(self.root/'a',self.parent/'outside')
        with self.assertRaisesRegex(ValueError,'external_hardlink'):a.snapshot(self.root)
        (self.parent/'outside').unlink();os.mkfifo(self.root/'fifo')
        with self.assertRaisesRegex(ValueError,'special_node'):a.snapshot(self.root)

    def modified(self,change):
        output=io.BytesIO()
        with tarfile.open(fileobj=io.BytesIO(self.tar),mode='r:') as source,tarfile.open(fileobj=output,mode='w',format=tarfile.PAX_FORMAT,encoding='utf-8',errors='surrogateescape') as target:
            for member in source:
                data=source.extractfile(member).read() if member.isfile() else None
                member=copy.deepcopy(member);member,data=change(member,data)
                target.addfile(member,io.BytesIO(data) if data is not None else None)
        return output.getvalue()

    def test_owner_nsmtime_xattr_byte_and_hardlink_corruption_each_refuse(self):
        cases=[lambda m,d:(m,d.replace(b'public',b'broken')) if m.name=='a' else (m,d),
            lambda m,d:(self.set(m,'uid',m.uid+1),d) if m.name=='a' else (m,d),
            lambda m,d:(self.pax(m,'mtime','1700000000.123456788'),d) if m.name=='a' else (m,d),
            lambda m,d:(self.pax(m,'SCHILY.xattr.user.binary','different'),d) if m.name=='a' else (m,d),
            lambda m,d:(self.set(m,'linkname','outside'),d) if m.name=='b' else (m,d)]
        for change in cases:
            with self.subTest(change=change):
                with self.assertRaises(ValueError):a.verify_tar(io.BytesIO(self.modified(change)),self.image)
    @staticmethod
    def set(member,key,value):setattr(member,key,value);return member
    @staticmethod
    def pax(member,key,value):member.pax_headers[key]=value;return member

    def test_private_host_gzip_full_decompression_and_member_proof(self):
        packed=self.parent/'private.tar.gz';expected=host.stream_compress(io.BytesIO(self.tar),packed,self.image['tar_upper_bound_bytes'])
        proof=host.verify_compressed(packed,self.image,expected)
        self.assertEqual(proof['tar_sha256'],hashlib.sha256(self.tar).hexdigest());self.assertFalse(proof['member_proof']['privileged_extraction_performed'])
        with self.assertRaises(ValueError):host.verify_compressed(packed,self.image,{**expected,'tar_sha256':'f'*64})
        packed.chmod(0o644)
        with self.assertRaisesRegex(ValueError,'private_archive'):host.verify_compressed(packed,self.image,expected)


class CandidateRetirementBoundaryTests(unittest.TestCase):
    def test_fixed_scope_requires_finalizer2_and_preserves_all_other_generations(self):
        self.assertEqual(guest.ARTIFACT,Path('/mnt/lfs/sources/stage/toddy-offline-image-1/root'))
        self.assertNotEqual(guest.ARTIFACT,guest.FINAL_ROOT);self.assertFalse(guest.CUSTODY.is_relative_to(guest.ARTIFACT))
        source=(ROOT/'scripts/build/phase2/candidate_root_custody.py').read_text()
        self.assertIn("finished.get('state')!='native-finalizer-verified'",source)
        self.assertIn('validate_finalizer_report(read(report),name,descriptor)',source)
        self.assertIn('p.PreparedPayload.audit_tree(tree,manifest,inputs.generated)',source)
        self.assertIn('unclosed_compiler_jobs(LOG)',source)
        self.assertNotIn('rmtree(WORK)',source);self.assertNotIn('rmtree(FINAL_ROOT)',source)

    def test_unproven_host_receipt_never_reaches_snapshot_or_delete(self):
        with patch.object(guest,'read',return_value={'state':'exported-awaiting-host-proof'}),patch.object(guest.archive,'snapshot') as snapshot,patch.object(guest.shutil,'rmtree') as remove:
            with self.assertRaisesRegex(ValueError,'durable_host_proof'):guest.retire({'state':'passed'})
            snapshot.assert_not_called();remove.assert_not_called()



    def test_only_synthetic_root_removed_after_durable_intent_and_evidence_retained(self):
        for profile in ('offline','h11-expanded','mvp-live-stage8'):
            with self.subTest(profile=profile):self._retirement_fixture(profile)

    def _retirement_fixture(self,profile):
        from types import SimpleNamespace
        with tempfile.TemporaryDirectory() as temporary:
            work=Path(temporary)/'candidate';work.mkdir();root=work/'root';root.mkdir();(root/'file').write_bytes(b'fixture only')
            custody=work/'root-custody-1';custody.mkdir();statefile=custody/'custody.json'
            journal=work/'unpacked.json';journal.write_bytes(b'preserved fixture journal')
            final=Path(temporary)/'reviewed';final.mkdir();(final/'file').write_bytes(b'preserved generation2 fixture')
            image=a.snapshot(root);metadata=custody/'source-metadata.json';metadata.write_bytes(a.encoded(image))
            provenance={'preserved':{str(journal):a.sha(journal)}}
            state={'version':1,'state':'exported-awaiting-host-proof','profile':profile,'root':str(root),
                'producer_sha256':a.sha(Path(guest.__file__)),'archive_verifier_sha256':a.sha(Path(a.__file__)),'metadata_sha256':a.sha(metadata),'tar_sha256':'a'*64,'tar_bytes':10240,'provenance':provenance}
            statefile.write_bytes(a.encoded(state))
            proof={'version':1,'state':'complete-member-and-decompression-verified','metadata_sha256':state['metadata_sha256'],
                'tar_sha256':'a'*64,'tar_bytes':10240,'compressed_sha256':'b'*64,'compressed_bytes':100,'host_receipt_sha256':'c'*64,
                'member_proof':{'state':'all-members-bytes-metadata-verified','entries':len(image['entries']),
                    'unique_regular_bytes':image['unique_regular_bytes'],'xattrs_ACLs_symlinks_hardlink_classes_verified':True,'privileged_extraction_performed':False}}
            original=guest.shutil.rmtree
            def guarded_fixture_remove(path):
                self.assertEqual(path,root);self.assertEqual(json.loads(statefile.read_bytes())['state'],'root-retirement-intended-no-replay')
                original(path)
            def checked_preserved_bound(path,*args,**kwargs):
                if Path(path)==journal and not root.exists():
                    self.assertEqual(args[0] if args else 256*1024**2,8*1024**3 if profile=='h11-expanded' else 256*1024**2)
                return Path(path)
            with patch.object(guest,'PROFILE',profile),patch.object(guest,'ARTIFACT',root),patch.object(guest,'WORK',work),patch.object(guest,'CUSTODY',custody),patch.object(guest,'STATE',statefile),\
                    patch.object(guest,'TARGET',Path(temporary)),patch.object(guest,'eligible',return_value=provenance),patch.object(guest,'read',side_effect=lambda path,**kw:json.loads(Path(path).read_bytes())),\
                    patch.object(guest,'secured',side_effect=checked_preserved_bound),patch.object(guest,'no_consumers') as consumers,\
                    patch.object(guest.shutil,'disk_usage',side_effect=[SimpleNamespace(free=40*1024**3),SimpleNamespace(free=40*1024**3+4096)]),\
                    patch.object(guest.shutil,'rmtree',side_effect=guarded_fixture_remove) as remove:
                remove.avoids_symlink_attacks=True
                result=guest.retire(proof);self.assertEqual(result['state'],'complete');self.assertEqual(result['actual_guest_free_gain_bytes'],4096)
                remove.assert_called_once_with(root);consumers.assert_called_once_with(image)
            self.assertFalse(root.exists());self.assertEqual(journal.read_bytes(),b'preserved fixture journal')
            self.assertEqual((final/'file').read_bytes(),b'preserved generation2 fixture');self.assertTrue(metadata.exists())



class LiveCandidateBoundaryTests(unittest.TestCase):
    def tearDown(self):guest.configure('offline');host.configure('offline')

    def test_live_has_distinct_fixed_context_and_no_arbitrary_profile(self):
        guest.configure('live');host.configure('live')
        self.assertEqual(guest.ARTIFACT,Path('/mnt/lfs/sources/stage/toddy-live-image-1/root'))
        self.assertEqual(guest.INPUTS,Path('/mnt/lfs/sources/stage/toddy-live-native-inputs'))
        self.assertEqual(host.ARCHIVE_NAME,'live-candidate1-root.tar.gz')
        self.assertIn('live-candidate-root-custody-1',str(host.CONTEXT))
        self.assertTrue(host.command('inspect')[-1].endswith(' custody-live-inspect'))
        with self.assertRaises(ValueError):guest.configure('/arbitrary/root')
        with self.assertRaises(ValueError):host.configure('live-reviewed')

    def test_preserved_media_relative_merged_usr_links_are_typed_raw_and_rechecked(self):
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup);parent=Path(temporary.name)
        media=parent/'media';runtime=media/'initramfs/runtime';(runtime/'usr/bin').mkdir(parents=True);(runtime/'usr/lib').mkdir();(runtime/'usr/sbin').mkdir()
        (runtime/'usr/bin/bash').write_bytes(b'retained native fixture')
        for name,target in [('lib64','usr/lib'),('bin','usr/bin'),('sbin','usr/sbin'),('lib','usr/lib'),('usr/bin/sh','bash')]:
            link=runtime/name;link.symlink_to(target);value=guest.preserved_link(link,media)
            self.assertEqual(value['type'],'symlink');self.assertEqual(base64.b64decode(value['target_base64']),os.fsencode(target))
            self.assertEqual(value['target_sha256'],hashlib.sha256(os.fsencode(target)).hexdigest())
            self.assertEqual(value,guest.preserved_link(link,media))
        link=runtime/'bin';before=guest.preserved_link(link,media);link.unlink();link.symlink_to('usr/sbin')
        self.assertNotEqual(before,guest.preserved_link(link,media))

    def test_preserved_links_reject_absolute_escape_and_outside_return_chain(self):
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup);parent=Path(temporary.name)
        media=parent/'retained-media';media.mkdir();outside=parent/'outside';outside.mkdir();(media/'file').write_bytes(b'preserved')
        for target in ('/etc/passwd','../outside'):
            link=media/'link';link.symlink_to(target)
            with self.assertRaisesRegex(ValueError,'absolute|escape'):guest.preserved_link(link,media)
            link.unlink()
        (outside/'return').symlink_to('../retained-media/file');(media/'redirect').symlink_to('../outside');(media/'link').symlink_to('redirect/return')
        with self.assertRaisesRegex(ValueError,'escape'):guest.preserved_link(media/'link',media)

    def test_historical_profiles_require_original_tree_and_preserve_media(self):
        import opaque_tar_profiles
        from types import SimpleNamespace
        for profile,basename,proof in (('h10-expanded','h10-live-root','h10'),('h11-expanded','h11-release-root','h11')):
            with self.subTest(profile=profile),tempfile.TemporaryDirectory() as temporary:
                target=Path(temporary)/'target';repo=Path(temporary)/'repo';(target/'sources/stage').mkdir(parents=True);repo.mkdir()
                with patch.object(guest,'TARGET',target),patch.object(guest,'ROOT',repo):
                    guest.configure(profile);host.configure(profile);root=guest.ARTIFACT;root.mkdir();(root/'file').write_bytes(b'fixture')
                    evidence=guest.WORK/('h10-live-root-evidence' if proof=='h10' else 'h11-release-root-evidence');evidence.mkdir()
                    media=guest.WORK/('h10-live-media' if proof=='h10' else 'h11-release-media');media.mkdir();(media/'retained.iso').write_bytes(b'fixture media')
                    driver=repo/'scripts/build/phase2/image_native.sh';driver.parent.mkdir(parents=True);driver.write_text('# fixture')
                    image=a.snapshot(root);original={'entries':copy.deepcopy(image['entries']),'hardlink_groups':image['hardlink_groups']}
                    for row in original['entries'].values():row['xattrs']={key:hashlib.sha256(base64.b64decode(value)).hexdigest() for key,value in row['xattrs'].items()}
                    manifest=evidence/'original.json';manifest.write_bytes(a.encoded(original));assembly=evidence/'assembly.json';assembly.write_bytes(b'fixture assembly')
                    config={'evidence':evidence.name,'manifest':manifest.name,'manifest_sha256':a.sha(manifest),'assembly_sha256':a.sha(assembly)}
                    identity=SimpleNamespace(st_dev=64788,st_ino=guest.HISTORICAL[profile][1],st_mtime_ns=guest.HISTORICAL[profile][2])
                    with patch.object(guest,'private',return_value=identity),patch.object(guest,'secured',side_effect=lambda path,*args:Path(path)),patch.object(guest,'read',side_effect=lambda path:json.loads(Path(path).read_bytes())),patch.object(opaque_tar_profiles,'profile',return_value=config),patch.object(guest,'no_mounts'):
                        result=guest.eligible();self.assertFalse(result['new_acceptance_claimed']);self.assertFalse(result['foundation_rebuild_authorized'])
                        self.assertIn(str(media/'retained.iso'),result['preserved'])
                        (root/'file').write_bytes(b'changed')
                        with self.assertRaisesRegex(ValueError,'original_full_image_differs'):guest.eligible()
                    self.assertEqual(root.name,basename);self.assertFalse(guest.CUSTODY.is_relative_to(root))
                    self.assertTrue(host.command('inspect')[-1].endswith(' custody-'+profile+'-inspect'))
        guest.configure('offline');host.configure('offline')

    def test_mvp_profiles_have_only_fixed_distinct_slots_and_lease_route(self):
        for name,kind in (('mvp-offline','offline'),('mvp-live','live')):
            with self.subTest(profile=name):
                guest.configure(name);host.configure(name)
                generation=9 if name=='mvp-live' else 1
                self.assertEqual(guest.ARTIFACT,Path('/mnt/lfs/sources/stage/toddy-'+name+f'-image-{generation}/root'))
                self.assertEqual(guest.FINAL_ROOT.name,name+'-root-2')
                self.assertEqual(guest.INPUTS.name,'toddy-mvp-'+('installer-native-inputs' if kind=='offline' else 'live-native-inputs-4'))
                self.assertIn(' custody-'+name+'-inspect',host.command('inspect')[-1])
                self.assertEqual(host.ARCHIVE_NAME,name+f'-candidate{generation}-root.tar.gz')
        with self.assertRaises(ValueError):guest.configure('mvp-arbitrary')
        source=(ROOT/'scripts/build/phase2/image_native.sh').read_text()
        self.assertIn('custody-mvp-offline-inspect|custody-mvp-offline-export',source)
        self.assertIn('custody-mvp-live-inspect|custody-mvp-live-export',source)
        self.assertIn('"$profile" "$action" <&8 8<&-',source)
        self.assertIn('validate_lease(9)',Path(guest.__file__).read_text())
        self.assertIn("inputs.kind={'offline':'base'",Path(guest.__file__).read_text())

    def test_actual_finalize_path_reads_reviewed_inputs_not_candidate1_root(self):
        import ast
        source=ROOT/'scripts/build/phase2/image_assemble.py';tree=ast.parse(source.read_text())
        node=next(row for row in tree.body if isinstance(row,ast.FunctionDef) and row.name=='finalize_native')
        body=ast.unparse(node)
        self.assertIn('ReviewedInputs(kind)',body);self.assertIn("AssemblyRoot(kind + '-reviewed', inputs.manifest)",body)
        self.assertNotIn('adopt_unpacked',body);self.assertNotIn('qualify(',body)
        self.assertNotIn('toddy-live-image-1',body);self.assertNotIn('candidate-clean-image-manifest',body)
        self.assertIn('native.install_payload(assembly.root, plan)',body)

    def test_live_requires_reviewed_inputs_and_resource_completion_before_fresh2(self):
        for profile in ('live','mvp-live'):
            with self.subTest(profile=profile):self._check_live_boundary(profile)

    def _check_live_boundary(self,profile):
        from types import SimpleNamespace
        with tempfile.TemporaryDirectory() as temporary:
            target=Path(temporary)/'target';repo=Path(temporary)/'checkout';target.mkdir();repo.mkdir()
            with patch.object(guest,'TARGET',target),patch.object(guest,'ROOT',repo):
                guest.configure(profile);work=guest.WORK;work.mkdir(parents=True);root=guest.ARTIFACT;root.mkdir();(root/'file').write_bytes(b'fixture')
                inputs=guest.INPUTS;bundle=inputs/'payload';bundle.mkdir(parents=True)
                files={'payload/manifest.json':{'fixture':'UNQUALIFIED'},'policy.json':{},'generated-entries.json':{},
                    'expected-image-manifest.json':{'/file':{'fixture':'UNQUALIFIED'}},'boot-profile.json':{}}
                for name,value in files.items():(inputs/name).write_bytes(a.encoded(value))
                pins={name:a.sha(inputs/name) for name in files};descriptor={'payload_manifest_sha256':pins['payload/manifest.json'],
                    'policy_sha256':pins['policy.json'],'image_manifest_sha256':hashlib.sha256(a.encoded(files['expected-image-manifest.json'])).hexdigest()}
                for old,new in [('candidate-generated-entries.json','generated-entries.json'),('candidate-clean-image-manifest.json','expected-image-manifest.json')]:
                    (work/old).write_bytes((inputs/new).read_bytes())
                (work/'dpkg.log').write_text('fixture only');pin=[root.stat().st_dev,work.stat().st_ino,root.stat().st_ino]
                receipt={'manifest_sha256':pins['payload/manifest.json'],'assembly_pin':pin,'root':guest.VIRTUAL,'dpkg_log_sha256':a.sha(work/'dpkg.log')}
                (work/'unpack-intent.json').write_bytes(a.encoded({**receipt,'state':'unpack-intended'}))
                (work/'unpacked.json').write_bytes(a.encoded({**receipt,'state':'native-archives-unpacked-needs-resource-qualification'}))
                candidate={'state':'native-candidate-awaiting-independent-review','blockers':[],'manifest_sha256':descriptor['payload_manifest_sha256'],
                    'root_inode':root.stat().st_ino,'root_device':root.stat().st_dev,'policy_sha256':descriptor['policy_sha256'],
                    'generated_entries_sha256':pins['generated-entries.json'],'candidate_image_manifest_sha256':pins['expected-image-manifest.json']}
                (work/'candidate-resource-receipt.json').write_bytes(a.encoded(candidate));(work/'resource-intent.json').write_text('{}')
                for name in ('image_assemble.py','resource_recipe.py','image_native.sh'):
                    path=repo/'scripts/build/phase2'/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text('# fixture only')
                def recheck(obj):
                    obj.pins=pins;obj.manifest={'fixture':'UNQUALIFIED'};obj.generated={};obj.descriptor=descriptor;obj.source_hashes={'fixture':'a'*64}
                audit=Mock(return_value=files['expected-image-manifest.json']);payload=SimpleNamespace(strict=json.loads,encoded=a.encoded,PreparedPayload=SimpleNamespace(audit_tree=audit))
                with patch.object(guest,'private',side_effect=lambda path,mode:Path(path).stat()),patch.object(guest,'secured',side_effect=lambda path,*args,**kw:Path(path)),\
                        patch.object(guest,'payload_module',return_value=payload),patch.object(guest.ReviewedInputs,'recheck',autospec=True,side_effect=recheck) as checked,patch.object(guest,'no_mounts'):
                    result=guest.eligible()
                    self.assertFalse(result['finalizer2_performed']);self.assertEqual(result['finalizer_reports_sha256'],{})
                    self.assertEqual(result['workflow_boundary'],'reviewed-live-inputs-before-fresh-finalizer2')
                    self.assertEqual(result['reviewed_input_pins'],pins);self.assertEqual(checked.call_count,2)
                    audit.assert_called_once_with(root,{'fixture':'UNQUALIFIED'},{})
                    self.assertFalse(guest.REVIEWED.exists());self.assertTrue(all('toddy-live-image-2' not in name for name in result['preserved']))
                    guest.REVIEWED.mkdir()
                    with self.assertRaisesRegex(ValueError,'live2_exists'):guest.eligible()
                    guest.REVIEWED.rmdir();(inputs/'expected-image-manifest.json').write_text('{"changed":true}')
                    with self.assertRaisesRegex(ValueError,'independent_review_binding'):guest.eligible()
            guest.configure('offline')


class Stage8ObserverCustodyTests(unittest.TestCase):
    def tearDown(self):guest.configure('offline');host.configure('offline')

    def fixture_maps(self):
        row={'mode':stat.S_IFDIR|0o755,'uid':0,'gid':0,'mtime_ns':1700000000000000000,'xattrs':{}}
        original={'entries':{'.':copy.deepcopy(row),'run':{**row,'mtime_ns':1795016359413183630},
            'file':{'mode':stat.S_IFREG|0o644,'uid':0,'gid':0,'mtime_ns':1700000000000000000,'xattrs':{},'sha256':'a'*64,'size':9}},'hardlink_groups':[]}
        actual=copy.deepcopy(original);actual['entries']['run']['mtime_ns']=1795016822210932469
        actual['entries'].update(copy.deepcopy(guest.STAGE8_DCONF_STATE))
        return original,actual

    def test_only_recorded_full_image_and_observer_delta_passes(self):
        original,actual=self.fixture_maps();before=copy.deepcopy(actual)
        guest.observer_stage8_manifest(actual,original)
        self.assertEqual(actual,before)

    def test_unknown_missing_or_changed_original_output_is_rejected(self):
        original,actual=self.fixture_maps()
        for kind in ('unknown','missing','bytes','mode','uid','mtime','xattr','hardlinks'):
            with self.subTest(kind=kind):
                changed=copy.deepcopy(actual)
                if kind=='unknown':changed['entries']['run/other']=copy.deepcopy(changed['entries']['run'])
                elif kind=='missing':del changed['entries']['file']
                elif kind=='bytes':changed['entries']['file']['sha256']='b'*64
                elif kind=='mode':changed['entries']['file']['mode']=stat.S_IFREG|0o600
                elif kind=='uid':changed['entries']['file']['uid']=101
                elif kind=='mtime':changed['entries']['file']['mtime_ns']+=1
                elif kind=='xattr':changed['entries']['file']['xattrs']['user.observer']='dmFsdWU='
                else:changed['hardlink_groups']=[['file','run/user/0/dconf/user']]
                with self.assertRaisesRegex(ValueError,'stage8_'):guest.observer_stage8_manifest(changed,original)

    def test_changed_observer_metadata_bytes_or_run_stamp_is_rejected(self):
        original,actual=self.fixture_maps()
        for kind in ('uid','mode','size','bytes','mtime','xattr','run-mtime','missing-observer'):
            with self.subTest(kind=kind):
                changed=copy.deepcopy(actual);row=changed['entries']['run/user/0/dconf/user']
                if kind=='uid':row['uid']=1000
                elif kind=='mode':row['mode']=stat.S_IFREG|0o644
                elif kind=='size':row['size']=3
                elif kind=='bytes':row['sha256']='b'*64
                elif kind=='mtime':row['mtime_ns']+=1
                elif kind=='xattr':row['xattrs']['user.observer']='dmFsdWU='
                elif kind=='run-mtime':changed['entries']['run']['mtime_ns']+=1
                else:del changed['entries']['run/user']
                with self.assertRaisesRegex(ValueError,'exact_stage8_observer'):guest.observer_stage8_manifest(changed,original)

    def test_only_fixed_stage8_gcc_preservation_gets_its_signed_size_bound(self):
        guest.configure('mvp-live-stage8');gcc=guest.INPUTS/'payload/archives/gcc_16.2.0-1+toddy2_amd64.deb'
        self.assertEqual(guest.preserved_file_limit(gcc),450963224)
        for other in (gcc.with_name('gcc_other_amd64.deb'),gcc.parent.parent/'gcc_16.2.0-1+toddy2_amd64.deb',guest.WORK/gcc.name):
            self.assertEqual(guest.preserved_file_limit(other),256*1024**2)
        for profile in ('mvp-live-stage7','mvp-live','offline'):
            with patch.object(guest,'PROFILE',profile):self.assertEqual(guest.preserved_file_limit(gcc),256*1024**2)
        with patch.object(guest,'PROFILE','h11-expanded'):self.assertEqual(guest.preserved_file_limit(gcc),8*1024**3)

    def test_retirement_postcheck_uses_same_fixed_gcc_bound_without_removing_files(self):
        from types import SimpleNamespace
        guest.configure('mvp-live-stage8');gcc=guest.INPUTS/'payload/archives/gcc_16.2.0-1+toddy2_amd64.deb'
        journal=guest.WORK/'finalized.json';image={'entries':{'.':{}},'unique_regular_bytes':0}
        provenance={'preserved':{str(gcc):'d'*64,str(journal):'e'*64}}
        state={'version':1,'state':'exported-awaiting-host-proof','profile':guest.PROFILE,'root':str(guest.ARTIFACT),
            'producer_sha256':'a'*64,'archive_verifier_sha256':'a'*64,'metadata_sha256':'a'*64,
            'tar_sha256':'a'*64,'tar_bytes':10240,'provenance':provenance}
        proof={'version':1,'state':'complete-member-and-decompression-verified','metadata_sha256':'a'*64,
            'tar_sha256':'a'*64,'tar_bytes':10240,'compressed_sha256':'b'*64,'compressed_bytes':100,'host_receipt_sha256':'c'*64,
            'member_proof':{'state':'all-members-bytes-metadata-verified','entries':1,'unique_regular_bytes':0,
                'xattrs_ACLs_symlinks_hardlink_classes_verified':True,'privileged_extraction_performed':False}}
        def digest(path):return provenance['preserved'].get(str(path),'a'*64)
        def secured(path,limit=256*1024**2):
            if Path(path)==gcc:
                self.assertTrue(remove.called);self.assertEqual(limit,450963224)
            elif Path(path)==journal and remove.called:self.assertEqual(limit,256*1024**2)
            return Path(path)
        with patch.object(guest,'read',side_effect=lambda path,**kw:state if Path(path)==guest.STATE else image),\
                patch.object(guest.archive,'sha',side_effect=digest),patch.object(guest.archive,'snapshot',return_value=image),\
                patch.object(guest,'eligible',return_value=provenance),patch.object(guest,'secured',side_effect=secured) as checked,\
                patch.object(guest,'save'),patch.object(guest,'fsync'),patch.object(guest,'no_consumers'),\
                patch.object(guest.shutil,'disk_usage',side_effect=[SimpleNamespace(free=40*1024**3),SimpleNamespace(free=40*1024**3+4096)]),\
                patch.object(guest.shutil,'rmtree') as remove,patch.object(guest.os.path,'lexists',return_value=False):
            remove.avoids_symlink_attacks=True
            result=guest.retire(proof);self.assertEqual(result['state'],'complete')
            checked.assert_any_call(str(gcc),450963224)
            remove.assert_called_once_with(guest.ARTIFACT)

    def test_archive_eligibility_binds_receipts_identity_inputs_and_full_drift(self):
        from types import SimpleNamespace
        original,actual=self.fixture_maps()
        with tempfile.TemporaryDirectory() as temporary:
            target=Path(temporary)/'target';repo=Path(temporary)/'repo';log=Path(temporary)/'log';repo.mkdir();log.mkdir()
            with patch.object(guest,'TARGET',target),patch.object(guest,'ROOT',repo),patch.object(guest,'LOG',log):
                guest.configure('mvp-live-stage8');work=guest.WORK;root=guest.ARTIFACT;root.mkdir(parents=True)
                source=work.parent/'toddy-mvp-live-image-8';source.mkdir()
                inputs=guest.INPUTS;inputs.mkdir();(inputs/'payload').mkdir();(inputs/'payload/manifest.json').write_text('{}')
                gcc=inputs/'payload/archives/gcc_16.2.0-1+toddy2_amd64.deb';gcc.parent.mkdir();gcc.write_bytes(b'signed archive fixture')
                final={'state':'native-finalizer-verified','root':guest.VIRTUAL,'assembly_pin':guest.STAGE8_PIN,
                    'checks':{name:{'passed':True,'exit_status':0} for name in ('one','two')},'image_manifest_sha256':'a'*64,
                    'payload_manifest_sha256':'b'*64,'policy_sha256':'c'*64,'generated_entries_sha256':'d'*64}
                live={'state':'source-attributed-live-profile-candidate','root':guest.VIRTUAL,'assembly_pin':guest.STAGE8_PIN,
                    'source_sha256':guest.STAGE8_LIVE_SOURCE,'base_image_manifest_sha256':'a'*64,
                    'production_ready':False,'native_boot_verified':False,'native_login_verified':False}
                for name,value in (('finalized.json',final),('live-profile-receipt.json',live),('evidence/image-manifest.json',original)):
                    path=work/name;path.parent.mkdir(exist_ok=True);path.write_bytes(a.encoded(value))
                journal={'assembled':True,'release_profile':True,'release_accepted':False,'g2_eligible':False,'installer_ready':False,
                    'native_image':guest.VIRTUAL,'image':str(root),'live_profile_receipt_sha256':a.sha(work/'live-profile-receipt.json'),
                    'native_finalizer_receipt_sha256':a.sha(work/'finalized.json')}
                (work/'evidence/assembly.json').write_bytes(a.encoded(journal))
                frozen={name:a.sha(work/name) for name in ('finalized.json','live-profile-receipt.json','evidence/image-manifest.json','evidence/assembly.json')}
                (source/'unpacked.json').write_text('{}');source_hashes={'unpacked.json':a.sha(source/'unpacked.json')}
                failure=log/'b06-generation8-compress.log';failure.write_text('retained native pre-compression failure')
                for name in ('image_native.sh','candidate_root_custody.py','candidate_root_archive.py'):
                    path=repo/'scripts/build/phase2'/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text('# fixture')
                def metadata(path,mode):
                    return SimpleNamespace(st_dev=64788,st_ino=10943709 if path==root else 11562326 if path==work else 10943708)
                def recheck(value):
                    value.descriptor={'payload_manifest_sha256':'b'*64,'policy_sha256':'c'*64,'image_manifest_sha256':'a'*64}
                    value.pins={'generated-entries.json':'d'*64}
                payload=SimpleNamespace(CHECKS={'one','two'})
                with patch.object(guest,'private',side_effect=metadata),patch.object(guest,'secured',side_effect=lambda path,*args,**kw:Path(path)) as secured_files,\
                        patch.object(guest,'read',side_effect=lambda path,**kw:json.loads(Path(path).read_bytes())),\
                        patch.object(guest,'payload_module',return_value=payload),patch.object(guest,'STAGE8_FROZEN',frozen),\
                        patch.object(guest,'STAGE8_SOURCE_JOURNALS',source_hashes),patch.object(guest,'STAGE8_FAILURE_SHA',a.sha(failure)),\
                        patch.object(guest,'STAGE8_ENTRY_COUNTS',(len(original['entries']),len(actual['entries']))),\
                        patch.object(guest.archive,'snapshot',return_value=actual),patch.object(guest.ReviewedInputs,'recheck',autospec=True,side_effect=recheck) as checked_inputs,\
                        patch.object(guest,'no_mounts'),patch.object(guest.shutil,'rmtree') as remove:
                    result=guest.eligible()
                    self.assertEqual(result['assembly_pin'],guest.STAGE8_PIN)
                    self.assertEqual(result['workflow_boundary'],'observed-stage8-root-archival-only-no-media-or-boot-acceptance')
                    self.assertFalse(result['ephemeral_finalizer_reports_replayed'])
                    self.assertIn(str(failure),result['preserved']);self.assertIn(str(source/'unpacked.json'),result['preserved'])
                    secured_files.assert_any_call(gcc,450963224)
                    self.assertIn(str(gcc),result['preserved'])
                    remove.assert_not_called()
                    final_bytes=(work/'finalized.json').read_bytes()
                    (work/'finalized.json').write_text('{"changed":true}')
                    with self.assertRaisesRegex(ValueError,'frozen_receipt_changed'):guest.eligible()
                    (work/'finalized.json').write_bytes(final_bytes)
                    with patch.object(guest,'STAGE8_PIN',[64788,11562326,999]):
                        with self.assertRaisesRegex(ValueError,'frozen_root_identity'):guest.eligible()
                    unexpected=work.parent/'toddy-mvp-live-compression-1';unexpected.mkdir()
                    with self.assertRaisesRegex(ValueError,'unexpected_media_output'):guest.eligible()
                    unexpected.rmdir()
                    failed_bytes=failure.read_bytes();failure.write_text('changed failure')
                    with self.assertRaisesRegex(ValueError,'compression_failure_changed'):guest.eligible()
                    failure.write_bytes(failed_bytes)
                    def bad_input(value):
                        recheck(value);value.descriptor['payload_manifest_sha256']='f'*64
                    checked_inputs.side_effect=bad_input
                    with self.assertRaisesRegex(ValueError,'signed_inputs_changed'):guest.eligible()
                    checked_inputs.side_effect=recheck
                    remove.assert_not_called()

if __name__=='__main__':unittest.main()
