"""Actual managed worker/canonical DB with explicitly synthetic standing RPC."""
import json
import os
from pathlib import Path
from types import SimpleNamespace
import tempfile
import threading
import unittest

from runtime.broker.automation import Automation, AutomationError, ACTIONS
from runtime.broker.automation_control import AutomationControl, StandingPolicy
from runtime.broker.profile_runtime import AutomationRuntime
from runtime.broker.profiles import ProfileStore, ProfileError
from runtime.broker.scheduler import ScheduleError

ROOT=Path(__file__).resolve().parents[1]


class ControlTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        schema=json.loads((ROOT/'config/phase2/profile.schema.json').read_text())
        config=json.loads((ROOT/'config/phase2/profile/config.json').read_text())
        config['automation']={'enabled':True,'workflow_ids':sorted(ACTIONS)}
        self.profiles=ProfileStore(Path(self.temp.name)/'profile','toddy-default',schema,
            capabilities={'tools':{'system-info'},'skills':{'explain-system'},'workflows':ACTIONS})
        self.profiles.apply({'config.json':json.dumps(config).encode()},expected_revision=None)
        self.granted=False;self.owner=True;self.calls=[];self.now=1000.
        parent=self
        class Root:
            def call(self,method,values,signature,timeout):
                # A second real SQLite writer proves no owner-policy IPC runs
                # while the scheduler enable path holds its write transaction.
                with parent.profiles._db() as db:
                    db.execute('BEGIN IMMEDIATE');db.rollback()
                parent.calls.append((method,values,signature,timeout))
                return {'version':1,'action_id':values[0],'allowed':parent.granted}
        self.policy=StandingPolicy(Root())
        class Health:
            services=('fixture.service',)
            def disk(self,budget):
                budget.check();return {'condition':'healthy','actionable':False,'details':{'free_bytes':1}}
        self.automation=Automation(self.profiles,owner_allowed=lambda:self.owner,
            standing_allowed=self.policy,health=Health(),clock=lambda:self.now)
        self.control=AutomationControl(self.automation)
    def mutate(self,operation,**settings):
        return self.control.mutate(self.profiles.current(),json.dumps({'version':1,'operation':operation,**settings}))
    def configure(self):
        return self.mutate('configure',job_id='disk',action='disk-health',interval=60,next_due=self.now,
            missed='skip',catchup=0,seconds=10,max_runs=2)

    def test_standing_rpc_never_caches_or_accepts_profile_authority(self):
        self.assertFalse(self.policy('disk-health'))
        self.granted=True;self.assertTrue(self.policy('disk-health'))
        self.granted=False;self.assertFalse(self.policy('disk-health'))
        self.assertFalse(self.policy('imported-admin-workflow'))
        self.assertEqual(len(self.calls),3)
        self.assertEqual(self.calls[-1],('GetStandingAuthorization',('disk-health',),'(s)',1000))
        for value in ({'version':1,'action_id':'disk-health','allowed':1},
                      {'version':True,'action_id':'disk-health','allowed':True},
                      {'version':1,'action_id':'service-health','allowed':True},
                      {'version':1,'action_id':'disk-health','allowed':True,'token':'ignored'}):
            with self.subTest(value=value):
                fake=SimpleNamespace(call=lambda *a,**k:value)
                self.assertFalse(StandingPolicy(fake)('disk-health'))
        fake=SimpleNamespace(call=lambda *a,**k:(_ for _ in ()).throw(OSError('unavailable')))
        self.assertFalse(StandingPolicy(fake)('disk-health'))

    def test_configure_disabled_then_explicit_standing_enable_stop_and_resume(self):
        self.assertFalse(self.configure()['enabled'])
        with self.assertRaisesRegex(ScheduleError,'authorization'):
            self.mutate('enable',job_id='disk')
        self.granted=True
        self.assertTrue(self.mutate('enable',job_id='disk')['enabled'])
        self.assertTrue(self.mutate('stop')['new_dispatch_stopped'])
        self.assertEqual(self.automation.poll()['state'],'stopped')
        self.assertTrue(self.mutate('enable',job_id='disk')['enabled'])
        self.assertEqual(self.automation.poll()['runs'][0]['state'],'completed')
        self.assertEqual(self.control.inspect()['jobs'][0]['id'],'disk')
        self.assertLess(len(json.dumps(self.control.inspect()).encode()),60000)

    def test_owner_schema_cas_and_shutdown_keep_idle_schedule_without_grant(self):
        self.configure();self.granted=True;self.mutate('enable',job_id='disk')
        self.automation.request_shutdown()
        self.assertEqual(self.automation.poll()['state'],'stopped')
        self.assertTrue(self.control.inspect()['jobs'][0]['enabled'])
        with self.assertRaisesRegex(ProfileError,'stale'):
            self.control.mutate('0'*64,'{}')
        with self.assertRaises(AutomationError):self.mutate('grant-standing',job_id='disk')
        self.owner=False
        with self.assertRaisesRegex(AutomationError,'owner'):
            self.control.inspect()

    def test_one_actual_worker_keeps_captured_profile_and_fast_lifecycle_barrier(self):
        entered,release,changed=threading.Event(),threading.Event(),threading.Event()
        calls=[]
        def poll():
            calls.append('first');entered.set()
            if not release.wait(3):raise AssertionError('probe not released')
            return {'state':'polled','runs':[{'state':'completed'}],'notifications_sent':0}
        stopping=[]
        context=SimpleNamespace(profiles=self.profiles,
            automation=SimpleNamespace(poll=poll,request_shutdown=lambda:stopping.append(True)))
        worker=AutomationRuntime(on_change=lambda c,r:changed.set())
        try:
            self.assertTrue(worker.tick([context]));self.assertTrue(entered.wait(3))
            self.assertFalse(worker.tick([context]))
            worker.stop_accepting([context]);self.assertEqual(stopping,[True])
            self.assertFalse(worker.tick([context]))
        finally:
            release.set();worker.shutdown([context])
        self.assertTrue(changed.is_set());self.assertEqual(calls,['first'])
        self.assertEqual(worker.status['toddy-default'],'polled')


if __name__=='__main__':unittest.main()
