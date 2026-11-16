"""One explicit worker voice action; UI dispatch/profile scope never submits a task."""
from concurrent.futures import ThreadPoolExecutor
import threading
from .artifacts import VoiceError
from .catalog import NativeVoiceCatalog


class VoiceController:
    def __init__(self,changed,dispatch,*,catalog_factory=NativeVoiceCatalog):
        self.changed,self.dispatch,self.catalog_factory=changed,dispatch,catalog_factory
        self.pool=ThreadPoolExecutor(max_workers=1,thread_name_prefix='toddy-voice')
        self.lock=threading.RLock();self.cancel=threading.Event();self.session=None
        self.profile=None;self.generation=0;self.busy=False;self.closed=False

    def _publish(self,generation,event,data=None):
        def deliver():
            if not self.closed and generation==self.generation:self.changed(event,data)
            return False
        self.dispatch(deliver)

    def bind(self,profile):
        if profile!=self.profile:
            self.stop()
            with self.lock:self.profile=profile;self.generation+=1
            return True
        return False

    def request(self,operation,*,accepted_pin=None,language='en',device=None,text=None):
        with self.lock:
            if self.closed or self.busy or self.profile is None:raise VoiceError('voice_busy_or_profile_unavailable')
            if operation not in ('inspect','devices','capture','speak'):raise VoiceError('voice_operation_unavailable')
            self.cancel.clear()  # Only this explicit new UI action arms work.
            self.busy=True;generation=self.generation
        try:
            self._publish(generation,'state','loading')
            self.pool.submit(self._work,generation,operation,accepted_pin,language,device,text)
        except Exception:
            self.cancel.set()
            with self.lock:self.busy=False
            raise VoiceError('voice_observer_unavailable') from None

    def _work(self,generation,operation,pin,language,device,text):
        try:
            catalog=self.catalog_factory()
            if self.cancel.is_set():raise VoiceError('canceled')
            if operation=='inspect':
                self._publish(generation,'catalog',catalog.preview())
            elif operation=='devices':
                self._publish(generation,'devices',catalog.devices(accepted_pin=pin,cancel=self.cancel))
            else:
                if not isinstance(device,dict) or set(device)!={'direction','target','label'}:
                    raise VoiceError('voice_device_selection_required')
                direction='input' if operation=='capture' else 'output'
                # Bind object.serial from an actual current PipeWire graph. No
                # default/auto routing or stale recycled graph node ID is used.
                actual=catalog.devices(accepted_pin=pin,cancel=self.cancel)
                if device['direction']!=direction or not any(row['direction']==direction and row['target']==device['target'] for row in actual):
                    raise VoiceError('voice_device_selection_changed')
                session=catalog.session(accepted_pin=pin,changed=lambda state:self._publish(generation,'state',state))
                with self.lock:
                    self.session=session
                    if self.cancel.is_set():session.stop()
                if operation=='capture':
                    result=session.push_to_talk(language,device['target'])
                    if self.cancel.is_set():raise VoiceError('canceled')
                    self._publish(generation,'transcript',result)
                else:
                    result=session.speak(text,language,device['target'],play=True)
                    if self.cancel.is_set():raise VoiceError('canceled')
                    self._publish(generation,'spoken',result)
        except Exception as exc:
            code=str(exc) if isinstance(exc,VoiceError) else 'voice_unavailable'
            # Only fixed state codes cross to GTK. No raw engine diagnostics,
            # personal transcript, device graph or exception text is logged.
            self._publish(generation,'error','canceled' if code=='canceled' else 'voice_unavailable')
        finally:
            with self.lock:self.session=None;self.busy=False
            self._publish(generation,'idle')

    def release_microphone(self):
        with self.lock:
            if self.session is None or self.session.state!='recording':
                # A quick release while loading must not start a later capture.
                self.cancel.set()
                if self.session is not None:self.session.stop()
            else:self.session.release_microphone()

    def stop(self):
        self.cancel.set()
        with self.lock:
            if self.session is not None:self.session.stop()

    def close(self):
        self.stop();self.closed=True;self.generation+=1
        self.pool.shutdown(wait=False,cancel_futures=True)
