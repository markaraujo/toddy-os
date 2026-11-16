"""No provider/keyring/model: bounded explicit onboarding orchestration."""
import queue
import threading
import unittest

from runtime.ui.onboarding import OnboardingController
from runtime.setup.pending import SetupError


class OnboardingControllerTests(unittest.TestCase):
    def setUp(self):
        self.queue=queue.Queue();self.controller=OnboardingController(None,lambda:None,api=object(),local=object(),schedule=lambda fn,*args:self.queue.put((fn,args)))
        self.addCleanup(lambda:self.controller.pool.shutdown(wait=True))
    def tick(self):
        fn,args=self.queue.get(timeout=2);fn(*args)
    def test_only_explicit_worker_action_and_no_duplicate_operation(self):
        calls=[];started=threading.Event();release=threading.Event()
        def work():
            calls.append('bind');started.set();release.wait(2);return {'state':'configured'}
        self.assertEqual(calls,[]);self.controller.start('remote',work);self.assertTrue(started.wait(1))
        self.assertFalse(self.controller.close())
        with self.assertRaisesRegex(SetupError,'busy'):self.controller.start('remote',work)
        release.set();self.tick();self.assertEqual(calls,['bind']);self.assertTrue(self.controller.close())
    def test_explicit_download_stop_is_cooperative_and_progress_coalesced(self):
        started=threading.Event()
        def work():
            started.set();self.controller.cancel.wait(2);return {'state':'canceled'}
        self.controller.start('download',work);self.assertTrue(started.wait(1))
        for n in range(100):self.controller.downloading(n,100)
        self.assertEqual(self.queue.qsize(),1)
        self.controller.stop();self.tick();self.tick();self.assertEqual(self.controller.status,'canceled')
    def test_errors_never_expose_raw_private_diagnostics(self):
        def failed():raise OSError('secret raw provider data')
        self.controller.start('remote',failed);self.tick()
        self.assertEqual(self.controller.result,{'state':'unavailable'})
