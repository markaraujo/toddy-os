"""Explicit voice worker/profile/Stop scope using synthetic non-audio callbacks."""
import threading
import time
import unittest
from unittest.mock import patch
from runtime.voice.controller import VoiceController
from runtime.voice.artifacts import VoiceError
from runtime.voice.catalog import NativeVoiceCatalog


class ControllerTests(unittest.TestCase):
    def setUp(self):
        self.events=[];self.called=[];self.entered=threading.Event();self.release=threading.Event();self.hold=False
        self.pin='a'*64;parent=self
        class Session:
            state='idle'
            def stop(self):self.state='canceled';parent.called.append('stop');parent.release.set()
            def push_to_talk(self,language,device):
                parent.called.append(('capture',language,device));self.state='recording';parent.entered.set()
                if not parent.release.wait(3):raise AssertionError('fixture not released')
                if self.state=='canceled':raise VoiceError('canceled')
                return {'text':'Explicit synthetic controller fixture.','untrusted':True,'requires_review':True}
            def release_microphone(self):parent.release.set()
            def speak(self,text,language,device,play):
                parent.called.append(('speak',text,language,device));return {'text_available':True}
        class Catalog:
            def preview(self):
                parent.called.append('inspect')
                if parent.hold:
                    parent.entered.set();parent.release.wait(3)
                return {'catalog_pin':parent.pin}
            def devices(self,*,accepted_pin,cancel):
                if accepted_pin!=parent.pin:raise VoiceError('changed')
                parent.called.append('devices')
                return [{'direction':'input','target':'42','label':'Fixture microphone'},
                        {'direction':'output','target':'43','label':'Fixture speaker'}]
            def session(self,*,accepted_pin,changed):
                if accepted_pin!=parent.pin:raise VoiceError('changed')
                parent.called.append('session');return Session()
        self.controller=VoiceController(lambda event,data:self.events.append((event,data)),lambda fn:fn(),catalog_factory=Catalog)
        self.addCleanup(self.controller.close);self.controller.bind('first')
    def until_idle(self):
        deadline=time.monotonic()+3
        while self.controller.busy:
            if time.monotonic()>deadline:raise AssertionError('voice fixture deadline')
            time.sleep(.005)
    def test_nothing_starts_implicitly_and_capture_returns_only_reviewable_text(self):
        self.assertEqual(self.called,[])
        self.controller.request('inspect');self.until_idle();self.assertEqual(self.called,['inspect'])
        self.controller.request('capture',accepted_pin=self.pin,language='pt-BR',
            device={'direction':'input','target':'42','label':'Fixture microphone'})
        self.assertTrue(self.entered.wait(3));self.controller.release_microphone();self.until_idle()
        transcript=next(data for event,data in self.events if event=='transcript')
        self.assertTrue(transcript['requires_review']);self.assertTrue(transcript['untrusted'])
        self.assertIn(('capture','pt-BR','42'),self.called)
    def test_stale_device_or_license_does_not_open_capture(self):
        self.controller.request('capture',accepted_pin=self.pin,
            device={'direction':'input','target':'99','label':'Old microphone'})
        self.until_idle();self.assertNotIn('session',self.called)
        self.controller.request('devices',accepted_pin='b'*64);self.until_idle()
        self.assertFalse(any(isinstance(row,tuple) and row[0]=='capture' for row in self.called))
    def test_profile_switch_stops_and_discards_old_transcript(self):
        self.controller.request('capture',accepted_pin=self.pin,
            device={'direction':'input','target':'42','label':'Fixture microphone'})
        self.assertTrue(self.entered.wait(3));self.controller.bind('second');self.until_idle()
        self.assertIn('stop',self.called);self.assertFalse(any(event=='transcript' for event,_ in self.events))
    def test_stop_while_loading_cannot_clear_into_a_queued_capture(self):
        self.hold=True;self.controller.request('inspect');self.assertTrue(self.entered.wait(3))
        self.controller.release_microphone();self.release.set();self.until_idle()
        self.assertTrue(self.controller.cancel.is_set());self.assertNotIn('session',self.called)
    def test_failed_ui_dispatch_cannot_arm_or_start_capture(self):
        self.controller.dispatch=lambda *_:(_ for _ in ()).throw(RuntimeError('private UI diagnostic'))
        with self.assertRaisesRegex(VoiceError,'observer_unavailable'):
            self.controller.request('capture',accepted_pin=self.pin,
                device={'direction':'input','target':'42','label':'Fixture microphone'})
        self.assertFalse(self.controller.busy);self.assertTrue(self.controller.cancel.is_set())
        self.assertEqual(self.called,[])
    def test_native_catalog_is_optional_and_cannot_be_armed_by_missing_metadata(self):
        with patch('runtime.voice.catalog.root_read',side_effect=FileNotFoundError), self.assertRaises(VoiceError):NativeVoiceCatalog()


if __name__=='__main__':unittest.main()
