"""Fail-closed local stdio MCP 2025-06-18 subset in Bubblewrap confinement.

Only explicitly enabled pinned Python bundles/read-only tool calls are qualified
by this slice. Network, arbitrary hooks, provider credentials, client sampling,
roots, resources, prompts and external connectors remain unavailable.
"""
import copy
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import select
import signal
import stat
import subprocess
import tempfile
import threading
import time

VERSION = '2025-06-18'
MAX_FRAME = 256 * 1024
MAX_BUNDLE = 8 * 1024 * 1024
NAME = re.compile(r'[a-z][a-z0-9-]{0,63}\Z')
HASH = re.compile(r'[0-9a-f]{64}\Z')


class PluginError(ValueError):
    pass


def name(value):
    if not isinstance(value, str) or not NAME.fullmatch(value):
        raise PluginError('plugin_name')
    return value


def relative(value):
    if not isinstance(value, str) or len(value) > 256 or '\\' in value or '\x00' in value or not value:
        raise PluginError('plugin_path')
    path = PurePosixPath(value)
    if path.is_absolute() or any(p in ('', '.', '..') for p in value.split('/')):
        raise PluginError('plugin_path')
    return value


def strict_json(data):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise PluginError('plugin_duplicate_json')
            result[key] = value
        return result
    def constant(_):
        raise PluginError('plugin_nonfinite_json')
    if not isinstance(data, bytes) or not 0 < len(data) <= MAX_FRAME:
        raise PluginError('plugin_frame_limit')
    try:
        value = json.loads(data.decode('utf-8', errors='strict'), object_pairs_hook=pairs, parse_constant=constant)
        def check(item, depth=0):
            if depth > 32:
                raise PluginError('plugin_json_depth')
            if isinstance(item, str):
                item.encode('utf-8', errors='strict')
            elif isinstance(item, dict):
                for key, child in item.items():
                    check(key, depth + 1)
                    check(child, depth + 1)
            elif isinstance(item, list):
                for child in item:
                    check(child, depth + 1)
            elif isinstance(item, (int, float)) and not isinstance(item, bool):
                if not -2**53 + 1 <= item <= 2**53 - 1 or not math.isfinite(item):
                    raise PluginError('plugin_json_number')
        check(value)
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise PluginError('plugin_invalid_json') from exc
    return value


def validate_manifest(document):
    if not isinstance(document, dict) or set(document) != {'plugin_version', 'id', 'entry', 'files', 'capabilities', 'tools'} or type(document['plugin_version']) is not int or document['plugin_version'] != 1:
        raise PluginError('plugin_manifest_schema')
    name(document['id'])
    relative(document['entry'])
    if document['capabilities'] != ['mcp.tools.read']:
        raise PluginError('plugin_capability_denied')
    files = document['files']
    if not isinstance(files, dict) or not 1 <= len(files) <= 128 or document['entry'] not in files or not document['entry'].endswith('.py'):
        raise PluginError('plugin_files')
    for path, digest in files.items():
        relative(path)
        if not isinstance(digest, str) or not HASH.fullmatch(digest):
            raise PluginError('plugin_file_hash')
    tools = document['tools']
    if not isinstance(tools, dict) or not 1 <= len(tools) <= 32:
        raise PluginError('plugin_tools')
    for tool, arguments in tools.items():
        name(tool)
        if not isinstance(arguments, list) or len(arguments) > 16:
            raise PluginError('plugin_arguments')
        for argument in arguments:
            name(argument)
        if len(arguments) != len(set(arguments)):
            raise PluginError('plugin_arguments')
    return copy.deepcopy(document)


def _read_regular(root_fd, path, maximum):
    """Open every path component relative to a held root without symlinks."""
    parts = relative(path).split('/')
    fd = os.dup(root_fd)
    try:
        for part in parts[:-1]:
            next_fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = next_fd
        file_fd = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
        try:
            metadata = os.fstat(file_fd)
            if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1 or metadata.st_size > maximum:
                raise PluginError('plugin_regular_file_limit')
            with os.fdopen(file_fd, 'rb', closefd=False) as stream:
                data = stream.read(maximum + 1)
            if len(data) > maximum:
                raise PluginError('plugin_file_limit')
            return data
        finally:
            os.close(file_fd)
    except OSError as exc:
        raise PluginError('plugin_bundle_path') from exc
    finally:
        os.close(fd)


