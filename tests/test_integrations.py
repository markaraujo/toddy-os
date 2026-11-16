"""Real confined release MCP + canonical broker with synthetic model/receipt binding.

These host checks do not establish a signed native plugin package or guest B10.
"""
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import threading
import unittest
from unittest.mock import patch

from runtime.broker.integrations import Integrations, IntegrationCatalog, IntegrationError, MCP_ID, MCP_TOOL
from runtime.broker.profiles import ProfileStore, ProfileError
from runtime.broker.profile_registry import ProfileRegistry
from runtime.broker.core import BrokerCore, NATIVE_TOOLS
from runtime.broker.configured_engine import ConfiguredEngine
from runtime.broker.tasks import TaskJournal
from runtime.broker.text import TaskText
from runtime.broker.memory_api import MemoryAPI, MemoryEngine

ROOT=Path(__file__).resolve().parents[1]
BUNDLE=ROOT/'runtime/plugins/bundled/release-reference'


class SourceCatalog:
    """Explicit source fixture; never installed or advertised as native qualified."""
    def __init__(self):
        self.present=True
        self.row={'manifest':json.loads((BUNDLE/'manifest.json').read_text()),'bundle':BUNDLE,
            'pin':hashlib.sha256((BUNDLE/'manifest.json').read_bytes()).hexdigest(),'package_version':'source-fixture'}
    def available(self):
        return self.row if self.present else None


