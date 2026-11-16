"""Async same-user session-bus client with no automatic task resubmission."""
import json
import os
import uuid

import gi
gi.require_version('Gio','2.0')
from gi.repository import Gio, GLib

from runtime.ui.task_state import TaskState, capabilities

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

    def _call(self, method, parameters, completed):
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

    def recheck(self):
        """Explicit read-only recovery; an unknown submission is never replayed."""
        if self.connection is not None and self.owner is not None:
            self.phase = 'connecting'
            self._call('GetCapabilities', None, self._capabilities)
            self.changed()

    def refresh(self):
        if self.phase == 'ready' and self.state.task_id is not None:
            self._call('GetTask', GLib.Variant('(s)', (self.state.task_id,)), self.state.observe)

    def submit_system_info(self, note):
        if self.phase != 'ready' or self.capabilities is None or \
                not isinstance(note, str) or len(note.encode('utf-8')) > 16384:
            raise ValueError('task_unavailable')
        self.state.begin_submit()
        self.state.profile_revision = self.capabilities['profile_revision']
        payload = json.dumps({'version':1,'text':note,
                              'tool':{'kind':'system-info','arguments':{}}}, ensure_ascii=False)

        def accepted(task_id):
            self.state.submitted(task_id)
            self.refresh()

        self._call('SubmitTask', GLib.Variant('(ssss)', (uuid.uuid4().hex,
            self.capabilities['profile_id'], self.capabilities['profile_revision'], payload)), accepted)
        self.changed()

    def stop(self):
        if self.phase != 'ready' or self.state.task_id is None:
            raise ValueError('task_unavailable')
        self._call('RequestCancel', GLib.Variant('(ss)', (self.state.task_id,uuid.uuid4().hex)),
                   self.state.observe)

    def _signal(self, _conn, sender, _path, _interface, _name, parameters, *_):
        if sender != self.owner or self.state.task_id is None:
            return
        task_id, _sequence, data = parameters.unpack()
        if task_id != self.state.task_id:
            return
        try:
            if self.state.observe(data, signal=True) == 'gap':
                self.refresh()
        except (ValueError, TypeError):
            self.phase = 'error'
        self.changed()
