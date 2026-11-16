"""Strict owner schedule control and nondelegating current root policy query."""
import json
try:
    from .automation import ACTIONS, AutomationError
    from .protocol import strict_json
    from .profiles import ProfileError
except ImportError:
    from automation import ACTIONS, AutomationError
    from protocol import strict_json
    from profiles import ProfileError


class StandingPolicy:
    def __init__(self, root_client):
        self.root_client = root_client

    def __call__(self, action):
        if not isinstance(action, str) or action not in ACTIONS:
            return False
        try:
            value = self.root_client.call('GetStandingAuthorization', (action,), '(s)', timeout=1000)
        except Exception:
            return False
        return (isinstance(value, dict) and set(value) == {'version','action_id','allowed'}
            and type(value['version']) is int and value['version'] == 1
            and value['action_id'] == action and type(value['allowed']) is bool and value['allowed'])


class AutomationControl:
    def __init__(self, automation):
        self.automation = automation

    def inspect(self):
        result = self.automation.inspect(limit=32)
        value = {'version': 1, 'profile_id': self.automation.profiles.profile_id,
            'profile_revision': self.automation.profiles.current(),
            'registered_workflows': sorted(ACTIONS), **result}
        if len(json.dumps(value, ensure_ascii=False).encode()) > 60000:
            raise AutomationError('automation_inspection_limit')
        return value

    def mutate(self, expected_revision, encoded):
        self.automation._owner()
        if self.automation.profiles.current() != expected_revision:
            raise ProfileError('stale_profile_revision')
        if not isinstance(encoded, str) or len(encoded.encode()) > 4096:
            raise AutomationError('automation_mutation_limit')
        value = strict_json(encoded.encode())
        fields = {'configure': {'job_id','action','interval','next_due','missed','catchup','seconds','max_runs'},
            'enable': {'job_id'}, 'cancel': {'job_id'}, 'stop': set(),
            'review-read-only': {'operation_id'}, 'prune-terminal-history': set()}
        if not isinstance(value, dict) or type(value.get('version')) is not int or value['version'] != 1:
            raise AutomationError('automation_mutation_schema')
        op = value.get('operation')
        if not isinstance(op, str) or op not in fields or set(value) != {'version','operation'} | fields[op]:
            raise AutomationError('automation_mutation_schema')
        if op == 'configure':
            settings = {key:value[key] for key in fields[op] - {'job_id','action'}}
            result = self.automation.configure(value['job_id'], value['action'], **settings)
        elif op == 'enable':
            result = self.automation.enable(value['job_id'])
        elif op == 'cancel':
            result = self.automation.cancel(value['job_id'])
        elif op == 'stop':
            result = self.automation.stop()
        elif op == 'review-read-only':
            result = self.automation.acknowledge_read_only_failure(value['operation_id'])
        else:
            result = self.automation.prune_terminal_history()
        return {'version': 1, 'profile_id': self.automation.profiles.profile_id,
            'profile_revision': self.automation.profiles.current(), **result}
