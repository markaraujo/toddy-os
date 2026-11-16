#!/usr/bin/env python3
"""Actual production worker/adapter/Pi with synthetic private Unix HTTP protocol.

No real model/provider qualification. Verifies framed process plumbing, FD secret
privacy and a real temporary file effect routed back to the trusted broker.
"""
import argparse
import copy
import hashlib
import http.server
import json
import os
from pathlib import Path
import shutil
import socketserver
import sys
import tempfile
import threading
import time

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'runtime/broker'))
from engine import EngineAdapter, EngineError


class Server(socketserver.ThreadingMixIn, socketserver.UnixStreamServer):
    daemon_threads = True


class Handler(http.server.BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'
    def log_message(self, *_):
        pass
    def do_POST(self):
        if self.headers.get('Authorization') != 'Bearer ' + self.server.credential:
            self.send_error(401); return
        size = int(self.headers.get('Content-Length', '0'))
        if size > 1048576:
            self.send_error(413); return
        body = json.loads(self.rfile.read(size))
        assert self.server.credential not in json.dumps(body)
        if self.path == '/apply-template':
            content = json.dumps({'prompt': 'Synthetic tokenizer input'}).encode()
            kind = 'application/json'
        elif self.path == '/tokenize':
            content = json.dumps({'tokens': [1, 2, 3]}).encode(); kind = 'application/json'
        elif self.path == '/v1/chat/completions':
            self.server.generations += 1
            after_tool = any(message['role'] == 'tool' for message in body['messages'])
            if after_tool:
                delta = {'role': 'assistant', 'content': 'Verified actual broker file write.'}
                reason = 'stop'
            else:
                delta = {'role': 'assistant', 'tool_calls': [{'index': 0, 'id': 'upstream-call', 'type': 'function',
                    'function': {'name': 'file-write', 'arguments': json.dumps({'path': 'actual.txt', 'text': 'ACTUAL-ONCE', 'expected_sha256': None})}}]}
                reason = 'tool_calls'
            def frame(delta, finish):
                return {'id': 'synthetic-response', 'object': 'chat.completion.chunk', 'created': 1,
                        'model': 'synthetic-local', 'choices': [{'index': 0, 'delta': delta, 'finish_reason': finish}]}
            content = (('data: ' + json.dumps(frame(delta, None)) + '\n\n') +
                       ('data: ' + json.dumps(frame({}, reason)) + '\n\n') + 'data: [DONE]\n\n').encode()
            kind = 'text/event-stream'
        else:
            self.send_error(404); return
        self.send_response(200)
        self.send_header('Content-Type', kind); self.send_header('Content-Length', str(len(content)))
        self.end_headers(); self.wfile.write(content); self.wfile.flush()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--node', default=shutil.which('node'))
    parser.add_argument('--worker', type=Path, default=ROOT / 'runtime/engine/worker.mjs')
    args = parser.parse_args()
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix='toddy-engine-protocol-') as directory:
        base = Path(directory); endpoint = base / 'server.sock'
        server = Server(str(endpoint), Handler)
        server.credential = 'dummy-private-fixture-token'
        server.generations = 0
        thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
        try:
            profile = json.loads((ROOT / 'config/phase2/profile/config.json').read_text())
            profile['provider'] = {'mode': 'local', 'adapter_id': 'local-llama-cpp', 'model_id': 'synthetic-local',
                'connection_ref': 'private-local', 'allow_remote_fallback': False}
            profile['tools']['enabled'] = ['file-write']; profile['budgets']['max_output_tokens'] = 256
            profile['budgets']['max_tool_calls'] = 2
            bootstrap = {'version': 1, 'profile_revision': 'a' * 64, 'profile': profile,
                'connection': {'id': 'private-local', 'socket_path': str(endpoint), 'model_id': 'synthetic-local', 'credential': server.credential},
                'catalog': {'synthetic-local': {'adapter_id': 'local-llama-cpp', 'qualified': True,
                    'context_tokens': 4096, 'max_output_tokens': 256}},
                'system_prompt': 'Call file-write once, report its verified outcome.', 'remote_consent': False,
                'tools': [{'name': 'file-write', 'label': 'Write fixture', 'description': 'Broker-owned actual temporary file write.',
                    'parameters': {'type': 'object', 'properties': {'path': {'type': 'string'}, 'text': {'type': 'string'},
                        'expected_sha256': {'type': ['string', 'null']}},
                        'required': ['path', 'text', 'expected_sha256'], 'additionalProperties': False}}]}
            adapter = EngineAdapter(args.node, args.worker)
            effects, texts = [], []
            def tool(call_id, name, arguments):
                assert call_id == 'tool-1' and name == 'file-write'
                assert arguments == {'path': 'actual.txt', 'text': 'ACTUAL-ONCE', 'expected_sha256': None}
                target = base / 'actual.txt'
                descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                with os.fdopen(descriptor, 'w') as output:
                    output.write(arguments['text']); output.flush(); os.fsync(output.fileno())
                assert target.read_text() == 'ACTUAL-ONCE'
                effects.append(call_id)
                return {'outcome': 'verified', 'content': 'Verified actual file content ACTUAL-ONCE.'}
            result = adapter.run(bootstrap, 'run-one', 'request-one', 'Use the actual broker file tool.', on_tool=tool, on_text=texts.append)
            assert result['state'] == 'completed' and result['tool_calls'] == 1
            assert effects == ['tool-1'] and 'Verified actual broker file write.' in ''.join(texts)
            assert server.credential not in json.dumps(result) + ''.join(texts)
            print(json.dumps({'scope': 'actual production worker/private FD/Pi/Unix HTTP synthetic protocol; no real model/provider/native guest qualification',
                'uid': os.getuid(), 'actual_file_effects': len(effects), 'actual_file_sha256': hashlib.sha256((base / 'actual.txt').read_bytes()).hexdigest(),
                'streamed_text': bool(texts), 'generation_requests': server.generations,
                'private_connection_absent_from_model_and_output': True, 'worker_state': result['state'],
                'duration_seconds': round(time.monotonic() - started, 3)}))
        finally:
            server.shutdown(); server.server_close(); thread.join(timeout=3)


if __name__ == '__main__':
    main()
