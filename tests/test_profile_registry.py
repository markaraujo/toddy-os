"""Named canonical-profile custody and safe portable-bundle host checks."""
import copy
import fcntl
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest import mock

from runtime.broker.profile_registry import ProfileRegistry,RegistryError,EMPTY_USER,MAX_BUNDLE
from runtime.broker.profiles import ProfileStore,ProfileError

ROOT=Path(__file__).resolve().parents[1]


class RegistryTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)/'profiles'
        self.schema=json.loads((ROOT/'config/phase2/profile.schema.json').read_text())
        self.defaults={name:(ROOT/'config/phase2/profile'/name).read_bytes()
                       for name in ['config.json','SOUL.md','IDENTITY.md','USER.md','AGENTS.md']}
        self.capabilities={'adapters':{'openai','local-llama-cpp'},'tools':{'system-info','shell','file-write','admin-command'},
            'skills':{'explain-system'},'extensions':{'example-extension'},'workflows':{'example-workflow'}}
        self.registry=ProfileRegistry(self.root,self.schema,self.defaults,capabilities=self.capabilities)

    def reopen(self):
        return ProfileRegistry(self.root,self.schema,self.defaults,capabilities=self.capabilities)

    def test_create_select_cas_and_reload_keep_separate_actual_stores(self):
        first=self.registry.create('first')
        second=self.registry.create('second')
        self.assertEqual(self.registry.active(),{'profile_id':None,'generation':0})
        self.assertNotEqual(first['profile_revision'],second['profile_revision'])
        selected=self.registry.select('first',expected_generation=0)
        self.assertEqual(selected,{'profile_id':'first','generation':1})
        other=self.reopen()
        other.select('second',expected_generation=1)
        with self.assertRaisesRegex(RegistryError,'stale_registry_generation'):
            self.registry.select('first',expected_generation=1)
        self.assertEqual(self.registry.active(),{'profile_id':'second','generation':2})
        self.assertEqual(self.root.stat().st_mode&0o777,0o700)
        self.assertEqual(self.registry.path.stat().st_mode&0o777,0o600)
        self.assertNotEqual(self.registry.store('first').path,self.registry.store('second').path)
        self.assertEqual(len(self.registry.list_profiles()['profiles']),2)

    def test_explicit_legacy_adoption_preserves_current_revision_and_never_selects(self):
        files=dict(self.defaults)
        config=json.loads(files['config.json']);config['profile_id']='legacy'
        files['config.json']=json.dumps(config).encode()
        files['USER.md']=b'Existing explicitly owned preferences, not an import.\n'
        legacy=ProfileStore(self.root/'legacy','legacy',self.schema,capabilities=self.capabilities)
        revision=legacy.apply(files,expected_revision=None)
        legacy.pin_task('legacy-task',expected_revision=revision)
        original=legacy.path.read_bytes()
        receipt=self.registry.adopt_existing('legacy')
        self.assertTrue(receipt['adopted'])
        self.assertEqual(receipt['profile_revision'],revision)
        self.assertEqual(legacy.path.read_bytes(),original)
        self.assertEqual(self.registry.store('legacy').snapshot()['USER.md'],files['USER.md'])
        self.registry.bind_task('legacy-task','legacy')
        self.assertEqual(self.registry.locate_task('legacy-task')['profile_revision'],revision)
        self.assertIsNone(self.registry.active()['profile_id'])
        with self.assertRaisesRegex(RegistryError,'profile_directory_exists'):
            self.registry.create('legacy')

    def test_clone_and_portable_export_reset_runtime_state_without_stale_USER_preferences(self):
        self.registry.create('source')
        source=self.registry.store('source')
        files=source.snapshot();config=json.loads(files['config.json'])
        config['provider']={'mode':'remote','adapter_id':'openai','model_id':'example',
                            'connection_ref':'dummy-key-ref','allow_remote_fallback':False}
        config['budgets']['remote_spending_enabled']=True
        config['memory']={'history_enabled':True,'retention_days':30}
        config['automation']={'enabled':True,'workflow_ids':['example-workflow']}
        config['extensions']={'enabled':['example-extension']}
        config['tools']={'enabled':['system-info','shell','file-write','admin-command']}
        files['config.json']=json.dumps(config).encode()
        files['USER.md']=b'Deleted preference: stale private text.\n'
        files['SOUL.md']=b'Reviewed portable persona.\n'
        revision=source.apply(files,expected_revision=source.current())
        # Data in canonical runtime tables is deliberately not a profile bundle.
        with source._db() as db:
            db.execute('CREATE TABLE private_history(secret TEXT)')
            db.execute("INSERT INTO private_history VALUES('dummy-runtime-secret')")
        self.registry.clone('source','cloned',expected_revision=revision)
        clone=self.registry.store('cloned');copied=clone.snapshot();actual=json.loads(copied['config.json'])
        self.assertEqual(copied['SOUL.md'],files['SOUL.md'])
        self.assertEqual(copied['USER.md'],EMPTY_USER)
        self.assertEqual(actual['provider']['mode'],'deferred')
        self.assertIsNone(actual['provider']['connection_ref'])
        self.assertFalse(actual['budgets']['remote_spending_enabled'])
        self.assertEqual(actual['memory'],{'history_enabled':False,'retention_days':0})
        self.assertEqual(actual['automation'],{'enabled':False,'workflow_ids':[]})
        self.assertEqual(actual['extensions'],{'enabled':[]})
        self.assertEqual(actual['tools'],{'enabled':['system-info']})
        self.assertEqual(actual['skills'],{'enabled':['explain-system']})
        with clone._db() as db:
            self.assertIsNone(db.execute("SELECT 1 FROM sqlite_master WHERE name='private_history'").fetchone())
        exported=self.registry.export_bundle('source')
        self.assertNotIn(b'dummy-key-ref',exported)
        self.assertNotIn(b'stale private text',exported)
        self.assertNotIn(b'dummy-runtime-secret',exported)
        self.registry.import_bundle('imported',exported)
        self.assertEqual(self.registry.store('imported').snapshot()['USER.md'],EMPTY_USER)
        self.assertIsNone(self.registry.active()['profile_id'])

    def test_sealed_readonly_fd_round_trip_rejects_writes_and_pipes(self):
        self.registry.create('source')
        descriptor=self.registry.export_fd('source')
        try:
            seals=fcntl.fcntl(descriptor,fcntl.F_GET_SEALS)
            self.assertEqual(seals&(fcntl.F_SEAL_WRITE|fcntl.F_SEAL_GROW|fcntl.F_SEAL_SHRINK),
                             fcntl.F_SEAL_WRITE|fcntl.F_SEAL_GROW|fcntl.F_SEAL_SHRINK)
            with self.assertRaises(OSError):os.write(descriptor,b'change')
            self.registry.import_fd('from-fd',descriptor)
        finally:os.close(descriptor)
        read,write=os.pipe()
        try:
            with self.assertRaisesRegex(RegistryError,'bundle_fd'):
                self.registry.import_fd('pipe',read)
        finally:os.close(read);os.close(write)

    def test_unknown_paths_duplicate_json_bad_hash_and_privileged_config_preserve_working_profile(self):
        self.registry.create('source')
        self.registry.select('source',expected_generation=0)
        original=self.registry.export_bundle('source')
        for change in ['path','hash','grant','entry-type']:
            value=json.loads(original)
            if change=='path':
                value['files']['../state.sqlite']='bad';value['sha256']['../state.sqlite']='a'*64
            elif change=='hash':value['sha256']['SOUL.md']='a'*64
            elif change=='grant':
                config=json.loads(value['files']['config.json']);config['root_grants']=['all']
                text=json.dumps(config);value['files']['config.json']=text
                value['sha256']['config.json']=hashlib.sha256(text.encode()).hexdigest()
            else:value['files']['SOUL.md']={'symlink':'/etc/passwd'}
            with self.subTest(change=change),self.assertRaises((RegistryError,ProfileError)):
                self.registry.import_bundle('bad-'+change,json.dumps(value).encode())
        with self.assertRaisesRegex(RegistryError,'bundle_json'):
            self.registry.import_bundle('duplicate',b'{"bundle_version":1,"bundle_version":1}')
        with self.assertRaisesRegex(RegistryError,'bundle_size'):
            self.registry.import_bundle('oversize',b'x'*(MAX_BUNDLE+1))
        self.assertEqual(self.registry.active(),{'profile_id':'source','generation':1})
        self.assertEqual([row['profile_id'] for row in self.registry.list_profiles()['profiles']],['source'])

    def test_running_task_locator_retains_original_profile_revision_after_selection(self):
        self.registry.create('first');self.registry.create('second')
        first=self.registry.store('first');revision=first.current()
        first.pin_task('task-captured',expected_revision=revision)
        self.registry.bind_task('task-captured','first')
        self.registry.select('first',expected_generation=0)
        self.registry.select('second',expected_generation=1)
        actual=self.reopen().locate_task('task-captured')
        self.assertEqual(actual,{'task_id':'task-captured','profile_id':'first','profile_revision':revision})
        second=self.registry.store('second')
        second.pin_task('task-captured',expected_revision=second.current())
        with self.assertRaisesRegex(RegistryError,'task_locator_conflict'):
            self.registry.bind_task('task-captured','second')
        with self.assertRaisesRegex(RegistryError,'unknown_task_locator'):
            self.registry.locate_task('not-recorded')

    def test_interrupted_ready_publication_reconciles_postcondition_without_apply_replay(self):
        with mock.patch.object(self.registry,'_publish',side_effect=RuntimeError('injected-after-apply')):
            with self.assertRaisesRegex(RuntimeError,'injected-after-apply'):
                self.registry.create('prepared')
        self.assertEqual(self.registry.list_profiles()['profiles'],[])
        resumed=self.reopen()
        with mock.patch.object(ProfileStore,'apply',side_effect=AssertionError('must not replay')):
            self.assertEqual(resumed.reconcile_prepared('prepared'),{'profile_id':'prepared','status':'ready'})
        self.assertEqual(resumed.store('prepared').current(),resumed.list_profiles()['profiles'][0]['profile_revision'])

    def test_unverified_interrupted_creation_stays_held_without_creating_a_success(self):
        with mock.patch.object(ProfileStore,'apply',side_effect=RuntimeError('injected-before-apply')):
            with self.assertRaises(RuntimeError):self.registry.create('unfinished')
        result=self.reopen().reconcile_prepared('unfinished')
        self.assertEqual(result['status'],'held')
        self.assertEqual(self.registry.list_profiles()['profiles'],[])
        self.assertIsNone(self.registry.active()['profile_id'])

    def test_corrupt_profile_is_visible_for_recovery_and_does_not_hide_other_profiles(self):
        self.registry.create('healthy');self.registry.create('broken')
        store=self.registry.store('broken')
        with store._db() as db:db.execute("UPDATE profile_revisions SET bundle='{}'")
        rows={row['profile_id']:row for row in self.registry.list_profiles()['profiles']}
        self.assertEqual(rows['healthy']['status'],'ready')
        self.assertEqual(rows['broken']['status'],'recovery_required')
        with self.assertRaises(ProfileError):self.registry.select('broken',expected_generation=0)
        self.assertIsNone(self.registry.active()['profile_id'])

    def test_busy_registry_and_metadata_limits_fail_without_replaying_profile_work(self):
        with (self.root/'.registry.lock').open('w+b') as lock:
            os.chmod(lock.name,0o600)
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            with self.assertRaisesRegex(RegistryError,'registry_busy'):
                self.registry.create('busy')
        self.assertFalse((self.root/'busy').exists())
        limited=ProfileRegistry(self.root,self.schema,self.defaults,capabilities=self.capabilities,
                                profile_limit=1,locator_limit=1)
        limited.create('one')
        with self.assertRaisesRegex(RegistryError,'profile_limit'):
            limited.create('two')
        self.assertFalse((self.root/'two').exists())
        store=limited.store('one');revision=store.current()
        store.pin_task('task-one',expected_revision=revision)
        store.pin_task('task-two',expected_revision=revision)
        limited.bind_task('task-one','one')
        with self.assertRaisesRegex(RegistryError,'task_locator_limit'):
            limited.bind_task('task-two','one')
        with self.assertRaisesRegex(RegistryError,'unknown_task_locator'):
            limited.locate_task('task-two')

    def test_schema_refusal_and_unsafe_paths_or_permissions_do_not_reset_data(self):
        self.registry.create('preserved')
        with self.registry._db() as db:db.execute('UPDATE registry_schema SET version=2')
        before=self.registry.path.read_bytes()
        with self.assertRaisesRegex(RegistryError,'unsupported_registry_schema'):self.reopen()
        self.assertEqual(self.registry.path.read_bytes(),before)
        with self.assertRaises(ProfileError):self.registry.create('../outside')
        link=Path(self.temp.name)/'link';link.symlink_to(self.root,target_is_directory=True)
        with self.assertRaisesRegex(RegistryError,'unsafe_registry_configuration'):
            ProfileRegistry(link,self.schema,self.defaults)
        self.root.chmod(0o755)
        with self.assertRaisesRegex(RegistryError,'unsafe_registry_custody'):self.reopen()


if __name__=='__main__':unittest.main()
