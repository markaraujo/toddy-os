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
    def __init__(self, profiles, journal, workspace, *, root_client=None, dispatch_allowed=lambda: False, shell_runner=None, engine_runner=None, text_store=None, memory_api=None, automation=None):
        if os.getuid() == 0 or os.geteuid() == 0:
            raise BrokerError('unprivileged_broker_required')
        self.profiles, self.journal = profiles, journal
        self.workspace = Path(workspace)
        self.root_client = root_client
        self.shell_runner = shell_runner
        self.engine_runner = engine_runner
        self.text_store = text_store
        self.memory_api = memory_api
        self.automation = automation
        self.dispatch_allowed = dispatch_allowed
        # Validate workspace immediately, no implicit host directory choice.
        with Tools(self.workspace):
            pass

    def capabilities(self):
        revision = self.profiles.current()
        config = strict_json(self.profiles.snapshot(revision)['config.json'])
        return {'version': 1, 'profile_schema': 1, 'store_version': 1,
                'profile_id': self.profiles.profile_id, 'profile_revision': revision,
                'features': ['native-tools', 'durable-tasks', 'cancel', 'profiles', 'profile-settings-v1'] +
                    (['agent-text-v1', 'agent-text-ack-v1'] if self.text_store is not None else []) +
                    (['owner-memory-v1'] if self.memory_api is not None else []) +
                    (['owner-automation-v1'] if self.automation is not None else []),
                'agent_backend': bool(self.engine_runner and self.engine_runner.available(config)),
                'provider_mode': config['provider']['mode'],
                'credential_state': 'checked-at-dispatch' if config['provider']['mode'] == 'remote' else 'not-required',
                'tools': sorted(set(config['tools']['enabled']) & NATIVE_TOOLS)}

    @staticmethod
    def decode_input(encoded):
        if not isinstance(encoded, str) or len(encoded.encode()) > 65536:
            raise BrokerError('task_input_limit')
        try:
            request = strict_json(encoded.encode())
        except (ValueError, UnicodeError, RecursionError, OverflowError):
            raise BrokerError('invalid_task_input') from None
        if (not isinstance(request, dict) or type(request.get('version')) is not int or request['version'] != 1
                or not isinstance(request.get('text'), str) or not 0 < len(request['text'].encode()) <= 16384):
            raise BrokerError('invalid_task_input')
        if set(request) == {'version', 'text', 'agent', 'remote_consent'}:
            if request['agent'] is not True or type(request['remote_consent']) is not bool:
                raise BrokerError('invalid_task_input')
        elif (set(request) != {'version', 'text', 'tool'} or not isinstance(request['tool'], dict)
                or set(request['tool']) != {'kind', 'arguments'}):
            raise BrokerError('invalid_task_input')
        return request

    @staticmethod
    def request_metadata(request):
        return request['tool'] if 'tool' in request else {'agent': True, 'remote_consent': request['remote_consent']}

    def accepted_request(self, request_id, revision, encoded):
        request = self.decode_input(encoded)
        return self.journal.accepted_request(request_id, revision, request['text'],
                                              request_metadata=self.request_metadata(request)), request

    def validate_input(self, revision, encoded):
        request = self.decode_input(encoded)
        if set(request) == {'version', 'text', 'agent', 'remote_consent'}:
            if request['agent'] is not True or type(request['remote_consent']) is not bool:
                raise BrokerError('invalid_task_input')
            config = strict_json(self.profiles.snapshot(revision)['config.json'])
            if self.engine_runner is None or self.text_store is None or config['provider']['mode'] == 'deferred':
                raise BrokerError('backend_deferred')
            if config['provider']['mode'] == 'local' and request['remote_consent']:
                raise BrokerError('local_remote_consent_mismatch')
            if config['provider']['mode'] == 'remote' and (not request['remote_consent'] or not config['budgets']['remote_spending_enabled']):
                raise BrokerError('remote_consent_required')
            return request
        if (set(request) != {'version', 'text', 'tool'} or not isinstance(request['tool'], dict)
                or set(request['tool']) != {'kind', 'arguments'}):
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
        existing, request = self.accepted_request(request_id, revision, encoded)
        if existing is not None:
            return existing, request
        request = self.validate_input(revision, encoded)
        if not self.dispatch_allowed():
            raise BrokerError('interactive_session_unavailable')
        snapshot = self.journal.submit(request_id, revision, request['text'], request_metadata=self.request_metadata(request))
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
        if request.get('agent'):
            return self._execute_agent(task_id, request, revision)
        kind, arguments = request['tool']['kind'], request['tool']['arguments']
        operation_id = 'operation-' + task_id.removeprefix('task-')

        def apply(op, _kind, args):
            return self._apply(task_id, op, kind, args)

        # Shell exit alone never proves arbitrary side effects. Such results stay
        # uncertain pending a separate trusted postcondition/review.
        self.journal.run_operation(task_id, operation_id, kind, arguments, apply,
                                   lambda result: isinstance(result, dict) and result.get('verified') is True,
                                   boundary='package' if kind == 'package' else 'interruptible')
        return self.journal.complete(task_id)

    def _apply(self, task_id, operation_id, kind, arguments):
        if not self.dispatch_allowed() or self.journal.inspect(task_id)['cancel_requested']:
            raise BrokerError('interactive_dispatch_stopped')
        canceled = lambda: (self.journal.inspect(task_id)['cancel_requested'] or not self.dispatch_allowed()
                            or self.journal.remaining_seconds(task_id) <= 0)
        if kind == 'system-info':
            kernel = os.uname()
            return {'verified': True, 'uid': os.getuid(), 'kernel': kernel.release, 'machine': kernel.machine}
        if kind in ROOT_KINDS:
            if self.root_client is None:
                raise BrokerError('executor_unavailable')
            return self.root_client.dispatch(operation_id, ROOT_KINDS[kind], arguments, canceled)
        with Tools(self.workspace) as tools:
            if kind == 'file-read':
                return {'verified': True, **tools.read(arguments['path'])}
            if kind == 'file-write':
                return tools.write(arguments['path'], arguments['text'], arguments['expected_sha256'])
            if self.shell_runner is None:
                raise BrokerError('managed_shell_unavailable')
            return self.shell_runner(self.workspace, arguments['argv'], timeout_seconds=arguments['timeout_seconds'], canceled=canceled)

    def _execute_agent(self, task_id, request, revision):
        _revision, files = self.profiles.task_snapshot(task_id)
        config = strict_json(files['config.json'])
        self.text_store.begin(task_id, history_enabled=config['memory']['history_enabled'],
                              retention_days=config['memory']['retention_days'])
        def tool(call_id, kind, arguments):
            operation_id = 'operation-' + task_id.removeprefix('task-') + '-' + call_id
            observed = []
            try:
                # Worker declarations never replace independent broker schemas,
                # pinned selection, current session and executor grant checks.
                self.validate_input(revision, json.dumps({'version': 1, 'text': 'Engine native tool request',
                                    'tool': {'kind': kind, 'arguments': arguments}}))
                def apply(op, _kind, args):
                    result = self._apply(task_id, op, kind, args)
                    observed.append(result)
                    return result
                record = self.journal.run_operation(task_id, operation_id, kind, arguments, apply,
                    lambda result: isinstance(result, dict) and result.get('verified') is True,
                    boundary='package' if kind == 'package' else 'interruptible')
                if record['state'] != 'completed' or not record['verified']:
                    return {'outcome': 'uncertain', 'content': 'Operation outcome requires review. Do not repeat it.'}
                content = json.dumps(observed[0], ensure_ascii=False, separators=(',', ':')) if observed else 'Previously verified operation; no effect replayed.'
                return {'outcome': 'verified', 'content': content}
            except (TaskError, BrokerError, ToolError):
                unknown = self.journal.inspect(task_id)['result_uncertain']
                return {'outcome': 'uncertain' if unknown else 'rejected',
                        'content': 'Operation outcome requires review. Do not repeat it.' if unknown else 'Tool request rejected before dispatch.'}
        try:
            result = self.engine_runner(files, revision, task_id, request['text'], request['remote_consent'],
                tool, lambda text: self.text_store.append(task_id, text),
                lambda: (self.journal.inspect(task_id)['cancel_requested'] or not self.dispatch_allowed()
                         or self.journal.remaining_seconds(task_id) <= 0))
            self.text_store.finish(task_id)
            return self.journal.finish_model(task_id, result['state'])
        finally:
            self.text_store.finish(task_id)

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
            if current['state'] == 'planning' and self.text_store is not None and self.text_store.exists(task_id):
                return self.journal.hold(task_id)  # Effect known; interrupted model reply is never replayed.
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
