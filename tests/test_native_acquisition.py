"""Source acquisition guards. Fake signing/native runners are not native proof.

No host keys/packages, pkexec, APT writes, provider contact or guest are used.
The crash test effects only an owned temporary file.
"""
import copy
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch

from runtime.setup.pending import Catalog,PendingStore,SetupError,_encode
from runtime.setup.releases import NativeCatalog,POSTCONDITIONS,REQUIRED_CHECKS,LOCAL_CHECKS,RELEASE_PACKAGES,RELEASE_PERMISSIONS,sha,signature
from runtime.setup.acquisition_journal import Journal
from runtime.setup.native_acquire import install,reconcile
from runtime.setup.native_backend import simulation,NativeBackend,command
from runtime.setup.acquisition import AcquisitionClient

ROOT=Path(__file__).resolve().parents[1]


def fixture(release_id='agent-backend',hardware=None):
    directory=Path('/source-test-only-no-native-authority')
    packages=[{'name':name,'version':'1.0-1','architecture':'amd64','bytes':100,'installed_bytes':4096,'sha256':'a'*64}
              for name in ('toddy-agent','toddy-executor','nodejs','llama-cpp') if name in RELEASE_PACKAGES[release_id]]
    from runtime.setup.runtime_compat import RUNTIME_PROFILE,RUNTIME_VERSION,RUNTIME_ARCHIVE_SHA256,CPU_FLAGS
    local='llama-cpp' in RELEASE_PACKAGES[release_id]
    for package in packages:
        if package['name']=='llama-cpp':package.update(version=RUNTIME_VERSION,sha256=RUNTIME_ARCHIVE_SHA256)
    evidence=_encode({'scope':'installed-native-agent-acquisition','runner_exit':0,'postconditions_exit':0,
                      'package_set_sha256':sha(_encode(packages)),'environment':'native-installed-user','fixture_only':False})
    report=_encode({'version':1,'scope':'installed-native-agent-acquisition','native_result':'passed',
        'package_set_sha256':sha(_encode(packages)),'checks':{key:True for key in REQUIRED_CHECKS|(LOCAL_CHECKS if local else set())},
        'retained_evidence_sha256':sha(evidence)})
    terms=b'Public synthetic review terms. No actual release is qualified.'
    row={'id':release_id,'artifact_id':'source-fixture','packages':packages,
        'postconditions':{path:'b'*64 for path,owner in POSTCONDITIONS.items() if owner in RELEASE_PACKAGES[release_id]},'terms_sha256':sha(terms),
        'license':'MIT; source test only','permissions':RELEASE_PERMISSIONS[release_id],
        'qualification_sha256':sha(report),'requires_owner_authorization':True,'auto_activate':False}
    if local:row['runtime_profile']=copy.deepcopy(RUNTIME_PROFILE)
    source_data=('deb [signed-by='+str(directory/'archive-keyring.gpg')+'] https://example.invalid/toddy native main\n').encode()
    value={'version':1,'generation':1,'not_before':500,'expires':2000,
        'repository':{'id':'toddy-native','sources_sha256':sha(source_data),
                      'inrelease_sha256':'c'*64,'inrelease_bytes':100},'releases':[row]}
    keyring=b'\xc6\x01\x04' # Public-shaped packet only; not a real cryptographic key.
    files={directory/'trust.json':_encode({'version':1,'fingerprint':'A'*40,'keyring_sha256':sha(keyring)}),
        directory/'archive-keyring.gpg':keyring,directory/'releases.json.asc':b'not a real signature',
        directory/'releases.json':_encode(value),directory/'terms'/(sha(terms)+'.txt'):terms,
        directory/'qualifications'/(sha(report)+'.json'):report,
        directory/'qualifications'/(sha(evidence)+'.evidence.json'):evidence,
        Path('/source-test-source.list'):source_data}
    def read(path,**_):
        if path not in files:raise FileNotFoundError(path)
        return files[path]
    def load():
        return NativeCatalog.load(directory=directory,sources=Path('/source-test-source.list'),read=read,
                                  verify=lambda *_:'A'*40,clock=lambda:1000,hardware=hardware or (lambda:('x86_64',set(CPU_FLAGS))))
    return value,files,directory,load


class NativeAcquisitionTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.directory=Path(self.temp.name)
        self.value,self.files,self.catalog_directory,self.load=fixture()
        self.catalog=self.load();self.review=self.catalog.review()
        self.journal=Journal(self.directory/'root-journal',owner_uid=os.getuid());self.addCleanup(self.journal.close)
        self.identity='1'*32;self.uid=12345

    def test_qualified_shape_binds_exact_packages_terms_and_retained_evidence(self):
        self.assertEqual(len(self.review['packages']),3)
        self.assertFalse(self.review['auto_activate'])
        self.assertIn('synthetic',self.catalog.terms())
        self.assertEqual(self.review['download_bytes'],300)
        self.files[self.catalog_directory/'releases.json']=_encode({**self.value,'expires':999})
        with self.assertRaisesRegex(SetupError,'expired'):self.load()

    def test_review_becomes_invalid_if_publisher_changes_before_write(self):
        self.catalog.ensure_current()
        changed=copy.deepcopy(self.value);changed['generation']=2
        self.files[self.catalog_directory/'releases.json']=_encode(changed)
        with self.assertRaisesRegex(SetupError,'release_changed'):self.catalog.ensure_current()

    def test_unsigned_wrong_signer_missing_report_or_arbitrary_package_is_unavailable(self):
        with patch('runtime.setup.releases.subprocess.run',return_value=subprocess.CompletedProcess([],0,b'[GNUPG:] GOODSIG fake\n')):
            with self.assertRaisesRegex(SetupError,'release_signature'):signature(Path('/x'),Path('/y'),Path('/z'))
        path=self.catalog_directory/'releases.json'
        altered=copy.deepcopy(self.value);altered['releases'][0]['packages'][0]['name']='glibc'
        self.files[path]=_encode(altered)
        with self.assertRaisesRegex(SetupError,'release_schema'):self.load()
        self.files[path]=_encode(self.value)
        report=next(path for path in self.files if path.suffix=='.json' and path.parent.name=='qualifications')
        del self.files[report]
        with self.assertRaises(FileNotFoundError):self.load()

    def test_secret_or_truncated_openpgp_packets_are_never_accepted(self):
        from runtime.shared.openpgp import public_key_only
        public_key_only(b'\xc6\x01\x04') # Synthetic tag6, no crypto claim.
        for data in (b'\xc5\x01\x04',b'\xc7\x01\x04',b'\xc6\x05\x04',b'not-a-key'):
            with self.assertRaises(ValueError):public_key_only(data)
        key=self.catalog_directory/'archive-keyring.gpg'
        self.files[key]=b'\xc5\x01\x04'
        trust=json.loads(self.files[self.catalog_directory/'trust.json'])
        trust['keyring_sha256']=sha(self.files[key]);self.files[self.catalog_directory/'trust.json']=_encode(trust)
        with self.assertRaisesRegex(SetupError,'release_public_keyring_required'):self.load()

    def test_foreign_os_duplicate_identity_and_unsupported_os_alias_are_refused(self):
        from runtime.setup.platform import installed_toddy
        def no_link(_):raise OSError('regular file')
        with self.assertRaisesRegex(SetupError,'native_os_unsupported'):
            installed_toddy(read=lambda _:b'ID=ubuntu\n',link=no_link)
        with self.assertRaisesRegex(SetupError,'native_os_unsupported'):
            installed_toddy(read=lambda _:b'ID=toddy\nID=ubuntu\n',link=no_link)
        with self.assertRaisesRegex(SetupError,'native_os_unsupported'):
            installed_toddy(read=lambda _:b'ID=toddy\n',link=lambda _:'/tmp/not-an-os-file')
        installed_toddy(read=lambda _:b'ID=toddy\n',link=no_link,exists=lambda _:False)

    def test_existing_candidate_catalog_still_refuses_untrusted_release_records(self):
        value=json.loads((ROOT/'config/phase2/software-catalog.json').read_text())
        value['qualified_releases']=[self.value['releases'][0]]
        with self.assertRaisesRegex(SetupError,'release_verification_required'):Catalog(_encode(value))

    def test_duplicate_returns_original_before_catalog_locked_or_busy_checks(self):
        self.journal.accept(self.uid,self.identity,self.review)
        self.journal.state(self.uid,self.identity,'installing')
        with patch('runtime.setup.native_acquire.active',side_effect=AssertionError('No redispatch')):
            result=install(self.journal,self.uid,self.identity,self.review['review_sha256'],self.review['terms_sha256'],'agent-backend')
        self.assertEqual(result['state'],'installing')
        with self.assertRaisesRegex(SetupError,'identity_conflict'):
            install(self.journal,self.uid,self.identity,'f'*64,self.review['terms_sha256'],'agent-backend')

    def test_backend_failed_after_write_stays_uncertain_and_never_replays(self):
        parent=self
        class Backend:
            calls=0
            def acquire(self,journal,uid,identity,*_):
                self.calls+=1;journal.state(uid,identity,'installing')
                (parent.directory/'effect').write_text('committed fixture effect')
                raise SetupError('native_write_requires_reconciliation')
        backend=Backend()
        with patch('runtime.setup.native_acquire.active'):
            with self.assertRaisesRegex(SetupError,'requires_reconciliation'):
                install(self.journal,self.uid,self.identity,self.review['review_sha256'],self.review['terms_sha256'],'agent-backend',catalog=self.catalog,backend=backend)
            result=install(self.journal,self.uid,self.identity,self.review['review_sha256'],self.review['terms_sha256'],'agent-backend',catalog=self.catalog,backend=backend)
        self.assertEqual(result['state'],'needs_reconciliation');self.assertEqual(backend.calls,1)
        self.assertEqual((self.directory/'effect').read_text(),'committed fixture effect')

    def test_actual_crash_after_effect_cannot_reaccept_or_repeat_dispatch(self):
        child=r'''
import json,os,sys
from pathlib import Path
from runtime.setup.acquisition_journal import Journal
journal=Journal(Path(sys.argv[1]),owner_uid=os.getuid())
review=json.loads(sys.argv[3]);row,created=journal.accept(12345,'2'*32,review)
assert created
journal.state(12345,'2'*32,'installing')
with open(sys.argv[2],'ab',buffering=0) as stream:stream.write(b'one-effect\n');os.fsync(stream.fileno())
os._exit(9)
'''
        path=self.directory/'crash-journal';effect=self.directory/'crash-effect'
        result=subprocess.run([sys.executable,'-c',child,str(path),str(effect),json.dumps(self.review)],cwd=ROOT)
        self.assertEqual(result.returncode,9)
        journal=Journal(path,owner_uid=os.getuid())
        try:
            row,created=journal.accept(self.uid,'2'*32,self.review)
            self.assertFalse(created);self.assertTrue(row['write_intent_recorded'])
            with self.assertRaisesRegex(SetupError,'reconciliation_required'):journal.accept(self.uid,'3'*32,self.review)
            self.assertEqual(effect.read_bytes(),b'one-effect\n')
        finally:journal.close()

    def test_known_reconcile_observes_effects_without_installing(self):
        self.journal.accept(self.uid,self.identity,self.review);self.journal.state(self.uid,self.identity,'installing')
        class Backend:
            def query(self,names):return {name:'1.0-1' for name in names}
            def postconditions(self,_):pass # Explicit source fixture, no native claim.
        with patch('runtime.setup.native_acquire.package_idle'):
            result=reconcile(self.journal,self.uid,self.identity,Backend())
        self.assertEqual(result['state'],'installed')
        self.assertFalse(result['backend_activated']);self.assertFalse(result['model_or_grant_created'])

    def test_native_solver_cannot_remove_or_change_unreviewed_packages(self):
        simulation(b'Inst toddy-agent (1.0-1 Toddy [amd64])\nConf toddy-agent (1.0-1 Toddy [amd64])\n',{'toddy-agent':'1.0-1'})
        for data in (b'Remv glibc [2.44]\n',b'Inst nodejs (2.0 Toddy [amd64])\n',b'Conf toddy-agent (2.0 Toddy [amd64])\n',b''):
            with self.assertRaisesRegex(SetupError,'native_plan_changed'):simulation(data,{'toddy-agent':'1.0-1'})

    def test_autoactivation_or_setuid_payload_is_refused_before_unpack(self):
        def payload(name,mode=0o644):
            stream=io.BytesIO()
            with tarfile.open(fileobj=stream,mode='w') as bundle:
                info=tarfile.TarInfo(name);info.size=1;info.mode=mode;bundle.addfile(info,io.BytesIO(b'x'))
            return stream.getvalue()
        class Child:
            def __init__(self,data):self.stdout=io.BytesIO(data)
            def wait(self,**_):return 0
            def kill(self):pass
        for name,mode in [('etc/systemd/system/multi-user.target.wants/toddy-executor.service',0o644),('usr/bin/unsafe',0o4755),('usr/share/models/no-weights.gguf',0o644)]:
            with patch('runtime.setup.native_backend.subprocess.Popen',return_value=Child(payload(name,mode))):
                with self.assertRaises(SetupError):NativeBackend.payload_policy(Path('/fixture.deb'),{'installed_bytes':4096})
        with patch('runtime.setup.native_backend.subprocess.Popen',return_value=Child(payload('usr/lib/toddy/worker/worker.mjs'))):
            NativeBackend.payload_policy(Path('/fixture.deb'),{'installed_bytes':4096})

    def test_user_lost_reply_reattaches_known_operation_and_never_resubmits(self):
        legacy=Catalog((ROOT/'config/phase2/software-catalog.json').read_bytes())
        with PendingStore(self.directory/'user-setup',legacy) as store:
            store.create('source-fixture');before=store.load()
            calls=[]
            def runner(argv,**_):
                calls.append(argv)
                if len(calls)==1:return 0,b'' # Lost reply, accepted outcome unknown.
                return 0,_encode({'version':1,'ok':True,'operation_id':argv[3],
                    'review_sha256':self.review['review_sha256'],'state':'installed'})
            client=AcquisitionClient(store,catalog=self.load,run=runner,platform_check=lambda:None,inventory=lambda names:{name:None for name in names})
            review=client.review();self.assertTrue(review['can_install'])
            with self.assertRaisesRegex(SetupError,'review_required'):client.install(review)
            result=client.install(review,accepted_terms=True);self.assertEqual(result['code'],'acquisition_reply_unknown')
            self.assertEqual(client.review()['state'],'reconciliation_required')
            with self.assertRaisesRegex(SetupError,'reconciliation_required'):client.install(review,accepted_terms=True)
            result=client.action('reconcile');self.assertEqual(result['state'],'installed')
            self.assertEqual([call[2] for call in calls],['install','reconcile'])
            self.assertEqual(calls[0][3],calls[1][3]);self.assertEqual(store.load(),before)
            self.assertEqual((self.directory/'user-setup/acquisition.json').stat().st_mode&0o777,0o600)

    def test_unavailable_catalog_is_harmless_and_no_root_helper_runs(self):
        legacy=Catalog((ROOT/'config/phase2/software-catalog.json').read_bytes())
        with PendingStore(self.directory/'offline-setup',legacy) as store:
            store.create('offline-fixture')
            def unavailable():raise FileNotFoundError('No signed native release')
            client=AcquisitionClient(store,catalog=unavailable,platform_check=lambda:None,run=lambda *_:self.fail('No root/network command'))
            self.assertEqual(client.review()['state'],'unavailable')
            self.assertEqual(store.load()[0]['ai_choice'],'later')

    def test_local_runtime_and_combined_closure_require_exact_frozen_profile(self):
        from runtime.setup.runtime_compat import RUNTIME_VERSION,RUNTIME_ARCHIVE_SHA256
        for release_id,count in [('local-runtime',1),('agent-local',4)]:
            value,files,directory,load=fixture(release_id)
            catalog=load();review=catalog.review(release_id)
            self.assertEqual(len(review['packages']),count)
            self.assertTrue(review['model_required']);self.assertFalse(review['runtime_activated'])
            row=next(package for package in review['packages'] if package['name']=='llama-cpp')
            self.assertEqual((row['version'],row['sha256']),(RUNTIME_VERSION,RUNTIME_ARCHIVE_SHA256))
            value['releases'][0]['runtime_profile']['weights_in_package']=True
            files[directory/'releases.json']=_encode(value)
            with self.assertRaisesRegex(SetupError,'native_runtime_profile_changed'):load()

    def test_unsupported_actual_cpu_never_offers_local_install_or_fallback(self):
        _,_,_,load=fixture('local-runtime',hardware=lambda:('x86_64',{'sse4_2'}))
        with self.assertRaisesRegex(SetupError,'native_runtime_cpu_unsupported'):load().review('local-runtime')
        from runtime.setup.runtime_compat import compatible,CPU_FLAGS,validate_installed,INSTALLED_PROFILE
        with self.assertRaisesRegex(SetupError,'native_runtime_cpu_unsupported'):
            compatible(hardware=lambda:('aarch64',set(CPU_FLAGS)))
        validate_installed(copy.deepcopy(INSTALLED_PROFILE))
        changed=copy.deepcopy(INSTALLED_PROFILE);changed['https_client']=True
        with self.assertRaisesRegex(SetupError,'native_runtime_profile_changed'):validate_installed(changed)

    def test_runtime_profile_matches_frozen_accepted_b03_source(self):
        from runtime.setup.runtime_compat import RUNTIME_PROFILE,RUNTIME_ARCHIVE_SHA256,CPU_FLAGS,cpu_features
        baseline=json.loads((ROOT/'config/phase2/local-model.lock.json').read_text())['runtime']
        self.assertEqual(RUNTIME_PROFILE['source_commit'],baseline['commit'])
        self.assertEqual(RUNTIME_PROFILE['source_sha256'],baseline['sha256'])
        self.assertEqual(CPU_FLAGS,baseline['required_cpu_flags'])
        self.assertIn(RUNTIME_ARCHIVE_SHA256,(ROOT/'docs/evidence/B03.md').read_text())
        with patch('runtime.setup.runtime_compat.Path.read_text',return_value='flags : avx avx2 fma\nflags : avx fma\n'):
            self.assertNotIn('avx2',cpu_features()[1])

    def test_local_client_uses_only_curated_release_id_and_no_model_arguments(self):
        _,_,_,load=fixture('local-runtime')
        legacy=Catalog((ROOT/'config/phase2/software-catalog.json').read_bytes())
        with PendingStore(self.directory/'local-setup',legacy) as store:
            store.create('local-fixture');calls=[]
            def runner(argv,**_):
                calls.append(argv);return 0,_encode({'version':1,'ok':True,'operation_id':argv[3],
                    'review_sha256':load().review('local-runtime')['review_sha256'],'state':'installed'})
            client=AcquisitionClient(store,catalog=load,run=runner,platform_check=lambda:None,inventory=lambda names:{name:None for name in names})
            review=client.review('local-runtime');self.assertTrue(review['can_install'])
            client.install(review,accepted_terms=True)
            self.assertEqual(calls[0][4],'local-runtime')
            self.assertEqual(len(calls[0]),7)
            self.assertEqual(store.load()[0]['ai_choice'],'later')

    def test_root_cli_nonroot_never_echoes_accidental_secret_argument(self):
        if os.getuid()==0:self.skipTest('Requires ordinary source test UID')
        secret='not-a-real-secret-do-not-echo'
        result=subprocess.run(['/usr/bin/python3','-I',str(ROOT/'runtime/setup/native_acquire.py'),secret],capture_output=True)
        self.assertEqual(result.returncode,2);self.assertNotIn(secret.encode(),result.stdout+result.stderr)
        self.assertEqual(json.loads(result.stdout)['code'],'acquisition_authentication_required')

    def test_unknown_status_does_not_create_a_journal_or_user_state(self):
        path=self.directory/'absent-root-state'
        with self.assertRaisesRegex(SetupError,'acquisition_unknown'):
            Journal(path,owner_uid=os.getuid(),read_only=True)
        self.assertFalse(path.exists())
        self.journal.accept(self.uid,self.identity,self.review)
        before=(self.directory/'root-journal/operations.sqlite').read_bytes()
        readonly=Journal(self.directory/'root-journal',owner_uid=os.getuid(),read_only=True)
        try:self.assertEqual(readonly.get(self.uid,self.identity)['state'],'prepared')
        finally:readonly.close()
        self.assertEqual((self.directory/'root-journal/operations.sqlite').read_bytes(),before)

    def test_public_command_output_is_bounded_without_host_package_activity(self):
        with self.assertRaisesRegex(SetupError,'native_output_bound'):
            command(['/usr/bin/python3','-c','import sys;sys.stdout.write("x"*(4*1024*1024+1))'],timeout=10)
