"""Explicit local voice UI; optional engine absence preserves ordinary typed text."""
import gi
gi.require_version('Gtk','4.0')
from gi.repository import Gtk,GLib,Gdk


class VoicePanel(Gtk.Box):
    def __init__(self,window,*,controller_factory=None):
        super().__init__(orientation=Gtk.Orientation.VERTICAL,spacing=10)
        self.window=window;self.text=window.model.text;self.catalog=None;self.devices=[];self.closed=False;self._holding=False
        self.status=Gtk.Label(label=self.text('voice.unavailable'),wrap=True,xalign=0)
        self.status.set_accessible_role(Gtk.AccessibleRole.STATUS);self.append(self.status)
        self.append(Gtk.Label(label=self.text('voice.notice'),wrap=True,xalign=0))
        self.refresh=Gtk.Button(label=self.text('voice.refresh'));self.refresh.connect('clicked',self._refresh);self.append(self.refresh)
        self.licenses=Gtk.TextView(editable=False,cursor_visible=False,wrap_mode=Gtk.WrapMode.WORD_CHAR)
        scroll=Gtk.ScrolledWindow(min_content_height=80,max_content_height=180);scroll.set_child(self.licenses)
        notices=Gtk.Expander(label=self.text('voice.licenses'));notices.set_child(scroll);self.append(notices)
        self.consent=Gtk.CheckButton(label=self.text('voice.consent'));self.consent.connect('toggled',lambda *_:self._controls());self.append(self.consent)
        self.device_refresh=Gtk.Button(label=self.text('voice.devices'));self.device_refresh.connect('clicked',self._devices);self.append(self.device_refresh)
        self.input=Gtk.DropDown.new_from_strings([self.text('voice.choose_input')]);self.input.set_enable_search(True)
        self.output=Gtk.DropDown.new_from_strings([self.text('voice.choose_output')]);self.output.set_enable_search(True)
        self.input.connect('notify::selected',lambda *_:self._controls());self.output.connect('notify::selected',lambda *_:self._controls())
        self.append(self.input);self.append(self.output)
        self.language=Gtk.DropDown.new_from_strings(['English','Português brasileiro'])
        self.language.set_selected(1 if window.model.locale=='pt-BR' else 0);self.append(self.language)
        self.record=Gtk.Button(label=self.text('voice.hold'));self.record.set_tooltip_text(self.text('voice.hold_notice'))
        gesture=Gtk.GestureClick.new();gesture.connect('pressed',self._press);gesture.connect('released',lambda *_:self._release());self.record.add_controller(gesture)
        keys=Gtk.EventControllerKey.new();keys.connect('key-pressed',self._key_press);keys.connect('key-released',self._key_release);self.record.add_controller(keys)
        self.append(self.record)
        self.stop_button=Gtk.Button(label=self.text('voice.stop'));self.stop_button.connect('clicked',lambda *_:self.stop());self.append(self.stop_button)
        self.append(Gtk.Label(label=self.text('voice.review'),wrap=True,xalign=0))
        self.review=Gtk.TextView(wrap_mode=Gtk.WrapMode.WORD_CHAR);self.review.get_buffer().connect('changed',lambda *_:self._controls())
        scroll=Gtk.ScrolledWindow(min_content_height=70,max_content_height=150);scroll.set_child(self.review);self.append(scroll)
        self.insert=Gtk.Button(label=self.text('voice.insert'));self.insert.connect('clicked',self._insert);self.append(self.insert)
        self.speech=Gtk.Entry(placeholder_text=self.text('voice.speech_text'),max_length=4096)
        self.speech.connect('changed',lambda *_:self._controls());self.append(self.speech)
        self.reply=Gtk.Button(label=self.text('voice.use_reply'));self.reply.connect('clicked',self._reply);self.append(self.reply)
        self.speak=Gtk.Button(label=self.text('voice.speak'));self.speak.connect('clicked',self._speak);self.append(self.speak)
        try:
            if controller_factory is None:
                from ..voice.controller import VoiceController
                controller_factory=VoiceController
            self.controller=controller_factory(self._event,GLib.idle_add)
        except ImportError:self.controller=None
        self._controls()

    def _review(self):
        buffer=self.review.get_buffer();start,end=buffer.get_bounds()
        return buffer.get_text(start,end,True).strip()

    def _selected(self,direction):
        candidates=[row for row in self.devices if row['direction']==direction]
        index=(self.input if direction=='input' else self.output).get_selected()
        return candidates[index-1] if 1<=index<=len(candidates) else None

    def _controls(self):
        if not hasattr(self,'controller'):return
        busy=bool(self.controller and self.controller.busy)
        available=bool(self.controller and self.controller.profile and not self.closed)
        accepted=bool(available and self.catalog and self.consent.get_active())
        self.refresh.set_sensitive(available and not busy)
        self.consent.set_sensitive(bool(available and self.catalog and not busy))
        self.device_refresh.set_sensitive(accepted and not busy)
        self.input.set_sensitive(accepted and not busy);self.output.set_sensitive(accepted and not busy)
        self.language.set_sensitive(not busy)
        self.record.set_sensitive(bool(accepted and self._selected('input') and (not busy or self._holding)))
        self.stop_button.set_sensitive(busy)
        self.speak.set_sensitive(bool(accepted and not busy and self._selected('output') and self.speech.get_text().strip()))
        self.insert.set_sensitive(bool(available and not busy and self._review() and self.window.entry.get_sensitive()))
        client=self.window.client
        self.reply.set_sensitive(bool(not busy and client.text and client.text.text and client.task_profile_id==(client.capabilities or {}).get('profile_id')))

    def sync(self):
        if self.controller:
            profile=(self.window.client.capabilities or {}).get('profile_id')
            if self.controller.bind(profile):
                self._holding=False
                self.catalog=None;self.devices=[];self.consent.set_active(False)
                self.review.get_buffer().set_text('');self.speech.set_text('');self.licenses.get_buffer().set_text('')
                self.input.set_model(Gtk.StringList.new([self.text('voice.choose_input')]))
                self.output.set_model(Gtk.StringList.new([self.text('voice.choose_output')]))
                self.status.set_text(self.text('voice.unavailable'))
        self._controls()

    def _request(self,operation,**kwargs):
        try:
            self.controller.request(operation,**kwargs);self._controls()
        except (ValueError,RuntimeError,AttributeError):self.status.set_text(self.text('voice.failed'))

    def _refresh(self,*_):self._request('inspect')
    def _devices(self,*_):
        if self.catalog and self.consent.get_active():self._request('devices',accepted_pin=self.catalog['catalog_pin'])
    def _press(self,*_):
        if self.record.get_sensitive() and not self._holding:
            self._holding=True
            self._request('capture',accepted_pin=self.catalog['catalog_pin'],language=self._language(),device=self._selected('input'))
    def _release(self):
        if self._holding and self.controller:self.controller.release_microphone()
        self._holding=False;self._controls()
    def _key_press(self,_controller,key,*_):
        if key in (Gdk.KEY_space,Gdk.KEY_Return):self._press();return True
        return False
    def _key_release(self,_controller,key,*_):
        if key in (Gdk.KEY_space,Gdk.KEY_Return):self._release()
    def _language(self):return 'pt-BR' if self.language.get_selected()==1 else 'en'
    def stop(self):
        self._holding=False
        if self.controller:self.controller.stop()
        self._controls()
    def close(self):
        self.closed=True
        if self.controller:self.controller.close()

    def _event(self,event,data):
        if event=='catalog':
            self.catalog=data;self.consent.set_active(False)
            summary='\n'.join(self.text('voice.role.'+row['role'])+': '+row['version']+' / '+row['license_id'] for row in data['artifacts'])
            notices='\n\n'.join(row['license_id']+'\n'+row['source_url']+'\n'+row['text'] for row in data['notices'])
            self.licenses.get_buffer().set_text(summary+'\n\n'+notices)
            self.status.set_text(self.text('voice.ready'))
        elif event=='devices':
            self.devices=data
            self.input.set_model(Gtk.StringList.new([self.text('voice.choose_input')]+[r['label'] for r in data if r['direction']=='input']))
            self.output.set_model(Gtk.StringList.new([self.text('voice.choose_output')]+[r['label'] for r in data if r['direction']=='output']))
            self.input.set_selected(0);self.output.set_selected(0)
            self.status.set_text(self.text('voice.devices_ready'))
        elif event=='transcript':
            if data.get('requires_review') is True and data.get('untrusted') is True:
                self.review.get_buffer().set_text(data['text']);self.status.set_text(self.text('voice.review'))
        elif event=='spoken':self.status.set_text(self.text('voice.complete'))
        elif event=='state':self.status.set_text(self.text('voice.state.'+data))
        elif event=='error':self.status.set_text(self.text('voice.canceled' if data=='canceled' else 'voice.failed'))
        self._controls()

    def _insert(self,*_):
        text=self._review();draft=self.window.entry.get_text();combined=(draft+' '+text).strip()
        if not text or len(combined)>4096 or len(combined.encode())>16384:
            self.status.set_text(self.text('voice.too_long'));return
        # Review/insert is separate from ordinary Send and per-request consent.
        self.window.remote_consent.set_active(False)
        self.window.entry.set_text(combined);self.window.entry.grab_focus()
        self.review.get_buffer().set_text('')

    def _reply(self,*_):
        client=self.window.client
        if client.text and client.task_profile_id==(client.capabilities or {}).get('profile_id'):
            text=client.text.text
            if len(text)>4096 or len(text.encode())>16384:
                self.status.set_text(self.text('voice.too_long'));return
            self.speech.set_text(text)
    def _speak(self,*_):
        if self.speak.get_sensitive():
            self._request('speak',accepted_pin=self.catalog['catalog_pin'],language=self._language(),
                device=self._selected('output'),text=self.speech.get_text())
