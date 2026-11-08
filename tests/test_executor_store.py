"""Independent policy/operation core; these tests do not claim root IPC proof."""
import json
import multiprocessing
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
import threading
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'runtime/executor'))
from store import Store,PolicyError


def interrupted(directory,marker):
    store=Store(Path(directory));
    def apply(kind,args):
        Path(marker).write_text('effect happened')
        import time
        while True:time.sleep(1)
    store.dispatch(101,None,'crash','configuration',{'synthetic':'input'},apply)


class ExecutorStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.path=Path(self.temp.name)/'policy'
        self.now=1000.;self.store=Store(self.path,clock=lambda:self.now)
        self.arguments={'fixture':'private dummy string not audit material'}
    def tearDown(self):self.temp.cleanup()
    def grant(self):return self.store.set_grant(101,'standing',expires=2000)
    def plan(self,op='operation'):
        return self.store.plan(101,None,op,'configuration',self.arguments)
    def dispatch_operation(self,op='operation',apply=lambda kind,args:{'verified':True}):
        return self.store.dispatch(101,None,op,'configuration',self.arguments,apply)
    def test_no_grant_wrong_user_expiry_and_session(self):
        with self.assertRaisesRegex(PolicyError,'grant_required'):self.plan()
        self.store.set_grant(101,'session',expires=2000,session='sessionA')
        with self.assertRaisesRegex(PolicyError,'grant_required'):self.plan()
        self.store.plan(101,'sessionA','a','configuration',self.arguments)
        with self.assertRaisesRegex(PolicyError,'grant_required'):
            self.store.plan(102,'sessionA','b','configuration',self.arguments)
        with self.assertRaisesRegex(PolicyError,'operation_identity_conflict'):
            self.store.dispatch(102,'sessionA','a','configuration',self.arguments,lambda *_:self.fail())
        self.now=2000
        with self.assertRaisesRegex(PolicyError,'grant_required'):
            self.store.dispatch(101,'sessionA','a','configuration',self.arguments,lambda *_:self.fail())
    def test_revocation_generation_and_no_replay(self):
        first=self.grant();self.plan();self.store.revoke(101)
        with self.assertRaisesRegex(PolicyError,'grant_required'):self.dispatch_operation(apply=lambda *_:self.fail())
        second=self.grant();self.assertGreater(second,first)
        with self.assertRaisesRegex(PolicyError,'grant_changed'):self.dispatch_operation(apply=lambda *_:self.fail())
        self.plan('fresh');calls=[]
        result=self.dispatch_operation('fresh',lambda kind,args:calls.append(kind) or {'verified':True})
        self.assertEqual(result['state'],'completed');self.assertEqual(len(calls),1)
        self.store.revoke(101)
        self.assertEqual(self.dispatch_operation('fresh',lambda *_:self.fail()),result)
        self.assertEqual(self.plan('fresh'),result)
        with self.assertRaisesRegex(PolicyError,'operation_identity_conflict'):
            self.store.plan(101,None,'fresh','configuration',{'changed':True})
    def test_conflicting_dispatch_and_revocation_during_inflight(self):
        self.grant();self.plan('a');self.plan('b');started=threading.Event();release=threading.Event();out=[]
        def apply(*_):started.set();release.wait(5);return {'verified':True}
        thread=threading.Thread(target=lambda:out.append(self.dispatch_operation('a',apply)));thread.start()
        try:
            self.assertTrue(started.wait(5))
            with self.assertRaisesRegex(PolicyError,'executor_busy'):self.dispatch_operation('b',lambda *_:self.fail())
            self.store.revoke(101)
            self.assertTrue(self.store.inspect(101,'a')['cancel_requested'])
        finally:release.set();thread.join(5)
        self.assertEqual(out[0]['state'],'completed')
        with self.assertRaisesRegex(PolicyError,'grant_required'):self.dispatch_operation('b',lambda *_:self.fail())
    def test_failed_effect_uncertain_never_replayed(self):
        self.grant();self.plan()
        def apply(*_):raise OSError('dummy-secret-must-not-export')
        with self.assertRaisesRegex(PolicyError,'operation_uncertain'):self.dispatch_operation(apply=apply)
        self.assertEqual(self.dispatch_operation(apply=lambda *_:self.fail())['state'],'uncertain')
        audit=json.dumps(self.store.audit(101))
        self.assertNotIn('dummy-secret',audit);self.assertNotIn('private dummy',audit)
        self.assertEqual(self.store.audit(102),[])
    def test_actual_process_loss_recovery_no_replay(self):
        # Real process loss after an observable effect and before terminal record.
        store=Store(self.path);store.set_grant(101,'standing',expires=__import__('time').time()+60)
        store.plan(101,None,'crash','configuration',{'synthetic':'input'})
        marker=Path(self.temp.name)/'effect'
        process=multiprocessing.Process(target=interrupted,args=(str(self.path),str(marker)));process.start()
        try:
            import time
            deadline=time.monotonic()+5
            while not marker.exists() and time.monotonic()<deadline:time.sleep(.01)
            self.assertTrue(marker.exists());self.assertEqual(store.inspect(101,'crash')['state'],'running')
        finally:process.terminate();process.join(5)
        self.assertIsNotNone(process.exitcode);self.assertEqual(store.recover(),1);self.assertEqual(store.recover(),0)
        result=store.dispatch(101,None,'crash','configuration',{'synthetic':'input'},lambda *_:self.fail())
        self.assertEqual(result['state'],'uncertain');self.assertEqual(marker.read_text(),'effect happened')
    def test_cancel_before_dispatch_and_running_persists(self):
        self.grant();self.plan('before');self.store.revoke(101)
        canceled=self.store.cancel(101,'before');self.assertEqual(canceled['state'],'canceled')
        self.assertTrue(canceled['cancel_requested'])
        self.assertEqual(self.dispatch_operation('before',lambda *_:self.fail()),canceled)
        self.grant();self.plan('running')
        def apply(*_):
            with self.assertRaisesRegex(PolicyError,'operation_unknown'):self.store.cancel(102,'running')
            self.store.cancel(101,'running')
            self.assertTrue(Store(self.path).inspect(101,'running')['cancel_requested'])
            raise OSError('effect outcome requires verification')
        with self.assertRaisesRegex(PolicyError,'operation_uncertain'):self.dispatch_operation('running',apply)
        result=Store(self.path).inspect(101,'running');self.assertEqual(result['state'],'uncertain')
        self.assertTrue(result['cancel_requested'])
    def test_prior_store_migrates_without_losing_operation_identity(self):
        other=self.path.parent/'old';other.mkdir(mode=0o700)
        with sqlite3.connect(other/'state.sqlite') as db:
            db.execute('CREATE TABLE operations(id TEXT PRIMARY KEY,uid INTEGER NOT NULL,kind TEXT NOT NULL,input_hash TEXT NOT NULL,generation INTEGER NOT NULL,state TEXT NOT NULL,result TEXT,created REAL NOT NULL)')
            db.execute("INSERT INTO operations VALUES('old',101,'configuration','digest',1,'completed','{}',1000)")
        (other/'state.sqlite').chmod(0o600)
        migrated=Store(other);result=migrated.inspect(101,'old')
        self.assertEqual(result['state'],'completed');self.assertFalse(result['cancel_requested'])
    def test_strict_inputs_store_permissions_and_nonsecret_audit(self):
        with self.assertRaisesRegex(PolicyError,'invalid_owner'):self.store.revoke(True)
        with self.assertRaisesRegex(PolicyError,'invalid_grant'):self.store.set_grant(101,'standing',expires=float('nan'))
        with self.assertRaisesRegex(PolicyError,'invalid_identifier'):self.store.plan(101,None,'../x','configuration',{})
        self.grant();self.plan();self.dispatch_operation()
        text=json.dumps(self.store.audit(101));self.assertNotIn('private dummy',text)
        self.assertNotIn('input_hash',text);self.assertNotIn('result',text)
        with sqlite3.connect(self.path/'state.sqlite') as db:
            contents=str(list(db.iterdump()));self.assertNotIn('private dummy',contents)
        self.assertEqual((self.path/'state.sqlite').stat().st_mode&0o777,0o600)
        self.path.chmod(0o755)
        with self.assertRaisesRegex(PolicyError,'unsafe_store_directory'):Store(self.path)

if __name__=='__main__':unittest.main(verbosity=2)
