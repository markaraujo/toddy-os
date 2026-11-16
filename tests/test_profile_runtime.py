"""Actual per-profile task capture/native private effects; no service/root grant."""
import json
import os
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest

from runtime.broker.profile_registry import ProfileRegistry
from runtime.broker.profile_runtime import ProfileRuntime
from runtime.broker.profiles import ProfileStore
from runtime.broker.tasks import TaskJournal
from runtime.broker.core import BrokerCore,NATIVE_TOOLS
from runtime.broker.text import TaskText

ROOT=Path(__file__).resolve().parents[1]


@unittest.skipIf(os.geteuid()==0,'ordinary native tools deliberately refuse root')
class CapturedProfileTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
  base=Path(self.temp.name);self.workspace=base/'workspace';self.workspace.mkdir(mode=0o700)
  schema=json.loads((ROOT/'config/phase2/profile.schema.json').read_text())
  defaults={p.name:p.read_bytes() for p in (ROOT/'config/phase2/profile').iterdir()
            if p.name in {'config.json','SOUL.md','IDENTITY.md','USER.md','AGENTS.md'}}
  self.registry=ProfileRegistry(base/'profiles',schema,defaults,
      capabilities={'adapters':set(),'tools':NATIVE_TOOLS,'skills':{'explain-system'}})
  def factory(profiles):
   journal=TaskJournal(profiles);journal.recover();text=TaskText(journal)
   core=BrokerCore(profiles,journal,self.workspace,dispatch_allowed=lambda:True,text_store=text)
   return SimpleNamespace(profiles=profiles,journal=journal,text_store=text,core=core)
  self.runtime=ProfileRuntime(self.registry,factory)
  self.registry.create('first');self.registry.create('second')
  self.registry.select('first',expected_generation=0)

 def test_queued_write_captures_first_core_before_selection_and_never_retargets_second(self):
  captured=self.runtime.selected()
  files=captured.profiles.snapshot();config=json.loads(files['config.json'])
  config['tools']['enabled']=['system-info','file-write'];files['config.json']=json.dumps(config).encode()
  revision=captured.profiles.apply(files,expected_revision=captured.profiles.current())
  body=json.dumps({'version':1,'text':'Private input not metadata',
      'tool':{'kind':'file-write','arguments':{'path':'captured.txt','text':'Only first profile.','expected_sha256':None}}})
  accepted,request=captured.core.submit('captured-request',revision,body)
  self.registry.bind_task(accepted['task_id'],'first')
  self.registry.select('second',expected_generation=1)
  self.assertIsNot(captured,self.runtime.selected())
  captured.core.execute(accepted['task_id'],request)
  self.assertEqual((self.workspace/'captured.txt').read_text(),'Only first profile.')
  self.assertIs(self.runtime.task(accepted['task_id']),captured)
  self.assertEqual(self.runtime.snapshot(captured,accepted['task_id'])['profile_id'],'first')
  self.assertIsNone(self.runtime.selected().journal.lookup_request('captured-request'))
  old=captured.journal.lookup_request('captured-request')
  self.assertEqual(old['task_id'],accepted['task_id'])
  metadata=captured.journal.list_metadata(0)
  self.assertNotIn('Private input',json.dumps(metadata));self.assertNotIn('Only first profile.',json.dumps(metadata))
  self.assertNotIn('input_hash',json.dumps(metadata))

 def test_metadata_is_bounded_and_old_task_is_readable_when_current_profile_is_broken(self):
  context=self.runtime.selected();revision=context.profiles.current()
  for number in range(35):
   task=context.journal.submit('metadata-'+str(number),revision,'Not retained in metadata')
   self.registry.bind_task(task['task_id'],'first')
  page=context.journal.list_metadata(0)
  self.assertEqual(len(page['tasks']),32);self.assertFalse(page['complete'])
  tail=context.journal.list_metadata(page['next_cursor'])
  self.assertEqual(len(tail['tasks']),3);self.assertTrue(tail['complete'])
  # Make current bytes invalid while keeping the immutable task pin valid.
  files=context.profiles.snapshot();config=json.loads(files['config.json']);config['display_name']='New revision'
  files['config.json']=json.dumps(config).encode()
  new=context.profiles.apply(files,expected_revision=revision)
  with context.profiles._db() as db:db.execute("UPDATE profile_revisions SET bundle='{}' WHERE revision=?",(new,))
  self.assertEqual(self.registry.locate_task(task['task_id'])['profile_revision'],revision)
  self.assertEqual(self.runtime.snapshot(context,task['task_id'])['task_id'],task['task_id'])
  caps=self.runtime.capabilities()
  self.assertTrue(caps['recovery_required']);self.assertEqual(caps['tools'],[])
  self.assertIn('named-profiles-v1',caps['features'])
  self.registry.select('second',expected_generation=1)
  self.assertFalse(self.runtime.capabilities()['agent_backend'])


if __name__=='__main__':unittest.main()
