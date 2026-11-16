"""Actual EN/PT GTK widgets with synthetic non-audio controller; no device call."""
import json
import sys
import tempfile
import threading
import time
from pathlib import Path
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
import gi
gi.require_version('Gtk','4.0')
from gi.repository import Gtk,GLib
from runtime.ui.voice import VoicePanel
from runtime.ui.model import SetupModel
from runtime.voice.controller import VoiceController

Gtk.init()

def until(check):
    deadline=time.monotonic()+3
    while time.monotonic()<deadline:
        while GLib.MainContext.default().pending():GLib.MainContext.default().iteration(False)
        if check():return
        time.sleep(.005)
    raise AssertionError('GTK voice fixture deadline')

for locale in ('en','pt-BR'):
    with tempfile.TemporaryDirectory() as directory:
        model=SetupModel(ROOT,Path(directory)/'setup',locale)
        entry=Gtk.Entry();entry.set_text('Existing owner draft.');consent=Gtk.CheckButton();consent.set_active(True)
        client=SimpleNamespace(capabilities={'profile_id':'first'},task_profile_id='first',text=SimpleNamespace(text='Visible reply.'))
        window=SimpleNamespace(model=model,entry=entry,remote_consent=consent,client=client)
        entered,release=threading.Event(),threading.Event()
        class Session:
            state='idle'
            def stop(self):self.state='canceled';release.set()
            def release_microphone(self):release.set()
            def push_to_talk(self,language,device):
                self.state='recording';entered.set()
                if not release.wait(3):raise AssertionError('GTK fixture not released')
                return {'text':'Explicit GTK transcript fixture.','requires_review':True,'untrusted':True}
        class Catalog:
            def preview(self):return {'catalog_pin':'a'*64,'artifacts':[],'notices':[]}
            def devices(self,**kwargs):return [{'direction':'input','target':'42','label':'Fixture input'},
                {'direction':'output','target':'43','label':'Fixture output'}]
            def session(self,**kwargs):return Session()
        panel=VoicePanel(window,controller_factory=lambda changed,dispatch:VoiceController(changed,dispatch,catalog_factory=Catalog))
        try:
            panel.sync();panel._refresh();until(lambda:not panel.controller.busy and panel.catalog is not None)
            panel.consent.set_active(True);panel._devices();until(lambda:not panel.controller.busy and bool(panel.devices))
            assert panel.input.get_selected()==0 and not panel.record.get_sensitive()
            panel.input.set_selected(1);panel.output.set_selected(1)
            panel._press();until(lambda:entered.is_set())
            # Disabling a held widget would lose its release event and leave
            # capture active. It must stay sensitive until explicit release.
            assert panel.record.get_sensitive() and panel.stop_button.get_sensitive()
            panel._release();until(lambda:not panel.controller.busy and bool(panel._review()))
            panel._insert();assert entry.get_text()=='Existing owner draft. Explicit GTK transcript fixture.'
            assert not consent.get_active() and not panel._review()
            panel.review.get_buffer().set_text('x'*5000);old=entry.get_text();panel._insert();assert entry.get_text()==old
            client.capabilities={'profile_id':'second'};panel.sync()
            assert not panel._review() and panel.catalog is None and not panel.consent.get_active()
            assert panel.refresh.get_sensitive()
        finally:panel.close();model.close()
print(json.dumps({'scope':'actual GTK EN/PT widgets with synthetic non-audio controller only',
    'press_release_stop_controls':True,'explicit_devices':True,'review_draft_without_submit':True,
    'no_silent_truncation':True,'profile_switch_clears_review':True}))
