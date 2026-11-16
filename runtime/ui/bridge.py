"""Async same-user session-bus client with no automatic task resubmission."""
import json
import os
import re
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
        self.profile_list = None
        self.profile_action_status = 'unavailable'
        self.profile_mutating = False
        self.task_profile_id = None
        self.pending_request = None
        self.acceptance_lookup = None
        self.profile_subscription = None
        self.observed_profile_id = None
        self.observed_profile_revision = None
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
        if self.profile_subscription is not None:
            self.connection.signal_unsubscribe(self.profile_subscription)
            self.profile_subscription = None
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
        if self.profile_mutating:
            self.profile_action_status='unknown'
        self.profile_mutating=False
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
                self.profile_subscription = conn.signal_subscribe(owner, INTERFACE, 'ProfilesChanged', OBJECT,
                    None, Gio.DBusSignalFlags.NONE, self._profiles_signal, None)
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
        previous=self.observed_profile_id
        previous_revision=self.observed_profile_revision
        self.capabilities = capabilities(data)
        selected=self.capabilities['profile_id']
        self.observed_profile_id=selected
        self.observed_profile_revision=self.capabilities['profile_revision']
        if previous is not None and previous!=selected:
            self.profile=None
            self.profile_stage=None
            self.profile_edit_generation+=1
            self.history=[]
            if self.state.snapshot is not None and self.state.snapshot['state'] in {'completed','failed','canceled'} and not self.state.snapshot['result_uncertain']:
                self.state=TaskState()
                self.text=None
                self.text_generation+=1
                self.current_prompt=''
                self.task_profile_id=None
        self.phase = 'ready'
        if self.state.task_id is not None:
            self.refresh()
            self.refresh_text()
        if 'profile-settings-v1' in self.capabilities['features'] and (self.profile is None or
                previous!=selected or previous_revision!=self.capabilities['profile_revision']):
            self.refresh_profile()
        if 'named-profiles-v1' in self.capabilities['features']:
            self.refresh_profiles()
        if self.state.acceptance_uncertain and self.pending_request is not None:
            self.lookup_acceptance()

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
        if previous is not None and previous.history_enabled and previous_snapshot is not None:
            self.history.append({'task_id':previous.task_id,'prompt':previous_prompt,
                                 'text':previous.text,'state':previous_snapshot['state']})
            self.history=self.history[-8:]
        else:
            self.history=[]
        self.text=None
        self.text_generation+=1
        self.text_fetching=False
        self.text_dirty=False
        self.current_prompt=prompt
        self.state.profile_revision=self.capabilities['profile_revision']
        self.task_profile_id=self.capabilities['profile_id']
        self.state.profile_id=self.task_profile_id
        request_id=uuid.uuid4().hex
        self.pending_request={'request_id':request_id,'profile_id':self.task_profile_id,
                              'profile_revision':self.state.profile_revision}
        payload=json.dumps(request,ensure_ascii=False,separators=(',',':'),allow_nan=False)
        def accepted(task_id):
            self.state.submitted(task_id)
            self.pending_request=None
            self.text=TaskText(task_id)
            self.refresh()
            self.refresh_text()
        self._call('SubmitTask',GLib.Variant('(ssss)',(request_id,
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
        if self.text.cleanup_requested:
            return
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
            if not more and self.text.complete and not self.text.history_enabled:
                self._acknowledge_text(task_id)
            if more or dirty:
                self.refresh_text()
        def failed(_code):
            if generation==self.text_generation:
                self.text_fetching=False
                self.text_status='failed'
        self._call('GetTaskText',GLib.Variant('(st)',(task_id,self.text.sequence)),received,failed)

    def _acknowledge_text(self,task_id):
        if self.text is None or self.text.cleanup_requested or self.capabilities is None or \
                'agent-text-ack-v1' not in self.capabilities['features']:
            return
        current=self.text
        current.cleanup_requested=True
        def received(data):
            value=body(data,32768)
            if value.get('task_id')!=task_id or type(value.get('erased')) is not bool:
                raise ValueError('invalid_text_acknowledgement')
            current.cleanup_acknowledged=True
        # A lost acknowledgement never resubmits the task or automatically
        # repeats deletion. The broker's bounded transient retention still applies.
        self._call('AcknowledgeTaskText',GLib.Variant('(st)',(task_id,current.sequence)),
                   received,lambda _code:None)

    def _text_signal(self,_conn,sender,_path,_interface,_name,parameters,*_):
        if sender!=self.owner or self.state.task_id is None:
            return
        task_id,sequence=parameters.unpack()
        if task_id==self.state.task_id and (self.text is None or
                (not self.text.cleanup_requested and sequence>=self.text.sequence)):
            self.refresh_text()

    @staticmethod
    def _profile_id(value):
        if not isinstance(value,str) or not re.fullmatch(r'[a-z][a-z0-9-]{0,63}',value):
            raise ValueError('invalid_profile_id')
        return value

    def refresh_profiles(self):
        if self.phase!='ready' or 'named-profiles-v1' not in (self.capabilities or {}).get('features',[]):
            return
        def received(data):
            value=body(data,32768)
            if type(value.get('generation')) is not int or not 0<=value['generation']<=2**53-1 or \
                    not isinstance(value.get('profiles'),list) or len(value['profiles'])>32:
                raise ValueError('invalid_profile_list')
            active=value.get('active_profile_id')
            if active is not None:self._profile_id(active)
            seen=set()
            for profile in value['profiles']:
                if not isinstance(profile,dict):raise ValueError('invalid_profile_list')
                profile_id=self._profile_id(profile.get('id'))
                if profile_id in seen or not isinstance(profile.get('display_name'),str) or \
                        not 0<len(profile['display_name'])<=80 or profile.get('health') not in ('ready','recovery_required') or \
                        type(profile.get('selected')) is not bool or \
                        (profile.get('health')=='ready' and profile.get('revision') is None) or \
                        (profile.get('revision') is not None and
                         (not isinstance(profile['revision'],str) or not REVISION.fullmatch(profile['revision']))):
                    raise ValueError('invalid_profile_list')
                seen.add(profile_id)
            if active is not None and active not in seen:raise ValueError('invalid_selected_profile')
            if any(row['selected']!=(row['id']==active) for row in value['profiles']):raise ValueError('invalid_selected_profile')
            self.profile_list=value
            if self.profile_action_status=='unavailable':self.profile_action_status='loaded'
        self._call('ListProfiles',None,received,lambda _code:setattr(self,'profile_action_status','failed'))

    def _profiles_signal(self,_connection,sender,*_):
        if sender==self.owner:
            self.recheck()

    def _profile_action(self,method,parameters,success):
        if self.phase!='ready' or self.profile_mutating or \
                'named-profiles-v1' not in (self.capabilities or {}).get('features',[]):
            raise ValueError('profile_registry_unavailable')
        self.profile_mutating=True
        self.profile_action_status='working'
        def received(data):
            value=body(data,32768)
            self._profile_id(value.get('profile_id'))
            self.profile_mutating=False
            self.profile_action_status=success
            self.refresh_profiles()
            if method=='SelectProfile':self.recheck()
        def failed(_code):
            self.profile_mutating=False
            self.profile_action_status='unknown'
            self.refresh_profiles()
        self._call(method,parameters,received,failed)
        self.changed()

    def create_profile(self,profile_id):
        self._profile_action('CreateProfile',GLib.Variant('(s)',(self._profile_id(profile_id),)),'created')

    def clone_profile(self,source_id,revision,target_id):
        if not isinstance(revision,str) or not REVISION.fullmatch(revision):raise ValueError('invalid_profile_revision')
        self._profile_action('CloneProfile',GLib.Variant('(sss)',
            (self._profile_id(source_id),revision,self._profile_id(target_id))),'cloned')

    def select_profile(self,profile_id):
        if self.profile_list is None:raise ValueError('profile_registry_unavailable')
        selected=next((row for row in self.profile_list['profiles'] if row['id']==profile_id),None)
        if selected is None or selected['health']!='ready':raise ValueError('profile_unavailable')
        self._profile_action('SelectProfile',GLib.Variant('(st)',
            (self._profile_id(profile_id),self.profile_list['generation'])),'selected')

    def _fd_call(self,method,parameters,reply_type,fd_list,completed):
        if self.phase!='ready' or self.owner is None:raise ValueError('profile_service_unavailable')
        generation=self.generation
        cancel=Gio.Cancellable();self.pending.add(cancel)
        def finished(conn,result,*_):
            self.pending.discard(cancel)
            try:
                value,descriptors=conn.call_with_unix_fd_list_finish(result)
                if generation!=self.generation:return
                completed(value,descriptors)
            except (GLib.Error,ValueError,TypeError,OSError):
                if generation==self.generation:
                    self.profile_mutating=False;self.profile_action_status='unknown'
                    self.refresh_profiles()
            if generation==self.generation:self.changed()
        try:
            self.connection.call_with_unix_fd_list(self.owner,OBJECT,INTERFACE,method,parameters,
                GLib.VariantType(reply_type),Gio.DBusCallFlags.NO_AUTO_START,5000,fd_list,cancel,finished,None)
        except (GLib.Error,ValueError,TypeError,OSError):
            self.pending.discard(cancel)
            self.profile_mutating=False;self.profile_action_status='unknown'
            self.changed()
            raise

    def export_profile(self,profile_id,revision,exported):
        if not isinstance(revision,str) or not REVISION.fullmatch(revision):raise ValueError('invalid_profile_revision')
        def received(value,descriptors):
            if descriptors is None or descriptors.get_length()!=1:raise ValueError('invalid_export_descriptor')
            descriptor=descriptors.get(value.unpack()[0])
            try:exported(descriptor)
            finally:os.close(descriptor)
            self.profile_action_status='exported'
        self._fd_call('ExportProfile',GLib.Variant('(ss)',(self._profile_id(profile_id),revision)),
                      '(h)',None,received)

    def import_profile(self,profile_id,descriptor):
        profile_id=self._profile_id(profile_id)
        if self.phase!='ready' or 'named-profiles-v1' not in (self.capabilities or {}).get('features',[]):
            raise ValueError('profile_registry_unavailable')
        if self.profile_mutating:raise ValueError('profile_registry_busy')
        incoming=Gio.UnixFDList.new();index=incoming.append(descriptor)
        self.profile_mutating=True;self.profile_action_status='working'
        def received(value,_descriptors):
            result=body(value.unpack()[0],32768)
            self._profile_id(result.get('profile_id'))
            self.profile_mutating=False;self.profile_action_status='imported'
            self.refresh_profiles()
        self._fd_call('ImportProfile',GLib.Variant('(sh)',(self._profile_id(profile_id),index)),
                      '(s)',incoming,received)
        self.changed()

    def lookup_acceptance(self):
        request=self.pending_request
        if self.phase!='ready' or request is None or 'task-history-v1' not in self.capabilities['features']:
            return
        self.acceptance_lookup='checking'
        def received(data):
            value=body(data,32768)
            if value.get('profile_id')!=request['profile_id'] or value.get('request_id')!=request['request_id'] or type(value.get('found')) is not bool:
                raise ValueError('invalid_acceptance_lookup')
            if not value['found']:
                self.acceptance_lookup='not-found'
                return
            snapshot=value.get('task')
            if not isinstance(snapshot,dict) or snapshot.get('profile_revision')!=request['profile_revision']:
                raise ValueError('invalid_acceptance_lookup')
            state=TaskState();state.profile_revision=request['profile_revision'];state.submitting=True;state.profile_id=request['profile_id']
            state.submitted(snapshot.get('task_id'));state.observe(json.dumps(snapshot))
            self.state=state;self.task_profile_id=request['profile_id']
            self.pending_request=None;self.acceptance_lookup='found'
            self.text=TaskText(state.task_id)
            self.refresh();self.refresh_text()
        self._call('LookupRequest',GLib.Variant('(ss)',(request['profile_id'],request['request_id'])),
                   received,lambda _code:setattr(self,'acceptance_lookup','unknown'))

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
