"""Real native tool routing behind the authenticated session service.

This initial entry advertises native-tools only, never a working model backend.
Profile selection cannot grant root: every root call goes through Executor1.
"""
import hashlib
import json
import os
from pathlib import Path
import sys

try:
    from .protocol import strict_json
    from .tasks import TaskError
except ImportError:
    from protocol import strict_json
    from tasks import TaskError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.native import Tools, ToolError


class BrokerError(ValueError):
    pass


NATIVE_TOOLS = {'system-info', 'file-read', 'file-write', 'shell',
                'admin-config', 'admin-command', 'package', 'service', 'network'}
ROOT_KINDS = {'admin-config': 'config_replace', 'admin-command': 'root_command',
              'package': 'package_transaction', 'service': 'service_operation',
              'network': 'network_operation'}


class BrokerCore:
    def __init__(self, profiles, journal, workspace, *, root_client=None, dispatch_allowed=lambda: False):
        if os.getuid() == 0 or os.geteuid() == 0:
            raise BrokerError('unprivileged_broker_required')
        self.profiles, self.journal = profiles, journal
        self.workspace = Path(workspace)
        self.root_client = root_client
        self.dispatch_allowed = dispatch_allowed
        # Validate workspace immediately, no implicit host directory choice.
        with Tools(self.workspace):
            pass

    def capabilities(self):
        revision = self.profiles.current()
        config = strict_json(self.profiles.snapshot(revision)['config.json'])
        return {'version': 1, 'profile_schema': 1, 'store_version': 1,
                'profile_id': self.profiles.profile_id, 'profile_revision': revision,
                'features': ['native-tools', 'durable-tasks', 'cancel', 'profiles'],
                'agent_backend': False,
                'tools': sorted(set(config['tools']['enabled']) & NATIVE_TOOLS)}

    def validate_input(self, revision, encoded):
        if not isinstance(encoded, str) or len(encoded.encode()) > 65536:
            raise BrokerError('task_input_limit')
        try:
            request = strict_json(encoded.encode())
        except (ValueError, UnicodeError, RecursionError, OverflowError):
            raise BrokerError('invalid_task_input') from None
        if (not isinstance(request, dict) or set(request) != {'version', 'text', 'tool'}
                or type(request['version']) is not int or request['version'] != 1
                or not isinstance(request['text'], str) or not 0 < len(request['text'].encode()) <= 16384
                or not isinstance(request['tool'], dict) or set(request['tool']) != {'kind', 'arguments'}):
            raise BrokerError('invalid_task_input')
        kind, arguments = request['tool']['kind'], request['tool']['arguments']
        if not isinstance(kind, str) or kind not in NATIVE_TOOLS or not isinstance(arguments, dict):
            raise BrokerError('tool_unavailable')
        config = strict_json(self.profiles.snapshot(revision)['config.json'])
        if kind not in config['tools']['enabled']:
            raise BrokerError('profile_tool_disabled')
        expected = {'system-info': set(), 'file-read': {'path'},
                    'file-write': {'path', 'text', 'expected_sha256'},
                    'shell': {'argv', 'timeout_seconds'}}.get(kind)
        if expected is not None and set(arguments) != expected:
            raise BrokerError('invalid_tool_arguments')
        # Tool-specific file/argv/root schemas are rechecked by their actual
        # adapter/executor immediately before effects; no arbitrary kwargs.
        return request

    def submit(self, request_id, revision, encoded):
        request = self.validate_input(revision, encoded)
        if not self.dispatch_allowed():
            raise BrokerError('interactive_session_unavailable')
        snapshot = self.journal.submit(request_id, revision, request['text'], request_metadata=request['tool'])
        return snapshot, request

    def execute(self, task_id, request):
        snapshot = self.journal.inspect(task_id)
        if snapshot['state'] != 'queued':
            return snapshot
        if not self.dispatch_allowed():
            self.journal.cancel(task_id)
            raise BrokerError('interactive_session_unavailable')
        # Revalidate pinned actual bytes and tool selection, not current profile.
        revision, _ = self.profiles.task_snapshot(task_id)
        self.validate_input(revision, json.dumps(request, separators=(',', ':')))
        self.journal.start(task_id)
        kind, arguments = request['tool']['kind'], request['tool']['arguments']
        operation_id = 'operation-' + task_id.removeprefix('task-')

        def apply(op, _kind, args):
            if not self.dispatch_allowed() or self.journal.inspect(task_id)['cancel_requested']:
                raise BrokerError('interactive_dispatch_stopped')
            canceled = lambda: self.journal.inspect(task_id)['cancel_requested'] or not self.dispatch_allowed()
            if kind == 'system-info':
                # Fixed read-only operation; no generated command/paths or model.
                kernel = os.uname()
                return {'verified': True, 'uid': os.getuid(), 'kernel': kernel.release,
                        'machine': kernel.machine}
            if kind in ROOT_KINDS:
                if self.root_client is None:
                    raise BrokerError('executor_unavailable')
                return self.root_client.dispatch(op, ROOT_KINDS[kind], args, canceled)
            with Tools(self.workspace) as tools:
                if kind == 'file-read':
                    return {'verified': True, **tools.read(args['path'])}
                if kind == 'file-write':
                    return tools.write(args['path'], args['text'], args['expected_sha256'])
                return tools.shell(args['argv'], timeout_seconds=args['timeout_seconds'], canceled=canceled)

        # Shell exit alone never proves arbitrary side effects. Such results stay
        # uncertain pending a separate trusted postcondition/review.
        self.journal.run_operation(task_id, operation_id, kind, arguments, apply,
                                   lambda result: isinstance(result, dict) and result.get('verified') is True,
                                   boundary='package' if kind == 'package' else 'interruptible')
        return self.journal.complete(task_id)

    def reconcile(self, task_id):
        snapshot = self.journal.inspect(task_id)
        operation_id = snapshot['operation_id']
        if not snapshot['result_uncertain'] or not operation_id or self.root_client is None:
            return snapshot
        operation = self.journal.operation(task_id, operation_id)
        if operation['kind'] not in ROOT_KINDS:
            return snapshot
        def inspect_effect(op, _kind):
            result = self.root_client.inspect(op)
            return (result.get('state') == 'completed' and isinstance(result.get('result'), dict)
                    and result['result'].get('verified') is True)
        record = self.journal.reconcile(task_id, operation_id, inspect_effect)
        if record['state'] == 'completed':
            current = self.journal.inspect(task_id)
            return self.journal.complete(task_id) if current['state'] == 'planning' else current
        return self.journal.inspect(task_id)

    def cancel(self, task_id):
        snapshot = self.journal.cancel(task_id)
        if snapshot['operation_id'] and self.root_client is not None:
            # Executor cancellation independently authenticates current UID.
            # Root request may not yet exist or be local: retain durable Stop,
            # tolerate unknown-operation only, and never report rollback.
            try:
                self.root_client.cancel(snapshot['operation_id'])
            except Exception:
                pass
        return self.journal.inspect(task_id)
