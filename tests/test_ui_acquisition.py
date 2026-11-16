"""Bounded UI orchestration fixtures; no actual Polkit/package/provider effects."""
import queue
import threading
import unittest

from runtime.setup.pending import SetupError
from runtime.ui.acquisition import AcquisitionController


class FakeClient:
    def __init__(self):self.calls=[];self.release=threading.Event();self.started=threading.Event()
    def review(self,identity):
        self.calls.append(('review',identity));return {'state':'review_required','can_install':True,'release_id':identity}
    def install(self,review,*,accepted_terms):
        self.calls.append(('install',review['release_id'],accepted_terms));self.started.set()
        if not self.release.wait(3):raise AssertionError('test did not release simulated native transaction')
        return {'ok':True,'state':'installed'}
    def action(self,action):self.calls.append((action,));return {'ok':True,'state':'installed'}
    def request_cancel(self):self.calls.append(('cancel',));return {'ok':True,'cancellation_requested':True}


class AcquisitionUITests(unittest.TestCase):
    def setUp(self):
        self.events=queue.Queue();self.client=FakeClient();self.changed=0
        self.controller=AcquisitionController(None,self.change,client=self.client,schedule=lambda fn,*args:self.events.put((fn,args)))
        self.addCleanup(self.cleanup)
    def cleanup(self):
        self.client.release.set()
        self.controller.pool.shutdown(wait=True);self.controller.cancel_pool.shutdown(wait=True)
    def change(self):self.changed+=1
    def tick(self):
        fn,args=self.events.get(timeout=3);fn(*args)
    def review(self):self.controller.inspect('agent-local');self.tick()
    def test_no_automatic_review_network_or_install_and_consent_required(self):
        self.assertEqual(self.client.calls,[])
        self.review()
        with self.assertRaisesRegex(SetupError,'review_required'):self.controller.install(accepted_terms=False)
        self.assertEqual(self.client.calls,[('review','agent-local')])
    def test_one_writer_explicit_stop_and_close_waits_for_safe_completion(self):
        self.review();self.controller.install(accepted_terms=True);self.assertTrue(self.client.started.wait(2))
        self.assertFalse(self.controller.close())
        with self.assertRaisesRegex(SetupError,'busy'):self.controller.action('status')
        self.controller.stop()
        with self.assertRaisesRegex(SetupError,'busy'):self.controller.stop()
        self.tick();self.assertEqual(self.controller.cancel_status,'stop_requested')
        self.client.release.set();self.tick()
        self.assertEqual(self.controller.status,'installed');self.assertTrue(self.controller.close())
        self.assertEqual(self.client.calls.count(('install','agent-local',True)),1)
    def test_lost_reply_holds_unknown_and_never_automatically_retries(self):
        self.review()
        def lost(*args,**kwargs):self.client.calls.append(('uncertain-install',));raise OSError('private raw diagnostics')
        self.client.install=lost
        self.controller.install(accepted_terms=True);self.tick()
        self.assertEqual(self.controller.status,'outcome_unknown')
        self.assertIsNone(self.controller.review)
        self.controller.action('status');self.tick()
        self.assertEqual(self.client.calls.count(('uncertain-install',)),1)
    def test_progress_is_coalesced_and_contains_only_phase(self):
        for n in range(1000):self.controller._progress({'phase':'verifying','diagnostic':'never expose'})
        self.assertEqual(self.events.qsize(),1);self.tick()
        self.assertEqual(self.controller.phase,'verifying')
