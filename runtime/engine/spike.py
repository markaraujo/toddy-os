#!/usr/bin/env python3
"""Real pinned Pi fixture/tool/cancel protocol proof; never a live-provider test."""
import argparse
import json
import os
from pathlib import Path
import resource
import shutil
import struct
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'broker'))
from protocol import encode, read_frame


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--node', default=shutil.which('node'))
    args = parser.parse_args()
    results = []
    started = time.monotonic()

    def launch():
        process = subprocess.Popen([args.node, str(Path(__file__).with_name('fixture-worker.mjs'))],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            env={'PATH': '/usr/bin:/usr/sbin', 'HOME': os.environ.get('HOME', '/tmp'), 'LANG': 'C.UTF-8'})
        hello = read_frame(process.stdout)
        assert hello == {'version': 1, 'kind': 'hello', 'worker_id': 'worker-fixture',
                         'capabilities': ['fixture-tool', 'cancel'], 'max_frame': 1048576}
        return process

    def finish(process, expected):
        if not process.stdin.closed:
            process.stdin.close()
        try:
            code = process.wait(timeout=5)
            assert code == expected, (code, process.stderr.read(4096).decode(errors='replace'))
        finally:
            if process.poll() is None:
                process.kill()
                process.wait()
            process.stdout.close()
            process.stderr.close()

    base = {'version': 1, 'worker_id': 'worker-fixture', 'run_id': 'run-fixture',
            'request_id': 'request-fixture'}
    run = {**base, 'kind': 'run', 'seq': 1, 'input': 'Read the fictional OS metadata.', 'profile_revision': 'f' * 64}
    for cancel in [False, True]:
        process = launch()
        try:
            frame = encode(run)
            # Exercise actual partial pipe framing, not just in-memory decoding.
            process.stdin.write(frame[:2]); process.stdin.flush()
            process.stdin.write(frame[2:]); process.stdin.flush()
            request = read_frame(process.stdout)
            assert request['kind'] == 'tool_request' and request['seq'] == 1
            assert request['arguments'] == {'name': 'os-release'} and request['tool'] == 'read_fixture'
            command = {**base, 'kind': 'cancel', 'seq': 2} if cancel else {
                **base, 'kind': 'tool_result', 'seq': 2, 'tool_call_id': request['tool_call_id'], 'content': 'NAME=Toddy OS fixture'}
            process.stdin.write(encode(command)); process.stdin.flush()
            events = []
            sequence = 1
            while True:
                event = read_frame(process.stdout)
                assert event['run_id'] == base['run_id'] and event['request_id'] == base['request_id']
                assert event['seq'] == sequence + 1
                sequence = event['seq']; events.append(event)
                if event['kind'] == 'done':
                    assert event['state'] == ('canceled' if cancel else 'completed')
                    break
                assert event['kind'] == 'text' and not cancel
            if not cancel:
                assert any(e['kind'] == 'text' and e['text'] == 'Verified fixture tool result.' for e in events)
            finish(process, 0)
            results.append({'case': 'cancel-pending-tool' if cancel else 'pi-fixture-tool-roundtrip', 'result': 'passed'})
        finally:
            if process.poll() is None:
                process.kill(); process.wait()

    malformed = {
        'duplicate-json-key': b'{"version":1,"version":1}',
        'unsupported-version': json.dumps({**run, 'version': 2}).encode(),
        'unknown-field': json.dumps({**run, 'root_grant': True}).encode(),
        'out-of-run-result': json.dumps({**base, 'kind': 'tool_result', 'seq': 1, 'tool_call_id': 'unknown', 'content': 'untrusted'}).encode(),
        'invalid-utf8': b'\xff',
    }
    for name, body in malformed.items():
        process = launch()
        process.stdin.write(struct.pack('>I', len(body)) + body); process.stdin.flush()
        finish(process, 2)
        results.append({'case': name, 'result': 'passed-rejection'})
    for name, body in [('oversized-frame', struct.pack('>I', 1048577)), ('truncated-frame', b'\0\0\0\x10{')]:
        process = launch()
        process.stdin.write(body); process.stdin.flush()
        finish(process, 2)
        results.append({'case': name, 'result': 'passed-rejection'})
    for name in ['disconnect-pending-tool', 'wrong-tool-result-id']:
        process = launch()
        process.stdin.write(encode(run)); process.stdin.flush()
        assert read_frame(process.stdout)['kind'] == 'tool_request'
        if name == 'wrong-tool-result-id':
            process.stdin.write(encode({**base, 'kind': 'tool_result', 'seq': 2,
                'tool_call_id': 'different-call', 'content': 'untrusted'})); process.stdin.flush()
        finish(process, 0 if name == 'disconnect-pending-tool' else 2)
        results.append({'case': name, 'result': 'passed-disconnect' if name == 'disconnect-pending-tool' else 'passed-rejection'})
    print(json.dumps({'scope': 'Pi 1.5.0 deterministic fixture; no live API/local model',
        'node': subprocess.check_output([args.node, '--version'], text=True).strip(),
        'uid': os.getuid(), 'cases': results, 'elapsed_seconds': round(time.monotonic() - started, 3),
        'max_child_rss_kib': resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss}, indent=2))


if __name__ == '__main__':
    main()
