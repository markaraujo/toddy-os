"""B03 actual native CPU inference/auth/egress fixture; no tool/UI/root claim."""
import errno
import json
import os
from pathlib import Path
import resource
import secrets
import signal
import socket
import stat
import subprocess
import time
import urllib.error
import urllib.request


def main():
    assert os.getuid() == 101
    status = dict(line.split(':', 1) for line in Path('/proc/self/status').read_text().splitlines() if ':' in line)
    assert int(status['CapEff'], 16) == 0 and int(status['CapPrm'], 16) == 0
    assert status['NoNewPrivs'].strip() == '1'
    with socket.socket() as external:
        external.settimeout(1)
        try:
            external.connect(('1.1.1.1', 443))
        except OSError as error:
            assert error.errno == errno.ENETUNREACH
        else:
            raise AssertionError('External route unexpectedly available')
    model = json.loads(Path('/src/model-input.json').read_text())
    assert Path('/src/model.gguf').stat().st_size == model['bytes']
    key = secrets.token_hex(32)
    keyfile = Path('/build/inference-key')
    descriptor = os.open(keyfile, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, 'w') as output:
        output.write(key+'\n')
    assert stat.S_IMODE(keyfile.stat().st_mode) == 0o600
    with socket.socket() as allocation:
        allocation.bind(('127.0.0.1', 0))
        port = allocation.getsockname()[1]
    origin = f'http://127.0.0.1:{port}'
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    cpus = sorted(os.sched_getaffinity(0))[:4]
    assert len(cpus) == 4

    def child_limits():
        os.sched_setaffinity(0, cpus)
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
        resource.setrlimit(resource.RLIMIT_AS, (8192*1024**2, 8192*1024**2))

    command = ['/usr/bin/llama-server', '-m', '/src/model.gguf', '--alias', 'toddy-qwen3-1.7b-q8_0',
               '--host', '127.0.0.1', '--port', str(port), '--api-key-file', str(keyfile),
               '--threads', '4', '--threads-batch', '4', '--threads-http', '2',
               '--parallel', '1', '--ctx-size', '4096', '--batch-size', '512', '--ubatch-size', '128',
               '--n-gpu-layers', '0', '--offline', '--no-slots', '--no-webui', '--poll', '0',
               '--chat-template-kwargs', '{"enable_thinking":false}', '--log-disable']
    logfd = os.open('/build/inference-server.log', os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    started = time.monotonic()
    process = None
    report = None
    forced = False
    try:
        with os.fdopen(logfd, 'wb') as log:
            process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, preexec_fn=child_limits)
        deadline = started+120
        while True:
            assert process.poll() is None, 'Model process exited before readiness'
            assert time.monotonic() < deadline, 'Model readiness deadline exceeded'
            try:
                with opener.open(urllib.request.Request(origin+'/health', headers={'Authorization':'Bearer '+key}), timeout=1) as response:
                    if response.status == 200:
                        break
            except (urllib.error.URLError, TimeoutError):
                pass
            time.sleep(.25)
        loaded = time.monotonic()
        request_body = {'model': 'toddy-qwen3-1.7b-q8_0', 'max_tokens': 32, 'temperature': 0,
                        'messages': [{'role': 'user', 'content': 'Respond with exactly READY and nothing else. /no_think'}],
                        'chat_template_kwargs': {'enable_thinking': False}}

        def request(body, credential):
            headers = {'Content-Type': 'application/json'}
            if credential is not None:
                headers['Authorization'] = 'Bearer '+credential
            return urllib.request.Request(origin+'/v1/chat/completions', data=json.dumps(body).encode(), headers=headers)

        denied = []
        for credential in [None, 'wrong-fixture-token']:
            try:
                with opener.open(request(request_body, credential), timeout=5):
                    raise AssertionError('Unauthorized generation accepted')
            except urllib.error.HTTPError as error:
                assert error.code in {401, 403}
                denied.append(error.code)
                error.close()
        request_body.update(stream=True, stream_options={'include_usage': True})
        generated = time.monotonic()
        first_token = None
        text = ''
        usage = None
        stream_done = False
        received = 0
        with opener.open(request(request_body, key), timeout=60) as response:
            while True:
                line = response.readline(65537)
                if not line:
                    break
                received += len(line)
                assert len(line) <= 65536 and received <= 256*1024
                if not line.startswith(b'data: '):
                    continue
                payload = line[6:].strip()
                if payload == b'[DONE]':
                    stream_done = True
                    break
                event = json.loads(payload)
                assert 'error' not in event, 'Local inference error'
                if event.get('usage'):
                    usage = {k: event['usage'].get(k) for k in ['prompt_tokens', 'completion_tokens', 'total_tokens']}
                for choice in event.get('choices', []):
                    delta = choice.get('delta', {}).get('content') or ''
                    assert isinstance(delta, str)
                    if delta and first_token is None:
                        first_token = time.monotonic()
                    text += delta
        assert stream_done and first_token is not None and text.strip() == 'READY', 'Required real streamed response missing'
        procstatus = Path(f'/proc/{process.pid}/status').read_text().splitlines()
        peak = int(next(line for line in procstatus if line.startswith('VmHWM:')).split()[1])
        assert peak <= 5120*1024, 'Measured model RSS exceeds candidate budget'
        assert key.encode() not in Path('/build/inference-server.log').read_bytes(), 'Do not publish credential-bearing diagnostics'
        report = {'scope': 'B03 native CPU inference/auth/egress only; no Pi tool/UI/executor acceptance',
                  'uid': os.getuid(), 'cap_effective': 0, 'no_new_privileges': True,
                  'llama_version': '0.9.0', 'model_sha256': model['sha256'],
                  'model_bytes': model['bytes'], 'model_license': model['license'],
                  'cpu_affinity_count': len(cpus), 'threads': 4, 'context_tokens': 4096, 'gpu_layers': 0,
                  'load_to_health_seconds': round(loaded-started, 3),
                  'request_first_text_seconds': round(first_token-generated, 3),
                  'request_complete_seconds': round(time.monotonic()-generated, 3),
                  'peak_model_rss_kib': peak, 'unauthorized_statuses': denied,
                  'external_network_errno': errno.ENETUNREACH, 'remote_fallback': False,
                  'stream_done': stream_done, 'expected_response': True, 'usage': usage}
    finally:
        if process is not None:
            if process.poll() is None:
                process.send_signal(signal.SIGTERM)
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                forced = True
                process.kill()
                process.wait()
        keyfile.unlink(missing_ok=True)
    assert not forced, 'Server shutdown required forced termination; not acceptance'
    assert report is not None
    report['server_exit'] = process.returncode
    report['credential_file_removed'] = not keyfile.exists()
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