@unittest.skipIf(os.geteuid()==0,'ordinary broker tools refuse root')
class IntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not shutil.which('bwrap'):raise unittest.SkipTest('bwrap unavailable; no native containment claim')
        command=['/usr/bin/bwrap','--unshare-all','--unshare-user','--disable-userns','--die-with-parent',
            '--new-session','--cap-drop','ALL','--clearenv','--ro-bind','/usr','/usr','--ro-bind','/lib64','/lib64',
            '--symlink','usr/bin','/bin','--symlink','usr/lib','/lib','--proc','/proc','--dev','/dev','--tmpfs','/tmp','/usr/bin/true']
        if subprocess.run(command,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=5).returncode:
            raise unittest.SkipTest('host mandatory bwrap namespaces unavailable; native proof pending')

    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.owner=True;self.catalog=SourceCatalog()
        self.schema=json.loads((ROOT/'config/phase2/profile.schema.json').read_text())
        self.config=json.loads((ROOT/'config/phase2/profile/config.json').read_text())
        self.config['tools']['enabled']=['system-info',MCP_TOOL]
        self.config['extensions']['enabled']=[MCP_ID]
        self.capabilities={'adapters':{'local-llama-cpp'},'tools':NATIVE_TOOLS|{MCP_TOOL},
            'skills':{'explain-system'},'extensions':{MCP_ID}}
        self.profiles=ProfileStore(self.root/'profile','toddy-default',self.schema,capabilities=self.capabilities,revision_limit=32)
        self.files={'config.json':json.dumps(self.config).encode(),
            'skills/explain-system/SKILL.md':(ROOT/'config/phase2/profile/skills/explain-system/SKILL.md').read_bytes()}
        self.profiles.apply(self.files,expected_revision=None)
        self.integrations=Integrations(self.profiles,ROOT/'config/phase2',catalog=self.catalog,owner_allowed=lambda:self.owner)
    def enable(self):
        return self.integrations.configure(self.profiles.current(),json.dumps({'version':1,'operation':'enable',
            'id':MCP_ID,'manifest_sha256':self.catalog.row['pin']}))
    def call(self,kind,args,files=None):
        return self.integrations.call('task-source','call-source',files or self.profiles.snapshot(),kind,args,
            canceled=lambda:False,remaining_seconds=lambda:5)

    def test_real_confined_mcp_release_lookup_is_useful_source_labeled_and_opt_in(self):
        self.assertFalse(self.integrations.inspect()['extensions'][0]['owner_enabled'])
        self.assertEqual([d['name'] for d in self.integrations.descriptors(self.files)],['load-skill'])
        self.enable()
        result=self.call(MCP_TOOL,{'package':'gdm'})
        self.assertTrue(result['untrusted']);self.assertTrue(result['verified'])
        content=json.loads(result['content']['content'][0]['text'])
        self.assertEqual(content['component']['version'],'50.2-1+toddy1')
        self.assertEqual(content['installed_status'],'not-queried')
        self.assertTrue(content['component']['sources'][0]['sha256'])
        self.assertIn('B02',content['scope'])
        with self.assertRaises(IntegrationError):self.call(MCP_TOOL,{'package':'../../etc/shadow'})
        self.owner=False
        with self.assertRaisesRegex(IntegrationError,'owner'):self.call(MCP_TOOL,{'package':'gdm'})

    def test_missing_package_revoke_or_changed_manifest_never_inherits_activation(self):
        self.enable();self.catalog.present=False
        with self.assertRaises(IntegrationError):self.call(MCP_TOOL,{'package':'gdm'})
        self.assertFalse(self.integrations.inspect()['extensions'][0]['available'])
        self.catalog.present=True;self.catalog.row['pin']='0'*64
        with self.assertRaises(IntegrationError):self.call(MCP_TOOL,{'package':'gdm'})
        self.integrations.reconcile();self.assertFalse(self.integrations._approved('0'*64))
        self.integrations.configure(self.profiles.current(),json.dumps({'version':1,'operation':'revoke','id':MCP_ID}))
        self.assertFalse(self.integrations.inspect()['extensions'][0]['owner_enabled'])

    def test_owner_revoke_terminates_an_actual_confined_child_before_tool_result(self):
        from runtime.plugins.mcp import Plugin
        self.enable();entered=threading.Event();release=threading.Event();errors=[];processes=[]
        original=Plugin._check
        def checkpoint(plugin,*args):
            original(plugin,*args)
            if plugin._process is not None and not entered.is_set():
                processes.append(plugin._process);entered.set()
                if not release.wait(3):raise AssertionError('test did not release real child')
                original(plugin,*args)
        def run():
            try:self.call(MCP_TOOL,{'package':'gdm'})
            except IntegrationError as error:errors.append(str(error))
        with patch.object(Plugin,'_check',checkpoint):
            worker=threading.Thread(target=run);worker.start()
            try:
                self.assertTrue(entered.wait(3))
                self.integrations.configure(self.profiles.current(),json.dumps({'version':1,'operation':'revoke','id':MCP_ID}))
            finally:
                release.set();worker.join(3)
        self.assertFalse(worker.is_alive());self.assertTrue(errors)
        self.assertIsNotNone(processes[0].poll())
        self.assertEqual(self.integrations._active,{})

    def test_custom_skill_import_edit_pin_and_current_disable_without_hooks(self):
        files=self.profiles.snapshot();config=json.loads(files['config.json'])
        config['skills']['enabled']=['owner-notes'];files['config.json']=json.dumps(config).encode()
        path='skills/owner-notes/SKILL.md'
        files[path]=b'---\nname: owner-notes\ndescription: Explain reviewed owner notes.\n---\n\nOriginal selected instructions. Never authority.\n'
        files['skills/owner-notes/references/guide.txt']=b'Reviewed reference text, never executed.'
        old=self.profiles.apply(files,expected_revision=self.profiles.current());self.profiles.pin_task('pinned',expected_revision=old)
        metadata=self.integrations.descriptors(files)
        self.assertNotIn('Original selected instructions',json.dumps(metadata))
        self.assertEqual(metadata[0]['parameters']['properties']['skill_id']['enum'],['owner-notes'])
        result=self.call('load-skill',{'skill_id':'owner-notes'},files)
        self.assertIn('Original selected',result['content']['body']);self.assertFalse(result['content']['grants_tools'])
        reference=self.call('read-skill-resource',{'skill_id':'owner-notes','resource':'references/guide.txt'},files)
        self.assertEqual(reference['content']['text'],'Reviewed reference text, never executed.')
        with self.assertRaises(IntegrationError):self.call('read-skill-resource',{'skill_id':'owner-notes','resource':'../../etc/shadow'},files)
        files[path]=files[path].replace(b'Original selected',b'New owner edited')
        self.profiles.apply(files,expected_revision=old)
        _,pinned=self.profiles.task_snapshot('pinned')
        self.assertIn('Original selected',self.call('load-skill',{'skill_id':'owner-notes'},pinned)['content']['body'])
        registry=ProfileRegistry(self.root/'registry',self.schema,files,capabilities=self.capabilities)
        registry.create('imported',files)
        imported=registry.store('imported').snapshot()
        self.assertEqual(imported[path],files[path])
        self.assertEqual(json.loads(imported['config.json'])['extensions']['enabled'],[])
        self.assertEqual(json.loads(imported['config.json'])['skills']['enabled'],['owner-notes'])
        broken=dict(files);broken['skills/owner-notes/runner.py']=b'print("must not run")'
        with self.assertRaises(ProfileError):self.profiles.validate(broken)
        config['skills']['enabled']=[];files['config.json']=json.dumps(config).encode()
        self.profiles.apply(files,expected_revision=self.profiles.current())
        with self.assertRaisesRegex(IntegrationError,'revoked'):self.call('load-skill',{'skill_id':'owner-notes'},pinned)

    def test_actual_configured_engine_descriptors_and_broker_tool_journal_with_synthetic_model(self):
        self.enable()
        files=self.profiles.snapshot();config=json.loads(files['config.json'])
        config['provider']={'mode':'local','adapter_id':'local-llama-cpp','model_id':'synthetic-only',
            'connection_ref':'test','allow_remote_fallback':False}
        files['config.json']=json.dumps(config).encode();revision=self.profiles.apply(files,expected_revision=self.profiles.current())
        parent=self;calls=[]
        class Adapter:
            def run(self,bootstrap,task,request,prompt,*,on_tool,on_text,canceled):
                definitions={d['name']:d for d in bootstrap['tools']}
                parent.assertIn(MCP_TOOL,definitions);parent.assertIn('load-skill',definitions)
                parent.assertNotIn('Use only when the user asks',json.dumps(definitions))
                for identifier,kind,args in [('lookup',MCP_TOOL,{'package':'gdm'}),('skill','load-skill',{'skill_id':'explain-system'})]:
                    result=on_tool(identifier,kind,args);parent.assertEqual(result['outcome'],'verified');calls.append(result)
                    parent.assertTrue(json.loads(result['content'])['untrusted'])
                on_text('Synthetic model orchestrated verified read-only results.')
                return {'state':'completed'}
        class ConfiguredFixture(ConfiguredEngine):
            def connection_settings(self,profile):return {'model_id':'synthetic-only'}
            def _local(self,profile,settings,canceled):return None,{'credential':'dummy-fixture'},{}
        configured=ConfiguredFixture(ROOT/'config/phase2',adapter=Adapter(),integrations=self.integrations)
        journal=TaskJournal(self.profiles);text=TaskText(journal);memory=MemoryAPI(self.profiles,owner_allowed=lambda:True)
        workspace=self.root/'workspace';workspace.mkdir(mode=0o700)
        core=BrokerCore(self.profiles,journal,workspace,dispatch_allowed=lambda:True,text_store=text,
            engine_runner=MemoryEngine(configured,memory),integrations=self.integrations)
        accepted,request=core.submit('actual-integrations',revision,json.dumps({'version':1,'agent':True,
            'text':'Explain the release package reference.','remote_consent':False}))
        self.assertEqual(core.execute(accepted['task_id'],request)['state'],'completed')
        self.assertEqual(len(calls),2)
        with self.profiles._db() as db:
            self.assertEqual(db.execute('SELECT count(*) FROM task_operations').fetchone()[0],2)
            self.assertNotIn('Synthetic model',json.dumps([dict(r) for r in db.execute('SELECT * FROM task_operations')]))
        self.assertEqual(list(workspace.iterdir()),[])


class CatalogTests(unittest.TestCase):
    def test_missing_unqualified_package_catalog_stays_unavailable(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            catalog=IntegrationCatalog(receipt_root=root,bundle_root=root,trusted_uid=os.getuid())
            self.assertIsNone(catalog.available())
            (root/'release-reference.receipt.json').write_text('{"qualified":true,"entry":"/bin/sh"}')
            self.assertIsNone(catalog.available())


if __name__=='__main__':unittest.main()