class Plugin:
    """One registered profile-local plugin, disabled at discovery and update.

    The broker binds this object to its authenticated user/profile; manifest text
    cannot authorize activation. No keyring handle or provider env enters it.
    """
    def __init__(self, manifest, bundle, *, bwrap='/usr/bin/bwrap'):
        self.manifest = validate_manifest(manifest)
        self.bundle = Path(bundle)
        self.bwrap = bwrap
        self.enabled = False
        self.generation = 0
        self._process = None
        self._state_lock = threading.RLock()
        self._call_lock = threading.Lock()

    def enable(self, *, authorize):
        with self._state_lock:
            if self._process is not None and self._process.poll() is None:
                raise PluginError('plugin_process_still_active')
            if not authorize(self.manifest['id'], tuple(self.manifest['capabilities'])):
                raise PluginError('plugin_owner_authorization_required')
            self.enabled = True
            self.generation += 1

    def revoke(self):
        with self._state_lock:
            self.enabled = False
            self.generation += 1
            if self._process is not None:
                self._kill(self._process)

    def remove(self):
        self.revoke()
        # Only registration is removed; never delete owner-selected bundle paths.
        self.bundle = None

    def _kill(self, process):
        if process.poll() is None:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass

    def _check(self, generation, deadline, stop):
        with self._state_lock:
            if not self.enabled or generation != self.generation:
                raise PluginError('plugin_revoked')
        if stop is not None and stop.is_set():
            raise PluginError('plugin_stopped')
        if time.monotonic() >= deadline:
            raise PluginError('plugin_timeout')

    def _snapshot(self, destination):
        if self.bundle is None:
            raise PluginError('plugin_removed')
        try:
            fd = os.open(self.bundle, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        except OSError as exc:
            raise PluginError('plugin_bundle_path') from exc
        try:
            remaining = MAX_BUNDLE
            for path, expected in self.manifest['files'].items():
                data = _read_regular(fd, path, remaining)
                remaining -= len(data)
                if hashlib.sha256(data).hexdigest() != expected:
                    raise PluginError('plugin_integrity')
                target = destination / path
                target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
                target.write_bytes(data)
                target.chmod(0o400)
        finally:
            os.close(fd)

    def _command(self, snapshot):
        # No --try flags: failed confinement leaves code disabled. Host /run,
        # /etc, /home, workspaces, sockets and source bundle paths are absent.
        return [self.bwrap, '--unshare-all', '--unshare-user', '--disable-userns', '--die-with-parent',
                '--new-session', '--cap-drop', 'ALL', '--clearenv',
                '--setenv', 'HOME', '/tmp', '--setenv', 'PATH', '/usr/bin',
                '--ro-bind', '/usr', '/usr', '--ro-bind', '/lib64', '/lib64',
                '--symlink', 'usr/bin', '/bin', '--symlink', 'usr/lib', '/lib',
                '--proc', '/proc', '--dev', '/dev', '--size', str(16 * 1024 * 1024), '--tmpfs', '/tmp',
                '--ro-bind', str(snapshot), '/plugin',
                '--ro-bind', str(Path(__file__).with_name('limits.py').resolve()), '/limits.py',
                '--chdir', '/plugin', '/usr/bin/python3', '-I', '-B', '/limits.py', '/plugin/' + self.manifest['entry']]

    def call(self, tool, arguments, *, authorize, timeout=5, stop=None):
        """One bounded fresh MCP connection. Tool output remains untrusted data."""
        name(tool)
        if tool not in self.manifest['tools']:
            raise PluginError('plugin_tool_denied')
        if not isinstance(arguments, dict) or set(arguments) != set(self.manifest['tools'][tool]):
            raise PluginError('plugin_tool_arguments')
        try:
            if any(not isinstance(v, str) or len(v.encode('utf-8')) > 4096 for v in arguments.values()):
                raise PluginError('plugin_tool_arguments')
        except UnicodeError as exc:
            raise PluginError('plugin_tool_arguments') from exc
        if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not .05 <= timeout <= 30:
            raise PluginError('plugin_deadline')
        if not self._call_lock.acquire(blocking=False):
            raise PluginError('plugin_busy')
        process = None
        try:
            with self._state_lock:
                generation = self.generation
            deadline = time.monotonic() + timeout
            self._check(generation, deadline, stop)
            if not authorize(self.manifest['id'], tuple(self.manifest['capabilities'])):
                self.revoke()
                raise PluginError('plugin_current_authorization_required')
            with tempfile.TemporaryDirectory(prefix='toddy-plugin-') as directory:
                snapshot = Path(directory) / 'bundle'
                snapshot.mkdir(mode=0o700)
                self._snapshot(snapshot)
                self._check(generation, deadline, stop)
                with self._state_lock:
                    self._check(generation, deadline, stop)
                    try:
                        process = subprocess.Popen(self._command(snapshot), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.DEVNULL, env={}, close_fds=True, start_new_session=True, bufsize=0)
                    except OSError as exc:
                        raise PluginError('plugin_confinement_unavailable') from exc
                    self._process = process
                os.set_blocking(process.stdin.fileno(), False)
                os.set_blocking(process.stdout.fileno(), False)
                buffered = bytearray()
                count = 0
                def send(message):
                    data = json.dumps(message, ensure_ascii=False, allow_nan=False, separators=(',', ':')).encode() + b'\n'
                    if len(data) > MAX_FRAME:
                        raise PluginError('plugin_frame_limit')
                    view = memoryview(data)
                    while view:
                        self._check(generation, deadline, stop)
                        if select.select([], [process.stdin], [], .02)[1]:
                            try:
                                written = os.write(process.stdin.fileno(), view[:4096])
                            except (BrokenPipeError, OSError) as exc:
                                raise PluginError('plugin_transport_closed') from exc
                            view = view[written:]
                def request(sequence, method, params):
                    nonlocal count
                    send({'jsonrpc': '2.0', 'id': sequence, 'method': method, 'params': params})
                    while True:
                        self._check(generation, deadline, stop)
                        if b'\n' not in buffered:
                            if not select.select([process.stdout], [], [], .02)[0]:
                                continue
                            data = os.read(process.stdout.fileno(), 4096)
                            if not data:
                                raise PluginError('plugin_transport_closed_or_confinement_failed')
                            buffered.extend(data)
                            if len(buffered) > MAX_FRAME:
                                raise PluginError('plugin_frame_limit')
                            continue
                        line, _, rest = buffered.partition(b'\n')
                        buffered[:] = rest
                        count += 1
                        if count > 32:
                            raise PluginError('plugin_message_limit')
                        message = strict_json(bytes(line))
                        if not isinstance(message, dict) or message.get('jsonrpc') != '2.0' or type(message.get('id')) is not int or message.get('id') != sequence or 'method' in message or set(message) != {'jsonrpc', 'id', 'result'}:
                            raise PluginError('plugin_protocol_response')
                        return message['result']
                initialized = request(1, 'initialize', {'protocolVersion': VERSION, 'capabilities': {}, 'clientInfo': {'name': 'toddy-local', 'version': '1'}})
                if not isinstance(initialized, dict) or initialized.get('protocolVersion') != VERSION or not isinstance(initialized.get('capabilities'), dict) or 'tools' not in initialized['capabilities']:
                    raise PluginError('plugin_protocol_version_or_capability')
                # Server-supplied instructions/metadata never become owner policy.
                send({'jsonrpc': '2.0', 'method': 'notifications/initialized'})
                listing = request(2, 'tools/list', {})
                if not isinstance(listing, dict) or set(listing) != {'tools'} or not isinstance(listing['tools'], list) or len(listing['tools']) > 32:
                    raise PluginError('plugin_tool_listing')
                advertised = [item.get('name') if isinstance(item, dict) else None for item in listing['tools']]
                for advertised_name in advertised:
                    name(advertised_name)
                if set(advertised) != set(self.manifest['tools']) or len(advertised) != len(set(advertised)):
                    raise PluginError('plugin_tool_listing')
                result = request(3, 'tools/call', {'name': tool, 'arguments': arguments})
                if not isinstance(result, dict) or set(result) - {'content', 'isError'} or not isinstance(result.get('content'), list) or len(result['content']) > 16 or type(result.get('isError', False)) is not bool:
                    raise PluginError('plugin_tool_result')
                for item in result['content']:
                    if not isinstance(item, dict) or set(item) != {'type', 'text'} or item['type'] != 'text' or not isinstance(item['text'], str):
                        raise PluginError('plugin_tool_result')
                self._check(generation, deadline, stop)
                return {'untrusted': True, 'plugin_id': self.manifest['id'], 'content': result['content'], 'isError': result.get('isError', False)}
        finally:
            try:
                if process is not None:
                    self._kill(process)
                    try:
                        process.wait(timeout=2)
                    except subprocess.TimeoutExpired as exc:
                        with self._state_lock:
                            self.enabled = False
                        raise PluginError('plugin_stop_uncertain') from exc
                    finally:
                        process.stdin.close()
                        process.stdout.close()
            finally:
                with self._state_lock:
                    if process is None or process.poll() is not None:
                        self._process = None
                self._call_lock.release()
