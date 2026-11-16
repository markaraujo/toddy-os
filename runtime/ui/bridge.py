"""Async same-user session-bus client with no automatic task resubmission."""
import json
import os
import uuid

import gi
gi.require_version('Gio','2.0')
from gi.repository import Gio, GLib

from .task_state import TaskState, TaskText, capabilities, body, REVISION

BUS = 'io.github.markaraujo.Toddy.Service'
OBJECT = '/io/github/markaraujo/Toddy/Service'
INTERFACE = BUS + '1'


class TaskClient:
    def __init__(self, changed):
        self.changed = changed
        self.state = TaskState()
        self.phase = 'absent'
        self.capabilities = None
        self.connection = None
        self.owner = None
        self.generation = 0
        self.subscription = None
        self.text_subscription = None
        self.text = None
        self.text_status = 'unavailable'
        self.text_fetching = False
        self.text_dirty = False
        self.text_generation = 0
        self.text_notice = None
        self.current_prompt = ''
        self.history = []
        self.profile = None
        self.profile_stage = None
        self.profile_status = 'unavailable'
        self.profile_edit_generation = 0
        self.pending = set()
        self.watch = Gio.bus_watch_name(Gio.BusType.SESSION, BUS, Gio.BusNameWatcherFlags.NONE,
                                        self._appeared, self._vanished)

    def close(self):
        self._detach()
        Gio.bus_unwatch_name(self.watch)

    def _detach(self):
        self.generation += 1
        if self.subscription is not None:
            self.connection.signal_unsubscribe(self.subscription)
            self.subscription = None
        if self.text_subscription is not None:
            self.connection.signal_unsubscribe(self.text_subscription)
            self.text_subscription = None
        if self.text_notice is not None:
            GLib.source_remove(self.text_notice)
            self.text_notice = None
        self.text_generation += 1
        self.text_fetching = False
        self.text_dirty = False
        self.profile_stage = None
        for cancellable in tuple(self.pending):
            cancellable.cancel()
        self.pending.clear()
        self.connection = None
        self.owner = None
        self.capabilities = None
        self.state.disconnected()

    def _appeared(self, connection, _name, owner):
        self._detach()
        self.connection, self.owner = connection, owner
        self.phase = 'connecting'
        self.changed()
        generation = self.generation

        def authenticated(conn, result, *_):
            if generation != self.generation:
                return
            try:
                if conn.call_finish(result).unpack()[0] != os.getuid():
                    raise ValueError('wrong_service_user')
                # Subscribe first, then read the snapshot after capabilities.
                self.subscription = conn.signal_subscribe(owner, INTERFACE, 'TaskChanged', OBJECT,
                    None, Gio.DBusSignalFlags.NONE, self._signal, None)
                self.text_subscription = conn.signal_subscribe(owner, INTERFACE, 'TaskTextChanged', OBJECT,
                    None, Gio.DBusSignalFlags.NONE, self._text_signal, None)
                self._call('GetCapabilities', None, self._capabilities)
            except (GLib.Error, ValueError):
                self.phase = 'unsupported'
                self.changed()

        connection.call('org.freedesktop.DBus', '/org/freedesktop/DBus',
                        'org.freedesktop.DBus', 'GetConnectionUnixUser', GLib.Variant('(s)', (owner,)),
                        GLib.VariantType('(u)'), Gio.DBusCallFlags.NO_AUTO_START, 3000, None,
                        authenticated, None)

    def _vanished(self, *_):
        self._detach()
        self.phase = 'absent'
        self.changed()

    def _call(self, method, parameters, completed, failed=None):
        if self.connection is None or self.owner is None:
            self.phase = 'absent'
            self.changed()
            return
        generation = self.generation
        cancel = Gio.Cancellable()
        self.pending.add(cancel)

        def finished(conn, result, *_):
            self.pending.discard(cancel)
            if generation != self.generation:
                return
            try:
                completed(conn.call_finish(result).unpack()[0])
            except (GLib.Error, ValueError, TypeError):
                if failed is not None:
                    failed('operation_failed')
                else:
                    self.state.disconnected()
                    self.phase = 'error'
            self.changed()

        self.connection.call(self.owner, OBJECT, INTERFACE, method, parameters,
            GLib.VariantType('(s)'), Gio.DBusCallFlags.NO_AUTO_START, 5000, cancel, finished, None)

    def _capabilities(self, data):
        self.capabilities = capabilities(data)
        self.phase = 'ready'
        if self.state.task_id is not None:
            self.refresh()
            self.refresh_text()
        if 'profile-settings-v1' in self.capabilities['features']:
            self.refresh_profile()

    def recheck(self):
        """Explicit read-only recovery; an unknown submission is never replayed."""
        if self.connection is not None and self.owner is not None:
            self.phase = 'connecting'
            self._call('GetCapabilities', None, self._capabilities)
            self.changed()

    def refresh(self):
        if self.phase == 'ready' and self.state.task_id is not None:
            task_id=self.state.task_id
            self._call('GetTask', GLib.Variant('(s)', (task_id,)),
                       lambda data:self._observe_task(task_id,data))

    def submit_system_info(self, note):
        if self.phase != 'ready' or self.capabilities is None or \
                'system-info' not in self.capabilities['tools'] or \
                not isinstance(note, str) or len(note.encode('utf-8')) > 16384:
            raise ValueError('task_unavailable')
        self._submit(note,{'version':1,'text':note,'tool':{'kind':'system-info','arguments':{}}})

    def _submit(self, prompt, request):
        previous=self.text
        previous_prompt=self.current_prompt
        previous_snapshot=self.state.snapshot
        self.state.begin_submit()
        if previous is not None and previous_snapshot is not None:
            self.history.append({'task_id':previous.task_id,'prompt':previous_prompt,
                                 'text':previous.text,'state':previous_snapshot['state']})
            self.history=self.history[-8:]
        self.text=None
        self.text_generation+=1
        self.text_fetching=False
        self.text_dirty=False
        self.current_prompt=prompt
        self.state.profile_revision=self.capabilities['profile_revision']
        payload=json.dumps(request,ensure_ascii=False,separators=(',',':'),allow_nan=False)
        def accepted(task_id):
            self.state.submitted(task_id)
            self.text=TaskText(task_id)
            self.refresh()
            self.refresh_text()
        self._call('SubmitTask',GLib.Variant('(ssss)',(uuid.uuid4().hex,
            self.capabilities['profile_id'],self.capabilities['profile_revision'],payload)),accepted)
        self.changed()

    def submit_text(self,text,*,remote_consent=False):
        if self.phase!='ready' or self.capabilities is None or \
                self.capabilities.get('agent_backend') is not True or \
                'agent-text-v1' not in self.capabilities['features'] or \
                not isinstance(text,str) or not 0<len(text.encode('utf-8'))<=16384 or \
                type(remote_consent) is not bool:
            raise ValueError('conversation_unavailable')
        mode=self.capabilities.get('provider_mode','deferred')
        if mode not in ('local','remote') or (mode=='remote' and not remote_consent):
            raise ValueError('remote_consent_required')
        self._submit(text,{'version':1,'text':text,'agent':True,
                           'remote_consent':remote_consent if mode=='remote' else False})

    def _notify_text(self):
        if self.text_notice is None:
            def notify():
                self.text_notice=None
                self.changed()
                return False
            self.text_notice=GLib.timeout_add(100,notify)

    def refresh_text(self):
        if self.phase!='ready' or self.state.task_id is None or self.capabilities is None or \
                'agent-text-v1' not in self.capabilities['features']:
            return
        if self.text_fetching:
            self.text_dirty=True
            return
        if self.text is None or self.text.task_id!=self.state.task_id:
            self.text=TaskText(self.state.task_id)
        self.text_fetching=True
        self.text_status='loading'
        task_id=self.state.task_id
        generation=self.text_generation
        def received(data):
            if generation!=self.text_generation:
                return
            self.text_fetching=False
            if self.state.task_id!=task_id:
                return
            more=self.text.observe(data)
            self.text_status='ready'
            dirty=self.text_dirty
            self.text_dirty=False
            self._notify_text()
            if more or dirty:
                self.refresh_text()
        def failed(_code):
            if generation==self.text_generation:
                self.text_fetching=False
                self.text_status='failed'
        self._call('GetTaskText',GLib.Variant('(st)',(task_id,self.text.sequence)),received,failed)

    def _text_signal(self,_conn,sender,_path,_interface,_name,parameters,*_):
        if sender!=self.owner or self.state.task_id is None:
            return
        task_id,sequence=parameters.unpack()
        if task_id==self.state.task_id and (self.text is None or sequence>self.text.sequence):
            self.refresh_text()

    def refresh_profile(self):
        if self.phase!='ready' or 'profile-settings-v1' not in self.capabilities['features']:
            return
        self.profile_stage=None
        self.profile_edit_generation+=1
        def received(data):
            value=body(data,131072)
            if not isinstance(value.get('config'),dict) or \
                    not isinstance(value.get('profile_revision'),str) or not REVISION.fullmatch(value['profile_revision']) or \
                    not isinstance(value.get('previous_revisions'),list) or len(value['previous_revisions'])>32 or \
                    any(not isinstance(revision,str) or not REVISION.fullmatch(revision)
                        for revision in value['previous_revisions']):
                raise ValueError('invalid_profile_response')
            self.profile=value
            self.profile_status='loaded'
        self._call('GetProfileConfig',GLib.Variant('(s)',(self.capabilities['profile_id'],)),received,self._profile_failed)

    def _profile_failed(self,_code):
        self.profile_stage=None
        self.profile_status='failed'

    def invalidate_profile_stage(self):
        self.profile_edit_generation+=1
        self.profile_stage=None
        if self.profile is not None:
            self.profile_status='editing'

    def validate_profile(self,encoded):
        if self.phase!='ready' or self.profile is None or not isinstance(encoded,str) or len(encoded.encode())>65536:
            raise ValueError('profile_unavailable')
        expected=self.profile['profile_revision']
        edit_generation=self.profile_edit_generation
        def received(data):
            if edit_generation!=self.profile_edit_generation:
                return
            value=body(data,32768)
            if value.get('valid') is not True or not isinstance(value.get('validated_revision'),str) or \
                    not 0<len(value['validated_revision'])<=128 or \
                    not isinstance(value.get('profile_revision'),str) or not REVISION.fullmatch(value['profile_revision']):
                raise ValueError('invalid_profile_stage')
            self.profile_stage={'token':value['validated_revision'],'expected':expected}
            self.profile_status='validated'
        self.profile_stage=None
        self._call('ValidateProfile',GLib.Variant('(sss)',(self.capabilities['profile_id'],expected,encoded)),
                   received,self._profile_failed)

    def apply_profile(self):
        if self.phase!='ready' or self.profile_stage is None:
            raise ValueError('profile_not_validated')
        stage=self.profile_stage
        self.profile_stage=None
        def received(data):
            value=body(data,32768)
            if value.get('applied') is not True:
                raise ValueError('profile_apply_failed')
            self.recheck()
        self._call('ApplyProfile',GLib.Variant('(sss)',(self.capabilities['profile_id'],stage['expected'],stage['token'])),
                   received,self._profile_failed)

    def restore_profile(self,revision):
        if self.phase!='ready' or self.profile is None or revision not in self.profile['previous_revisions']:
            raise ValueError('profile_restore_unavailable')
        expected=self.profile['profile_revision']
        self.profile_stage=None
        def received(data):
            value=body(data,32768)
            if value.get('restored') is not True:
                raise ValueError('profile_restore_failed')
            self.recheck()
        self._call('RestoreProfile',GLib.Variant('(sss)',(self.capabilities['profile_id'],expected,revision)),
                   received,self._profile_failed)

    def stop(self):
        if self.phase not in ('ready','error') or self.state.task_id is None or self.owner is None:
            raise ValueError('task_unavailable')
        task_id=self.state.task_id
        self._call('RequestCancel', GLib.Variant('(ss)', (task_id,uuid.uuid4().hex)),
                   lambda data:self._observe_task(task_id,data))

    def _observe_task(self,task_id,data):
        if task_id==self.state.task_id:
            self.state.observe(data)

    def _signal(self, _conn, sender, _path, _interface, _name, parameters, *_):
        if sender != self.owner or self.state.task_id is None:
            return
        task_id, _sequence, data = parameters.unpack()
        if task_id != self.state.task_id:
            return
        try:
            if self.state.observe(data, signal=True) == 'gap':
                self.refresh()
            self.refresh_text()
        except (ValueError, TypeError):
            self.phase = 'error'
        self.changed()
