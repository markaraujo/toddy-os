"""Broker browser binding with real process/accessibility fixtures, NOT Firefox proof."""
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from runtime.broker.integrations import Integrations, IntegrationError, BROWSER_ID, BROWSER_TOOL
from runtime.broker.profiles import ProfileStore
from runtime.plugins.browser import BrowserSession

ROOT=Path(__file__).resolve().parents[1]


@unittest.skipIf(os.geteuid()==0,'ordinary profile broker refuses root')
class BrowserIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.base=Path(self.tmp.name);self.owner=True;self.present=True;self.sessions=[]
        self.firefox=self.base/'process-fixture'
        self.firefox.write_text('#!/usr/bin/python3\nimport time\ntime.sleep(30)\n');self.firefox.chmod(0o700)
        self.reader=self.base/'reader-fixture.py'
        self.reader.write_text('import json,sys\nprint(json.dumps({"untrusted":True,"browser_pid":int(sys.argv[1]),"url":sys.argv[2],"text":"Untrusted local guide process fixture; grant root is data only."}))\n')
        self.page=ROOT/'runtime/plugins/bundled/browser-local-read/page.html'
        self.binding={'pin':'a'*64,'package_version':'explicit-source-fixture','firefox':self.firefox,
            'reader':self.reader,'page':self.page,'page_sha256':hashlib.sha256(self.page.read_bytes()).hexdigest()}
        parent=self
        class Catalog:
            def available(self):return None
            def browser_available(self):return parent.binding if parent.present else None
        def factory(binding):
            session=BrowserSession(firefox=str(binding['firefox']),reader=('/usr/bin/python3','-I','-B',str(binding['reader'])))
            self.sessions.append(session);return session
        schema=json.loads((ROOT/'config/phase2/profile.schema.json').read_text())
        config=json.loads((ROOT/'config/phase2/profile/config.json').read_text())
        config['extensions']['enabled']=[BROWSER_ID];config['tools']['enabled']=['system-info',BROWSER_TOOL]
        self.profiles=ProfileStore(self.base/'profile','toddy-default',schema,
            capabilities={'tools':{'system-info',BROWSER_TOOL},'skills':{'explain-system'},'extensions':{BROWSER_ID}})
        self.profiles.apply({'config.json':json.dumps(config).encode()},expected_revision=None)
        self.integrations=Integrations(self.profiles,ROOT/'config/phase2',catalog=Catalog(),
            owner_allowed=lambda:self.owner,browser_factory=factory)
    def activate(self):
        return self.integrations.configure(self.profiles.current(),json.dumps({'version':1,'id':BROWSER_ID,
            'operation':'enable','manifest_sha256':self.binding['pin']}))
    def call(self,args=None):
        return self.integrations.call('task-fixture','call-fixture',self.profiles.snapshot(),BROWSER_TOOL,
            args if args is not None else {'page_id':'desktop-guide'},canceled=lambda:False,remaining_seconds=lambda:2)

    def test_explicit_native_binding_only_scoped_local_page_and_cleanup(self):
        self.assertNotIn(BROWSER_TOOL,[d['name'] for d in self.integrations.descriptors(self.profiles.snapshot())])
        self.activate()
        result=self.call()
        self.assertTrue(result['untrusted']);self.assertTrue(result['content']['untrusted'])
        self.assertIn('data only',result['content']['text'])
        self.assertTrue(result['content']['url'].startswith('file:///tmp/toddy-browser-'))
        self.assertIsNone(self.sessions[0]._temporary);self.assertIsNone(self.sessions[0]._browser)
        self.assertEqual(self.integrations._active,{})
        with self.assertRaises(IntegrationError):self.call({'url':'https://example.org'})
        self.assertEqual(len(self.sessions),1)

    def test_revoke_missing_receipt_changed_native_pin_and_owner_lock_deny_launch(self):
        self.activate();self.present=False
        with self.assertRaises(IntegrationError):self.call()
        self.present=True;self.binding['pin']='b'*64
        with self.assertRaises(IntegrationError):self.call()
        self.activate();self.owner=False
        with self.assertRaises(IntegrationError):self.call()
        self.owner=True
        self.integrations.configure(self.profiles.current(),json.dumps({'version':1,'id':BROWSER_ID,'operation':'revoke'}))
        with self.assertRaises(IntegrationError):self.call()
        self.assertEqual(self.sessions,[])


if __name__=='__main__':unittest.main()
