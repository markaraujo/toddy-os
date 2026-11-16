"""Managed real engine worker: private FD bootstrap and bounded v1 framed events.

Caller owns validated profile/connection consent, canonical journal and effects.
Only trusted broker callbacks may return verified tool postconditions. A worker
'done' event proves no native effect by itself and never resumes an old task.
"""
import fcntl
import json
import os
from pathlib import Path
import selectors
import signal
import stat
import subprocess
import sys
import time

try:
    from .protocol import MAX_FRAME, encode, strict_json
except ImportError:
    from protocol import MAX_FRAME, encode, strict_json


class EngineError(RuntimeError):
    pass


def _id(value):
    import re
    return isinstance(value, str) and re.fullmatch(r'[a-z][a-z0-9-]{0,63}', value) is not None


class EngineAdapter:
    def __init__(self, node='/usr/bin/node', worker=None):
        self.node = str(node)
        runtime_root = Path(__file__).resolve().parents[1]
        source_worker = runtime_root / 'engine/worker.mjs'
        self.worker = Path(worker) if worker else source_worker if source_worker.is_file() else runtime_root / 'worker/worker.mjs'
        if (os.getuid() == 0 or not Path(self.node).is_absolute() or not self.worker.is_absolute()
                or self.worker.resolve() != self.worker):
            raise EngineError('unsafe_engine_invocation')

    @staticmethod
    def _bootstrap_fd(bootstrap):
        try:
            body = json.dumps(bootstrap, ensure_ascii=False, allow_nan=False,
                              separators=(',', ':')).encode()
            strict_json(body)
        except (ValueError, UnicodeError, RecursionError, OverflowError):
            raise EngineError('invalid_engine_bootstrap') from None
        if not 0 < len(body) <= 65536:
            raise EngineError('engine_bootstrap_limit')
        descriptor = os.memfd_create('toddy-engine-bootstrap', os.MFD_CLOEXEC | os.MFD_ALLOW_SEALING)
        try:
            os.fchmod(descriptor, 0o600)
            view = memoryview(body)
            while view:
                view = view[os.write(descriptor, view):]
            os.lseek(descriptor, 0, os.SEEK_SET)
            fcntl.fcntl(descriptor, fcntl.F_ADD_SEALS,
                        fcntl.F_SEAL_WRITE | fcntl.F_SEAL_GROW | fcntl.F_SEAL_SHRINK | fcntl.F_SEAL_SEAL)
            return descriptor
        except BaseException:
            os.close(descriptor)
            raise

    def run(self, bootstrap, task_id, request_id, input_text, *, on_tool, on_text=lambda _text: None,
            canceled=lambda: False):
        if not _id(task_id) or not _id(request_id) or not isinstance(input_text, str):
            raise EngineError('invalid_engine_run')
        if not 0 < len(input_text.encode()) <= 16384:
            raise EngineError('engine_input_limit')
        budget = bootstrap.get('profile', {}).get('budgets', {}).get('task_deadline_seconds')
        if type(budget) is not int or not 1 <= budget <= 3600:
            raise EngineError('invalid_engine_deadline')
        if canceled():
            return {'state': 'canceled', 'code': 'canceled', 'tool_calls': 0, 'text_bytes': 0}
        credential = bootstrap.get('connection', {}).get('credential')
        if not isinstance(credential, str) or not credential:
            raise EngineError('credential_unavailable')
        def contains_secret(value):
            if isinstance(value, str):
                return credential in value
            if isinstance(value, dict):
                return any(contains_secret(key) or contains_secret(item) for key, item in value.items())
            if isinstance(value, list):
                return any(contains_secret(item) for item in value)
            return False
        if contains_secret(input_text) or contains_secret({key: value for key, value in bootstrap.items() if key != 'connection'}):
            raise EngineError('credential_in_model_input')
        pending_text = ''
        descriptor = self._bootstrap_fd(bootstrap)
        launcher = Path(__file__).resolve().parents[1] / 'tools/child.py'
        try:
            process = subprocess.Popen([sys.executable, str(launcher), str(os.getpid()), self.node, str(self.worker)],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                cwd='/', pass_fds=(descriptor,), close_fds=True, start_new_session=True, umask=0o077,
                env={'PATH': '/usr/bin:/usr/sbin', 'HOME': '/nonexistent', 'LANG': 'C.UTF-8',
                     'LC_ALL': 'C.UTF-8', 'TODDY_BOOTSTRAP_FD': str(descriptor)})
        finally:
            os.close(descriptor)
        started = time.monotonic()
        deadline = started + budget
        incoming = bytearray()
        stderr_bytes = 0
        sequence = 0
        outgoing = 0
        calls = 0
        text_bytes = 0
        cancel_sent = False
        cancel_deadline = None
        startup_canceled = False
        known_tools = {tool['name'] for tool in bootstrap.get('tools', ())}
        selector = selectors.DefaultSelector()
        selector.register(process.stdout, selectors.EVENT_READ, 'stdout')
        selector.register(process.stderr, selectors.EVENT_READ, 'stderr')
        os.set_blocking(process.stdin.fileno(), False)
        base = {'version': 1, 'worker_id': 'worker-runtime', 'run_id': task_id, 'request_id': request_id}

        def send(kind, fields):
            nonlocal outgoing
            outgoing += 1
            data = memoryview(encode({**base, 'kind': kind, 'seq': outgoing, **fields}))
            write_deadline = time.monotonic() + 5
            while data:
                try:
                    count = os.write(process.stdin.fileno(), data)
                    data = data[count:]
                except BlockingIOError:
                    if time.monotonic() >= write_deadline or process.poll() is not None:
                        raise EngineError('engine_write_unavailable') from None
                    import select
                    select.select([], [process.stdin.fileno()], [], .05)
                except BrokenPipeError:
                    raise EngineError('engine_disconnected') from None

        def next_frame(bound, *, monitor_cancel=False, startup=False):
            nonlocal stderr_bytes, cancel_sent, cancel_deadline
            while True:
                if startup and canceled():
                    raise EngineError('engine_canceled_before_run')
                if len(incoming) >= 4:
                    size = int.from_bytes(incoming[:4], 'big')
                    if not 0 < size <= MAX_FRAME:
                        raise EngineError('engine_frame_limit')
                    if len(incoming) >= size + 4:
                        body = bytes(incoming[4:4 + size]); del incoming[:4 + size]
                        try:
                            return strict_json(body)
                        except (ValueError, UnicodeError, RecursionError, OverflowError):
                            raise EngineError('engine_invalid_json') from None
                now = time.monotonic()
                if monitor_cancel and not cancel_sent and (canceled() or now >= deadline):
                    send('cancel', {})
                    cancel_sent = True; cancel_deadline = now + 2
                effective = min(bound, cancel_deadline) if cancel_deadline is not None else bound
                if now >= effective:
                    raise EngineError('engine_cancel_deadline' if cancel_sent else 'engine_deadline')
                events = selector.select(min(.05, effective - now))
                for key, _ in events:
                    chunk = os.read(key.fileobj.fileno(), 4096)
                    if not chunk:
                        selector.unregister(key.fileobj)
                        if key.data == 'stdout':
                            raise EngineError('engine_disconnected')
                    elif key.data == 'stderr':
                        # Discard raw SDK diagnostics rather than guess redaction.
                        stderr_bytes += len(chunk)
                        if stderr_bytes > 65536:
                            raise EngineError('engine_stderr_limit')
                    else:
                        incoming.extend(chunk)
                        if len(incoming) > MAX_FRAME + 4:
                            raise EngineError('engine_frame_limit')
                if not events and process.poll() is not None:
                    raise EngineError('engine_disconnected')

        try:
            hello = next_frame(min(started + 5, deadline),startup=True)
            if (not isinstance(hello, dict) or set(hello) != {'version', 'kind', 'worker_id', 'capabilities', 'max_frame'}
                    or hello['version'] != 1 or hello['kind'] != 'hello' or hello['worker_id'] != 'worker-runtime'
                    or hello['max_frame'] != MAX_FRAME or hello['capabilities'] !=
                    ['agent-runtime-v1', 'runtime-tool-result-v1', 'single-run', 'cancel']):
                raise EngineError('engine_capability_mismatch')
            if canceled():raise EngineError('engine_canceled_before_run')
            send('run', {'input': input_text, 'profile_revision': bootstrap['profile_revision']})
            while True:
                event = next_frame(deadline + 2, monitor_cancel=True)
                common = {'version', 'kind', 'worker_id', 'run_id', 'request_id', 'seq'}
                if not isinstance(event, dict):
                    raise EngineError('engine_invalid_event')
                extra = {'text': {'text'}, 'tool_request': {'tool_call_id', 'tool', 'arguments'},
                         'done': {'state', 'code'}}.get(event.get('kind'))
                if (extra is None or set(event) != common | extra or event['version'] != 1
                        or event['worker_id'] != base['worker_id'] or event['run_id'] != task_id
                        or event['request_id'] != request_id or type(event['seq']) is not int
                        or event['seq'] != sequence + 1 or event['seq'] > 2**53 - 1):
                    raise EngineError('engine_event_identity')
                sequence = event['seq']
                if event['kind'] == 'text':
                    if not isinstance(event['text'], str):
                        raise EngineError('engine_invalid_text')
                    text_bytes += len(event['text'].encode())
                    if text_bytes > 262144:
                        raise EngineError('engine_text_limit')
                    if not cancel_sent:
                        pending_text += event['text']
                        if credential in pending_text:
                            raise EngineError('credential_in_model_output')
                        keep = len(credential) - 1
                        if len(pending_text) > keep:
                            ready = pending_text[:-keep] if keep else pending_text
                            pending_text = pending_text[-keep:] if keep else ''
                            if ready:
                                on_text(ready)
                elif event['kind'] == 'tool_request':
                    calls += 1
                    if (event['tool'] not in known_tools or not _id(event['tool_call_id'])
                            or not isinstance(event['arguments'], dict)
                            or len(json.dumps(event['arguments']).encode()) > 65536
                            or calls > bootstrap['profile']['budgets']['max_tool_calls']):
                        raise EngineError('engine_tool_limit')
                    if cancel_sent or canceled() or time.monotonic() >= deadline:
                        result = {'outcome': 'rejected', 'content': 'Task stopped; no new tool dispatched.'}
                    else:
                        try:
                            result = on_tool(event['tool_call_id'], event['tool'], event['arguments'])
                        except Exception:
                            result = {'outcome': 'uncertain', 'content': 'Tool outcome requires review; do not repeat it.'}
                    if (not isinstance(result, dict) or set(result) != {'outcome', 'content'}
                            or result['outcome'] not in {'verified', 'rejected', 'uncertain'}
                            or not isinstance(result['content'], str) or len(result['content'].encode()) > 262144):
                        raise EngineError('engine_tool_result_invalid')
                    secret_result = contains_secret(result['content'])
                    try:
                        secret_result = secret_result or contains_secret(strict_json(result['content'].encode()))
                    except (ValueError, UnicodeError, RecursionError, OverflowError):
                        pass
                    if secret_result:
                        result = {'outcome': 'rejected', 'content': 'Protected credential content was excluded from tool output.'}
                    send('tool_result', {'tool_call_id': event['tool_call_id'], **result})
                else:
                    if event['state'] not in {'completed', 'failed', 'canceled'} or not isinstance(event['code'], str):
                        raise EngineError('engine_terminal_invalid')
                    # Only the independently tested worker's fixed classification
                    # is returned; untrusted code cannot inject arbitrary logs.
                    import re
                    if not re.fullmatch(r'[a-z][a-z0-9_]{0,63}', event['code']):
                        raise EngineError('engine_terminal_invalid')
                    if pending_text and not cancel_sent:
                        on_text(pending_text)
                        pending_text = ''
                    process.stdin.close()
                    try:
                        exit_code = process.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        raise EngineError('engine_exit_unverified') from None
                    if exit_code != 0:
                        raise EngineError('engine_exit_unverified')
                    return {'state': 'canceled' if cancel_sent and event['state'] == 'completed' else event['state'],
                            'code': 'canceled' if cancel_sent and event['state'] == 'completed' else event['code'],
                            'tool_calls': calls, 'text_bytes': text_bytes}
        except EngineError as error:
            if str(error)!='engine_canceled_before_run':raise
            startup_canceled=True
            return {'state':'canceled','code':'canceled','tool_calls':0,'text_bytes':0}
        finally:
            selector.close()
            process.stdin.close()
            if startup_canceled and process.poll() is None:
                # No run frame/tool effect was admitted. Stop startup directly;
                # a stalled hello must not postpone owner cancellation.
                try:os.killpg(process.pid,signal.SIGKILL)
                except ProcessLookupError:pass
            # The engine executes no native effects; native writes remain in the
            # independent journal/executor and are not killed to meet this bound.
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait(timeout=3)
            process.stdout.close(); process.stderr.close()
