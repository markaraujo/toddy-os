#!/usr/bin/env python3
"""B01 native GIO async/peer/FD/signal fixture on a private session bus only."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import select
import stat
import subprocess
import sys
import time

import gi
gi.require_version('Gio', '2.0')
from gi.repository import Gio, GLib

BUS = 'io.github.markaraujo.Toddy.Service'
OBJECT = '/io/github/markaraujo/Toddy/Service'
INTERFACE = BUS + '1'
INFO = Gio.DBusNodeInfo.new_for_xml(Path(__file__).with_name(INTERFACE + '.xml').read_text())


def serve():
    connection = Gio.bus_get_sync(Gio.BusType.SESSION, None)

    def handle(conn, sender, _path, _interface, method, parameters, invocation):
        try:
            uid = conn.call_sync('org.freedesktop.DBus', '/org/freedesktop/DBus',
                'org.freedesktop.DBus', 'GetConnectionUnixUser', GLib.Variant('(s)', (sender,)),
                GLib.VariantType('(u)'), Gio.DBusCallFlags.NONE, 5000, None).unpack()[0]
            if uid != os.getuid():
                raise ValueError('wrong_peer')
            values = parameters.unpack()
            if any(isinstance(v, str) and len(v.encode()) > 65536 for v in values):
                raise ValueError('input_bound')
            if method == 'GetCapabilities':
                body = {'version': 1, 'fixture_only': True, 'authenticated_uid': uid,
                        'features': ['async', 'peer-uid', 'unix-fd', 'task-signal']}
                invocation.return_value(GLib.Variant('(s)', (json.dumps(body),)))
            elif method == 'RequestCancel':
                body = {'version': 1, 'fixture_only': True, 'cancel_requested': True}
                invocation.return_value(GLib.Variant('(s)', (json.dumps(body),)))
                conn.emit_signal(None, OBJECT, INTERFACE, 'TaskChanged',
                    GLib.Variant('(sts)', (values[0], 2, json.dumps(body))))
            elif method == 'ExportProfile':
                fd = os.memfd_create('toddy-fixture-profile', os.MFD_ALLOW_SEALING | os.MFD_CLOEXEC)
                try:
                    os.write(fd, b'{"fixture_only":true,"provider":"deferred"}')
                    fcntl.fcntl(fd, fcntl.F_ADD_SEALS, fcntl.F_SEAL_SEAL | fcntl.F_SEAL_SHRINK | fcntl.F_SEAL_GROW | fcntl.F_SEAL_WRITE)
                    read_fd = os.open('/proc/self/fd/' + str(fd), os.O_RDONLY | os.O_CLOEXEC)
                    try:
                        descriptors = Gio.UnixFDList.new()
                        index = descriptors.append(read_fd)
                        invocation.return_value_with_unix_fd_list(GLib.Variant('(h)', (index,)), descriptors)
                    finally:
                        os.close(read_fd)
                finally:
                    os.close(fd)
            elif method == 'StageProfileBundle':
                descriptors = invocation.get_message().get_unix_fd_list()
                if descriptors is None:
                    raise ValueError('missing_fd')
                fd = descriptors.get(values[2])
                try:
                    info = os.fstat(fd)
                    if not stat.S_ISREG(info.st_mode) or info.st_size > 8 * 1024 * 1024:
                        raise ValueError('invalid_fd')
                    data = os.pread(fd, 8 * 1024 * 1024 + 1, 0)
                    if len(data) > 8 * 1024 * 1024:
                        raise ValueError('bundle_bound')
                    body = {'fixture_only': True, 'copied_bytes_sha256': hashlib.sha256(data).hexdigest()}
                    invocation.return_value(GLib.Variant('(s)', (json.dumps(body),)))
                finally:
                    os.close(fd)
            else:
                invocation.return_dbus_error(INTERFACE + '.NotImplemented', 'Fixture capability unavailable')
        except (ValueError, OSError, GLib.Error):
            invocation.return_dbus_error(INTERFACE + '.InvalidInput', 'Rejected fixture request')

    connection.register_object(OBJECT, INFO.interfaces[0], handle, None, None)
    Gio.bus_own_name_on_connection(connection, BUS, Gio.BusNameOwnerFlags.NONE,
        lambda *_: print('READY', flush=True), None)
    GLib.MainLoop().run()


def client():
    started = time.monotonic()
    server = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), '--serve'],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        if not select.select([server.stdout], [], [], 5)[0] or server.stdout.readline() != b'READY\n':
            raise RuntimeError('bridge_server_not_ready')
        connection = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        loop = GLib.MainLoop()
        outcome = {}

        def completed(conn, result, *_):
            try:
                outcome['capabilities'] = json.loads(conn.call_finish(result).unpack()[0])
            except GLib.Error as exc:
                outcome['error'] = str(exc)
            loop.quit()

        timeout = GLib.timeout_add(5000, lambda: (outcome.update(error='async_deadline'), loop.quit(), False)[-1])
        connection.call(BUS, OBJECT, INTERFACE, 'GetCapabilities', None,
            GLib.VariantType('(s)'), Gio.DBusCallFlags.NONE, 5000, None, completed, None)
        loop.run()
        GLib.source_remove(timeout)
        assert 'error' not in outcome
        assert outcome['capabilities']['version'] == 1
        assert outcome['capabilities']['authenticated_uid'] == os.getuid() and os.getuid() != 0
        parameters = GLib.Variant('(ss)', ('default', 'f' * 64))
        response, descriptors = connection.call_with_unix_fd_list_sync(BUS, OBJECT, INTERFACE,
            'ExportProfile', parameters, GLib.VariantType('(h)'), Gio.DBusCallFlags.NONE, 5000, None, None)
        fd = descriptors.get(response.unpack()[0])
        try:
            content = os.pread(fd, 8192, 0)
            assert json.loads(content) == {'fixture_only': True, 'provider': 'deferred'}
            try:
                os.write(fd, b'forbidden')
            except OSError:
                pass
            else:
                raise AssertionError('export_fd_writable')
            incoming = Gio.UnixFDList.new()
            index = incoming.append(fd)
            result, _ = connection.call_with_unix_fd_list_sync(BUS, OBJECT, INTERFACE,
                'StageProfileBundle', GLib.Variant('(ssh)', ('default', 'f' * 64, index)),
                GLib.VariantType('(s)'), Gio.DBusCallFlags.NONE, 5000, incoming, None)
            assert json.loads(result.unpack()[0])['copied_bytes_sha256'] == hashlib.sha256(content).hexdigest()
        finally:
            os.close(fd)
        read_fd, write_fd = os.pipe()
        try:
            incoming = Gio.UnixFDList.new()
            index = incoming.append(read_fd)
            try:
                connection.call_with_unix_fd_list_sync(BUS, OBJECT, INTERFACE,
                    'StageProfileBundle', GLib.Variant('(ssh)', ('default', 'f' * 64, index)),
                    GLib.VariantType('(s)'), Gio.DBusCallFlags.NONE, 1000, incoming, None)
            except GLib.Error as exc:
                assert 'InvalidInput' in str(exc)
            else:
                raise AssertionError('nonregular_fd_accepted')
        finally:
            os.close(read_fd); os.close(write_fd)
        signals = []

        def signal(_conn, _sender, _path, _interface, _name, values, *_):
            signals.append(values.unpack()); loop.quit()

        subscription = connection.signal_subscribe(BUS, INTERFACE, 'TaskChanged', OBJECT,
            None, Gio.DBusSignalFlags.NONE, signal, None)
        connection.call_sync(BUS, OBJECT, INTERFACE, 'RequestCancel',
            GLib.Variant('(ss)', ('task-fixture', 'cancel-fixture')), GLib.VariantType('(s)'),
            Gio.DBusCallFlags.NONE, 5000, None)
        timeout = GLib.timeout_add(5000, lambda: (loop.quit(), False)[-1])
        loop.run(); GLib.source_remove(timeout)
        connection.signal_unsubscribe(subscription)
        assert signals and signals[0][0:2] == ('task-fixture', 2)
        print(json.dumps({'scope': 'native GIO fixture only; no durable task/profile/root effect',
            'uid': os.getuid(), 'gio_version': [GLib.MAJOR_VERSION, GLib.MINOR_VERSION, GLib.MICRO_VERSION],
            'async_call': 'passed', 'actual_peer_uid': 'passed', 'typed_signal': 'passed',
            'sealed_readonly_fd_roundtrip': 'passed', 'pipe_fd_rejected': 'passed',
            'pid_namespace': os.readlink('/proc/self/ns/pid'),
            'elapsed_seconds': round(time.monotonic() - started, 3)}, indent=2))
    finally:
        server.terminate()
        server.wait(timeout=5)
        server.stdout.close(); server.stderr.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--serve', action='store_true')
    args = parser.parse_args()
    serve() if args.serve else client()
