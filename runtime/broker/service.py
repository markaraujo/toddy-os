#!/usr/bin/env python3
"""Authenticated unprivileged native-tool broker; no model backend advertised."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import fcntl
import json
import os
from pathlib import Path
import resource
import signal
import stat
import sys
import time
import uuid

import gi
gi.require_version('Gio', '2.0')
from gi.repository import Gio, GLib

from profiles import ProfileError, ProfileStore
from protocol import strict_json
from tasks import TaskError, TaskJournal
from core import BrokerCore, BrokerError, NATIVE_TOOLS

BUS = 'io.github.markaraujo.Toddy.Service'
OBJECT = '/io/github/markaraujo/Toddy/Service'
INTERFACE = BUS + '1'
ROOT_BUS = 'io.github.markaraujo.Toddy.Executor'
ROOT_OBJECT = '/io/github/markaraujo/Toddy/Executor'
ROOT_INTERFACE = ROOT_BUS + '1'


class RootClient:
    def __init__(self, connection):
        self.connection = connection

    def call(self, method, values, signature, timeout=5000):
        # Independent bus owner check; root policy still authenticates our actual
        # connection UID/session, never a JSON-provided identity or grant.
        uid = self.connection.call_sync('org.freedesktop.DBus', '/org/freedesktop/DBus',
            'org.freedesktop.DBus', 'GetConnectionUnixUser', GLib.Variant('(s)', (ROOT_BUS,)),
            GLib.VariantType('(u)'), Gio.DBusCallFlags.NONE, 3000, None).unpack()[0]
        if uid != 0:
            raise BrokerError('executor_owner_invalid')
        response = self.connection.call_sync(ROOT_BUS, ROOT_OBJECT, ROOT_INTERFACE, method,
            GLib.Variant(signature, values), GLib.VariantType('(s)'),
            Gio.DBusCallFlags.NONE, timeout, None).unpack()[0]
        if len(response.encode()) > 65536:
            raise BrokerError('executor_response_limit')
        result = strict_json(response.encode())
        if not isinstance(result, dict):
            raise BrokerError('executor_response_invalid')
        return result

    def dispatch(self, operation_id, kind, arguments, canceled):
        values = (operation_id, kind, json.dumps(arguments, separators=(',', ':'), allow_nan=False))
        self.call('PlanOperation', values, '(sss)')
        if canceled():
            self.cancel(operation_id)
            raise BrokerError('interactive_dispatch_stopped')
        result = self.call('DispatchOperation', values, '(sss)', timeout=3600000)
        # Only a root adapter's actual verified postcondition proves an effect;
        # arbitrary root command exit explicitly leaves side effects unverified.
        postcondition = result.get('result')
        return {'verified': result.get('state') == 'completed'
                and isinstance(postcondition, dict) and postcondition.get('verified') is True}

    def inspect(self, operation_id):
        return self.call('GetOperation', (operation_id,), '(s)')

    def cancel(self, operation_id):
        return self.call('CancelOperation', (operation_id,), '(s)')


class ActiveSession:
    """Native logind account session; unavailable/remote/locked fails closed."""
    def __init__(self, connection, uid):
        self.connection, self.uid = connection, uid

    def __call__(self):
        try:
            user = self.connection.call_sync('org.freedesktop.login1', '/org/freedesktop/login1',
                'org.freedesktop.login1.Manager', 'GetUser', GLib.Variant('(u)', (self.uid,)),
                GLib.VariantType('(o)'), Gio.DBusCallFlags.NONE, 1000, None).unpack()[0]
            display = self.connection.call_sync('org.freedesktop.login1', user,
                'org.freedesktop.DBus.Properties', 'Get', GLib.Variant('(ss)',
                ('org.freedesktop.login1.User', 'Display')), GLib.VariantType('(v)'),
                Gio.DBusCallFlags.NONE, 1000, None).unpack()[0]
            session_id, path = display
            if not session_id or path == '/':
                return False
            properties = self.connection.call_sync('org.freedesktop.login1', path,
                'org.freedesktop.DBus.Properties', 'GetAll', GLib.Variant('(s)',
                ('org.freedesktop.login1.Session',)), GLib.VariantType('(a{sv})'),
                Gio.DBusCallFlags.NONE, 1000, None).unpack()[0]
            return (properties.get('User', (None,))[0] == self.uid
                    and properties.get('Active') is True
                    and properties.get('Remote') is False
                    and properties.get('LockedHint') is False)
        except (GLib.Error, ValueError, TypeError, IndexError):
            return False


def peer_uid(connection, sender):
    uid = connection.call_sync('org.freedesktop.DBus', '/org/freedesktop/DBus',
        'org.freedesktop.DBus', 'GetConnectionUnixUser', GLib.Variant('(s)', (sender,)),
        GLib.VariantType('(u)'), Gio.DBusCallFlags.NONE, 3000, None).unpack()[0]
    if uid != os.getuid() or uid == 0:
        raise BrokerError('wrong_peer')
    return uid


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source_default = Path(__file__).resolve().parents[2] / 'config/phase2'
    installed_default = Path('/usr/share/toddy')
    parser.add_argument('--data-dir', type=Path, default=Path(os.environ.get('XDG_DATA_HOME',
                        str(Path.home() / '.local/share'))) / 'toddy/profiles/toddy-default')
    parser.add_argument('--workspace', type=Path, default=Path.home() / 'Toddy')
    parser.add_argument('--defaults', type=Path, default=source_default if source_default.is_dir() else installed_default)
    args = parser.parse_args()
    if os.getuid() == 0 or os.geteuid() == 0:
        raise SystemExit('unprivileged_broker_required')
    os.umask(0o077)
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    # Source/installed configuration path is an invocation option, never client
    # input. Refuse symlinked/noncanonical private workspace/store paths.
    for directory in (args.data_dir, args.workspace):
        if not directory.is_absolute() or directory.resolve() != directory:
            raise SystemExit('unsafe_broker_directory')
        directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    schema = strict_json((args.defaults / 'profile.schema.json').read_bytes())
    profiles = ProfileStore(args.data_dir, 'toddy-default', schema,
        capabilities={'adapters': set(), 'tools': NATIVE_TOOLS, 'skills': {'explain-system'},
                      'extensions': set(), 'workflows': set()})
    if profiles.current() is None:
        template = args.defaults / 'profile'
        files = {path.name: path.read_bytes() for path in template.iterdir()
                 if path.name in {'config.json', 'SOUL.md', 'IDENTITY.md', 'USER.md', 'AGENTS.md'}
                 and path.is_file() and not path.is_symlink()}
        profiles.apply(files, expected_revision=None)
    journal = TaskJournal(profiles)
    # A separate lifetime service lock prevents a second broker from recovering
    # another instance's accepted-but-not-yet-dispatched task.
    owner_fd = os.open(args.data_dir / 'broker.lock', os.O_RDWR | os.O_CREAT | os.O_CLOEXEC | os.O_NOFOLLOW, 0o600)
    owner_info = os.fstat(owner_fd)
    if (not stat.S_ISREG(owner_info.st_mode) or owner_info.st_nlink != 1
            or owner_info.st_uid != os.getuid() or stat.S_IMODE(owner_info.st_mode) != 0o600):
        os.close(owner_fd)
        raise SystemExit('unsafe_broker_lock')
    try:
        fcntl.flock(owner_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        raise SystemExit('broker_already_running') from None
    journal.recover()
    session_connection = Gio.bus_get_sync(Gio.BusType.SESSION, None)
    system_connection = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)
    core = BrokerCore(profiles, journal, args.workspace, root_client=RootClient(system_connection),
                      dispatch_allowed=ActiveSession(system_connection, os.getuid()))
    info = Gio.DBusNodeInfo.new_for_xml(Path(__file__).with_name(INTERFACE + '.xml').read_text())
    loop = GLib.MainLoop()
    pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix='toddy-broker')
    pending = None
    stopping = False
    stages = {}
    emitted = {}

    def emit(task_id):
        snapshot = journal.inspect(task_id)
        if emitted.get(task_id) != snapshot['sequence']:
            session_connection.emit_signal(None, OBJECT, INTERFACE, 'TaskChanged',
                GLib.Variant('(sts)', (task_id, snapshot['sequence'], json.dumps(snapshot, separators=(',', ':')))))
            emitted[task_id] = snapshot['sequence']
        # One in-flight task and bounded terminal bookkeeping.
        if len(emitted) > 256:
            emitted.pop(next(iter(emitted)))
        return False

    def poll():
        if pending:
            current = journal.inspect(pending)
            if not current['cancel_requested'] and (journal.remaining_seconds(pending) <= 0 or not core.dispatch_allowed()):
                core.cancel(pending)
            emit(pending)
        return True

    def finished(task_id):
        nonlocal pending
        emit(task_id)
        pending = None
        if stopping:
            loop.quit()
        return False

    def execute(task_id, request):
        try:
            core.execute(task_id, request)
        except (TaskError, ProfileError, BrokerError, ToolError, OSError, GLib.Error):
            # The journal holds uncertain effects; no exception text/raw output
            # is exported or retried. Pre-dispatch stop remains visible.
            journal.hold(task_id)
        except Exception:
            # Never turn an unexpected worker failure into success.
            journal.hold(task_id)
        finally:
            GLib.idle_add(finished, task_id)

    def reply(invocation, result):
        invocation.return_value(GLib.Variant('(s)', (json.dumps(result, separators=(',', ':')),)))

    def handle(conn, sender, _path, _interface, method, parameters, invocation):
        nonlocal pending
        try:
            peer_uid(conn, sender)
            values = parameters.unpack()
            if any(isinstance(value, str) and len(value.encode()) > 65536 for value in values):
                raise BrokerError('request_limit')
            if method == 'GetCapabilities':
                reply(invocation, core.capabilities())
            elif method == 'GetTask':
                reply(invocation, core.reconcile(values[0]))
            elif method == 'RequestCancel':
                task_id, request_id = values
                if not request_id or len(request_id) > 128:
                    raise BrokerError('invalid_cancel_request')
                reply(invocation, core.cancel(task_id)); emit(task_id)
            elif method == 'SubmitTask':
                request_id, profile_id, revision, encoded = values
                if profile_id != profiles.profile_id:
                    raise BrokerError('unknown_profile')
                if stopping or pending:
                    raise BrokerError('broker_busy')
                snapshot, request = core.submit(request_id, revision, encoded)
                task_id = snapshot['task_id']
                invocation.return_value(GLib.Variant('(s)', (task_id,)))
                emit(task_id)
                if snapshot['state'] == 'queued':
                    pending = task_id
                    pool.submit(execute, task_id, request)
            elif method in ('ValidateProfile', 'ApplyProfile'):
                profile_id, expected, candidate = values
                if profile_id != profiles.profile_id or expected != profiles.current():
                    raise BrokerError('stale_profile_revision')
                now = time.monotonic()
                for token in list(stages):
                    if stages[token]['expires'] <= now:
                        del stages[token]
                if method == 'ValidateProfile':
                    if len(stages) >= 8:
                        raise BrokerError('profile_stage_limit')
                    files = profiles.snapshot(expected)
                    files['config.json'] = candidate.encode()
                    revision, _, _ = profiles.validate(files)
                    token = 'stage-' + uuid.uuid4().hex
                    stages[token] = {'sender': sender, 'expected': expected, 'files': files,
                                     'revision': revision, 'expires': now + 600}
                    reply(invocation, {'version': 1, 'validated_revision': token,
                                       'profile_revision': revision, 'valid': True})
                else:
                    stage = stages.get(candidate)
                    if not stage or stage['sender'] != sender or stage['expected'] != expected:
                        raise BrokerError('profile_stage_unavailable')
                    revision = profiles.apply(stage['files'], expected_revision=expected)
                    del stages[candidate]
                    reply(invocation, {'version': 1, 'profile_revision': revision, 'applied': True})
            else:
                raise BrokerError('method_unavailable')
        except (ProfileError, TaskError, BrokerError) as error:
            invocation.return_dbus_error(INTERFACE + '.Rejected', str(error))
        except (ValueError, UnicodeError, RecursionError, OverflowError, GLib.Error, OSError):
            invocation.return_dbus_error(INTERFACE + '.Rejected', 'invalid_or_unavailable_request')
        except Exception:
            invocation.return_dbus_error(INTERFACE + '.Rejected', 'broker_internal_error')

    def stop():
        nonlocal stopping
        stopping = True
        if pending:
            core.cancel(pending)
        else:
            loop.quit()
        return False

    session_connection.register_object(OBJECT, info.interfaces[0], handle, None, None)
    Gio.bus_own_name_on_connection(session_connection, BUS, Gio.BusNameOwnerFlags.NONE,
        lambda *_: print('READY', flush=True), lambda *_: stop())
    GLib.timeout_add(100, poll)
    GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGTERM, stop)
    GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGINT, stop)
    try:
        loop.run()
    finally:
        pool.shutdown(wait=True, cancel_futures=True)
        os.close(owner_fd)


if __name__ == '__main__':
    main()
