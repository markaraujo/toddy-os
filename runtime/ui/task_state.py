"""Conservative UI projection; reconnect retrieves known work, never submits it."""
import re

from ..shared.json import strict_json

IDENTIFIER = re.compile(r'[A-Za-z0-9][A-Za-z0-9._:-]{0,127}\Z')
REVISION = re.compile(r'[0-9a-f]{64}\Z')
STATES = {'queued','planning','running','waiting','completed','failed','canceled'}
TERMINAL = {'completed','failed','canceled'}


def body(data, maximum):
    if not isinstance(data, str) or len(data.encode('utf-8')) > maximum:
        raise ValueError('response_bound')
    value = strict_json(data.encode('utf-8'))
    if not isinstance(value, dict) or type(value.get('version')) is not int or value['version'] != 1:
        raise ValueError('response_version')
    return value


def capabilities(data):
    value = body(data, 32768)
    if value.get('fixture_only') is True or not isinstance(value.get('profile_id'), str) or \
            not IDENTIFIER.fullmatch(value['profile_id']) or \
            not isinstance(value.get('profile_revision'), str) or not REVISION.fullmatch(value['profile_revision']) or \
            not isinstance(value.get('features'), list) or \
            not all(isinstance(item, str) for item in value['features']) or \
            not {'durable-tasks','cancel'}.issubset(value['features']) or \
            not isinstance(value.get('tools'), list) or \
            not all(isinstance(item, str) for item in value['tools']) or \
            ('agent_backend' in value and type(value['agent_backend']) is not bool):
        raise ValueError('unsupported_capabilities')
    return value


class TaskState:
    def __init__(self):
        self.task_id = None
        self.snapshot = None
        self.submitting = False
        self.acceptance_uncertain = False
        self.profile_revision = None

    def begin_submit(self):
        if self.submitting or self.acceptance_uncertain or \
                (self.task_id is not None and self.snapshot is None) or \
                (self.snapshot is not None and (self.snapshot['state'] not in TERMINAL or
                                               self.snapshot['result_uncertain'])):
            raise ValueError('task_already_active')
        self.submitting = True
        self.task_id = None
        self.snapshot = None

    def submitted(self, task_id):
        if not self.submitting or not isinstance(task_id, str) or not IDENTIFIER.fullmatch(task_id):
            raise ValueError('invalid_task_id')
        self.task_id = task_id
        self.submitting = False

    def disconnected(self):
        if self.submitting:
            self.acceptance_uncertain = True
            self.submitting = False
        # A known task_id stays attached for a subsequent GetTask.

    def observe(self, data, *, signal=False):
        value = body(data, 32768)
        if not {'task_id','profile_revision','sequence','state','cancel_requested','result_uncertain','summary','operation_id'}.issubset(value) or \
                value.get('task_id') != self.task_id or not isinstance(value.get('profile_revision'), str) or \
                not REVISION.fullmatch(value['profile_revision']) or \
                (self.profile_revision is not None and value['profile_revision'] != self.profile_revision) or \
                not isinstance(value.get('state'), str) or value['state'] not in STATES or \
                type(value.get('sequence')) is not int or not 0 <= value['sequence'] <= 2**53-1 or \
                type(value.get('cancel_requested')) is not bool or type(value.get('result_uncertain')) is not bool or \
                not isinstance(value.get('summary'), str) or len(value['summary']) > 4096 or \
                (value.get('operation_id') is not None and
                 (not isinstance(value['operation_id'], str) or not IDENTIFIER.fullmatch(value['operation_id']))):
            raise ValueError('invalid_snapshot')
        if self.snapshot is not None:
            if value['sequence'] <= self.snapshot['sequence']:
                return 'stale'
            if signal and value['sequence'] != self.snapshot['sequence'] + 1:
                return 'gap'
        self.snapshot = value
        return 'updated'


class TaskText:
    """Bounded private text pages; these are separate from status signals."""
    def __init__(self, task_id):
        self.task_id=task_id
        self.sequence=0
        self.latest_sequence=0
        self.text=''
        self.complete=False
        self.history_enabled=False
        self.cleanup_requested=False
        self.cleanup_acknowledged=False

    def observe(self,data):
        value=body(data,32768)
        if set(value)!={'version','task_id','chunks','next_sequence','latest_sequence','complete','history_enabled'} or \
                value['task_id']!=self.task_id or not isinstance(value['chunks'],list) or \
                type(value['next_sequence']) is not int or type(value['latest_sequence']) is not int or \
                not self.sequence<=value['next_sequence']<=value['latest_sequence']<=2**53-1 or \
                type(value['complete']) is not bool or type(value['history_enabled']) is not bool:
            raise ValueError('invalid_text_page')
        sequence=self.sequence
        chunks=[]
        for chunk in value['chunks']:
            if not isinstance(chunk,dict) or set(chunk)!={'sequence','text'} or \
                    type(chunk['sequence']) is not int or chunk['sequence']!=sequence+1 or \
                    not isinstance(chunk['text'],str) or not 0<len(chunk['text'].encode('utf-8'))<=1024:
                raise ValueError('invalid_text_chunk')
            sequence=chunk['sequence']
            chunks.append(chunk['text'])
        if sequence!=value['next_sequence'] or \
                (sequence<value['latest_sequence'] and not chunks):
            raise ValueError('text_cursor_stalled')
        candidate=self.text+''.join(chunks)
        if len(candidate.encode('utf-8'))>256*1024:
            raise ValueError('text_total_bound')
        self.sequence=sequence
        self.latest_sequence=value['latest_sequence']
        self.text=candidate
        self.complete=value['complete']
        self.history_enabled=value['history_enabled']
        return self.sequence<self.latest_sequence
