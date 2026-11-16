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
            assert 'agent-text-v1' in cap['features'] and 'profile-settings-v1' in cap['features']
            revision = cap['profile_revision']
            original_revision = revision
            settings = call('GetProfileConfig', ('toddy-default',), '(s)')
            assert settings['profile_revision'] == revision and settings['config']['provider']['mode'] == 'deferred'
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
            # A standalone source process is deliberately outside the canonical
            # user-systemd parent. Shell must fail closed, never run uncontained.
            stop_argv = ['/usr/bin/python3', '-c',
                "from pathlib import Path; Path('must-not-run').write_text('bad')"]
            denied_task = call('SubmitTask', ('unmanaged-shell', 'toddy-default', revision,
                body('shell', {'argv': stop_argv, 'timeout_seconds': 10})), '(ssss)')
            until(lambda: snapshot(denied_task)['state'] == 'waiting')
            assert not (workspace / 'must-not-run').exists()
            assert snapshot(denied_task)['result_uncertain'] is True
            # Actual setup failure traverses the asynchronous exception handler;
            # it must become held, not silently strand a queued task.
            local = dict(config)
            local['provider'] = {'mode': 'local', 'adapter_id': 'local-llama-cpp',
                'model_id': 'toddy-qwen3-1.7b-q8_0', 'connection_ref': 'missing-local', 'allow_remote_fallback': False}
            stage = call('ValidateProfile', ('toddy-default', revision, json.dumps(local)), '(sss)')
            revision = call('ApplyProfile', ('toddy-default', revision, stage['validated_revision']), '(sss)')['profile_revision']
            unavailable = call('SubmitTask', ('missing-setup', 'toddy-default', revision,
                json.dumps({'version': 1, 'agent': True, 'text': 'No configured connection exists.', 'remote_consent': False})), '(ssss)')
            until(lambda: snapshot(unavailable)['state'] == 'waiting')
            assert snapshot(unavailable)['summary'] == 'dispatch_review_required'
            page = call('GetTaskText', (unavailable, 0), '(st)')
            assert page['complete'] and page['chunks'] == [] and page['latest_sequence'] == 0
            assert call('AcknowledgeTaskText', (unavailable, 0), '(st)')['erased']
            assert call('RestoreProfile', ('toddy-default', revision, original_revision), '(sss)')['restored']
            assert call('GetCapabilities')['provider_mode'] == 'deferred'
            print(json.dumps({'scope': 'actual unprivileged broker source, private session bus, native logind, temporary workspace; no root/provider/guest acceptance',
                'uid': os.getuid(), 'agent_backend': False, 'system_info_completed': True,
                'profile_stage_apply': True, 'actual_file_write_duplicate_no_replay': True,
                'shell_unavailable_without_managed_parent_no_effect': True,
                'profile_get_restore': True, 'failed_engine_setup_held_not_queued': True, 'empty_transient_output_ack_erased': True,
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
