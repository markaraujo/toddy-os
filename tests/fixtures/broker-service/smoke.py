#!/usr/bin/env python3
"""Real unprivileged broker/source smoke on private session bus and actual logind.

Run with dbus-run-session. Uses a temporary private workspace only; no root call,
provider, package install or native-target acceptance is implied.
"""
import argparse
import json
import os
from pathlib import Path
import select
import signal
import subprocess
import sys
import tempfile
import time

import gi
gi.require_version('Gio', '2.0')
from gi.repository import Gio, GLib

ROOT = Path(__file__).resolve().parents[3]
BUS = 'io.github.markaraujo.Toddy.Service'
OBJECT = '/io/github/markaraujo/Toddy/Service'
INTERFACE = BUS + '1'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--broker', type=Path, default=ROOT / 'runtime/broker/service.py')
    parser.add_argument('--defaults', type=Path, default=ROOT / 'config/phase2')
    args = parser.parse_args()
    if os.geteuid() == 0:
        raise SystemExit('unprivileged_probe_required')
    started = time.monotonic()
    connection = Gio.bus_get_sync(Gio.BusType.SESSION, None)
    def call(method, values=(), signature='()'):
        result = connection.call_sync(BUS, OBJECT, INTERFACE, method,
            GLib.Variant(signature, values) if values else None,
            GLib.VariantType('(s)'), Gio.DBusCallFlags.NONE, 5000, None).unpack()[0]
        return result if method == 'SubmitTask' else json.loads(result)
    def snapshot(task):
        return call('GetTask', (task,), '(s)')
    def until(check, timeout=8):
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            value = check()
            if value:
                return value
            time.sleep(.025)
        raise AssertionError('probe_deadline')
    def body(kind, arguments):
        return json.dumps({'version': 1, 'text': 'Explicit native broker smoke',
                           'tool': {'kind': kind, 'arguments': arguments}})
    with tempfile.TemporaryDirectory(prefix='toddy-broker-smoke-') as directory:
        base = Path(directory)
        data, workspace = base / 'data', base / 'workspace'
        process = None
        command = [sys.executable, str(args.broker), '--data-dir', str(data),
                   '--workspace', str(workspace), '--defaults', str(args.defaults)]
        def start():
            child = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if not select.select([child.stdout], [], [], 8)[0] or child.stdout.readline() != b'READY\n':
                child.terminate(); child.wait(timeout=5)
                raise AssertionError('broker_not_ready')
            return child
        try:
            process = start()
            cap = call('GetCapabilities')
            assert cap['agent_backend'] is False and cap['tools'] == ['system-info']
            revision = cap['profile_revision']
            system_task = call('SubmitTask', ('system-one', 'toddy-default', revision, body('system-info', {})), '(ssss)')
            until(lambda: snapshot(system_task)['state'] == 'completed')
            assert snapshot(system_task)['result_uncertain'] is False
            config = json.loads((args.defaults / 'profile/config.json').read_text())
            config['tools']['enabled'] = ['system-info', 'file-write', 'file-read', 'shell']
            stage = call('ValidateProfile', ('toddy-default', revision, json.dumps(config)), '(sss)')
            applied = call('ApplyProfile', ('toddy-default', revision, stage['validated_revision']), '(sss)')
            revision = applied['profile_revision']
            write_body = body('file-write', {'path': 'hello.txt', 'text': 'Actual native broker write.', 'expected_sha256': None})
            written = call('SubmitTask', ('write-one', 'toddy-default', revision, write_body), '(ssss)')
            until(lambda: snapshot(written)['state'] == 'completed')
            assert (workspace / 'hello.txt').read_text() == 'Actual native broker write.'
            duplicate = call('SubmitTask', ('write-one', 'toddy-default', revision, write_body), '(ssss)')
            assert duplicate == written
            # Actual managed command, explicit Stop, verify the command PID exits.
            stop_argv = ['/usr/bin/python3', '-c',
                "import os,time; from pathlib import Path; Path('stop.pid').write_text(str(os.getpid())); time.sleep(60)"]
            stop_task = call('SubmitTask', ('stop-one', 'toddy-default', revision,
                body('shell', {'argv': stop_argv, 'timeout_seconds': 90})), '(ssss)')
            until(lambda: (workspace / 'stop.pid').exists())
            stopped_pid = int((workspace / 'stop.pid').read_text())
            stop = call('RequestCancel', (stop_task, 'stop-request'), '(ss)')
            assert stop['cancel_requested'] is True
            until(lambda: snapshot(stop_task)['state'] == 'waiting')
            until(lambda: not Path('/proc', str(stopped_pid)).exists())
            assert snapshot(stop_task)['result_uncertain'] is True  # Shell effects are not proved by exit.
            # Crash after a real fsynced effect, before any result recording.
            crash_argv = ['/usr/bin/python3', '-c',
                "import os,time; f=open('effect-once','a'); f.write('x'); f.flush(); os.fsync(f.fileno()); time.sleep(60)"]
            crash_body = body('shell', {'argv': crash_argv, 'timeout_seconds': 90})
            crash_task = call('SubmitTask', ('crash-one', 'toddy-default', revision, crash_body), '(ssss)')
            until(lambda: (workspace / 'effect-once').exists())
            assert (workspace / 'effect-once').read_text() == 'x'
            process.kill(); process.wait(timeout=5)
            process.stdout.close(); process.stderr.close()
            process = start()
            recovered = snapshot(crash_task)
            assert recovered['state'] == 'waiting' and recovered['result_uncertain'] is True
            assert call('SubmitTask', ('crash-one', 'toddy-default', revision, crash_body), '(ssss)') == crash_task
            assert (workspace / 'effect-once').read_text() == 'x'
            assert snapshot(crash_task)['operation_id'] is not None
            print(json.dumps({'scope': 'actual unprivileged broker source, private session bus, native logind, temporary workspace; no root/provider/guest acceptance',
                'uid': os.getuid(), 'agent_backend': False, 'system_info_completed': True,
                'profile_stage_apply': True, 'actual_file_write_duplicate_no_replay': True,
                'shell_stop_process_exit_uncertainty_retained': True,
                'crash_after_fsynced_effect_restart_no_replay': True,
                'duration_seconds': round(time.monotonic() - started, 3)}))
        finally:
            if process is not None:
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=8)
                    except subprocess.TimeoutExpired:
                        process.kill(); process.wait(timeout=5)
                process.stdout.close(); process.stderr.close()


if __name__ == '__main__':
    main()
