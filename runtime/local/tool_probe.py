"""Native per-user runtime lifecycle/Unix auth/Pi-agent real-tool integration."""
from contextlib import closing
import json
import os
from pathlib import Path
import secrets
import subprocess
import time

from server import LocalRuntime, UnixHTTPConnection


def main():
    assert os.getuid() == 101
    contract = json.loads(Path('/src/local-model.lock.json').read_text())
    runtime = LocalRuntime(contract, '/src/model.gguf', '/build/run')
    node = None
    report = None
    try:
        connection = runtime.start()
        private = runtime.directory
        assert private.stat().st_uid == os.getuid()
        assert (private.stat().st_mode & 0o777) == 0o700
        # Root test driver probes a different unprivileged UID without credentials.
        Path('/build/peer-ready.json').write_text(json.dumps({'component': private.name}))
        deadline = time.monotonic()+30
        while not Path('/build/peer-release').exists():
            assert time.monotonic() < deadline, 'Other-UID denial proof missing'
            time.sleep(.05)
        peer = json.loads(Path('/build/peer-release').read_text())
        assert peer['socket_errno'] == 13 and peer['key_errno'] == 13
        denied = []
        body = json.dumps({'model': connection.model_id, 'messages':[{'role':'user','content':'READY'}], 'max_tokens':1})
        for key in [None, 'wrong-fixture-token']:
            headers = {'Content-Type':'application/json'}
            if key is not None:
                headers['Authorization'] = 'Bearer '+key
            with closing(UnixHTTPConnection(connection.socket_path)) as client:
                client.request('POST', '/v1/chat/completions', body, headers)
                response = client.getresponse()
                response.read(4096)
                assert response.status in {401, 403}
                denied.append(response.status)
        fixture = Path('/build/disposable')
        fixture.mkdir(mode=0o700)
        # Harmless read/return task, not a long random-token copying benchmark.
        (fixture/'fixture.txt').write_text('TODDY-'+str(secrets.randbelow(9000)+1000))
        results = {}
        for script in ['local-tool-spike.mjs', 'local-cancel-spike.mjs']:
            readfd, writefd = os.pipe()
            try:
                node = subprocess.Popen(['/usr/bin/node','/src/runtime/engine/'+script],
                    stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    pass_fds=(readfd,), env={'PATH':'/usr/bin:/usr/sbin','HOME':'/build/home',
                        'LANG':'C.UTF-8','TODDY_CONNECTION_FD':str(readfd)})
                os.close(readfd)
                readfd = None
                os.write(writefd, json.dumps({'socket_path':connection.socket_path,
                    'model_id':connection.model_id,'credential':connection.credential}).encode())
            finally:
                if readfd is not None:
                    os.close(readfd)
                os.close(writefd)
            stdout, stderr = node.communicate(timeout=90)
            assert connection.credential.encode() not in stdout+stderr, 'Private credential in child output'
            if node.returncode:
                Path('/build/worker-code.json').write_bytes(stderr[:4096])
                raise AssertionError('Local worker failed; inspect private classified code')
            results[script] = json.loads(stdout)
        task = results['local-tool-spike.mjs']
        cancellation = results['local-cancel-spike.mjs']
        assert task['actual_tool_executions'] == 1 and task['actual_file_content_matched']
        assert cancellation['classified_code'] == 'canceled' and cancellation['overbudget_generation_requests'] == 0
        status = Path(f'/proc/{runtime.process.pid}/status').read_text().splitlines()
        peak = int(next(line for line in status if line.startswith('VmHWM:')).split()[1])
        assert peak <= 5120*1024
        report = {'scope':'actual local Pi tool/runtime lifecycle; not durable service/root/UI acceptance',
                  'uid':os.getuid(),'transport':'private0700-directory Unix socket + ephemeral bearer',
                  'other_uid':peer['uid'],'other_uid_socket_errno':peer['socket_errno'],
                  'other_uid_key_errno':peer['key_errno'],'unauthorized_statuses':denied,
                  'load_and_integrity_seconds':round(runtime.load_seconds,3),'peak_model_rss_kib':peak,
                  'task':task,'cancellation_and_context':cancellation}
    finally:
        if node is not None and node.poll() is None:
            node.kill()
            node.wait()
        stopped = runtime.stop()
    assert stopped and stopped['exit'] == 0 and not stopped['forced'] and stopped['private_state_removed']
    assert runtime.stop() == stopped, 'Stop must be idempotent after reconciliation'
    assert report is not None
    report['stop'] = stopped
    report['second_stop'] = 'same reconciled result'
    print(json.dumps(report,indent=2))


if __name__ == '__main__':
    main()
