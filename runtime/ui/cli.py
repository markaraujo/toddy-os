"""Terminal client for the same authenticated service used by the desktop."""
import argparse
import json
import os
import sys
import time
import uuid

from .task_state import TaskState, TaskText, TERMINAL, IDENTIFIER, body, capabilities

BUS = 'io.github.markaraujo.Toddy.Service'
OBJECT = '/io/github/markaraujo/Toddy/Service'


class Session:
    def __init__(self):
        import gi
        gi.require_version('Gio', '2.0')
        from gi.repository import Gio, GLib
        self.Gio, self.GLib = Gio, GLib
        self.connection = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        def bus(method, signature, values, result):
            return self.connection.call_sync('org.freedesktop.DBus', '/org/freedesktop/DBus',
                'org.freedesktop.DBus', method, GLib.Variant(signature, values),
                GLib.VariantType(result), Gio.DBusCallFlags.NO_AUTO_START, 5000, None).unpack()[0]
        self.owner = bus('GetNameOwner', '(s)', (BUS,), '(s)')
        if bus('GetConnectionUnixUser', '(s)', (self.owner,), '(u)') != os.getuid():
            raise ValueError('wrong_service_user')

    def call(self, method, signature=None, values=()):
        # Pin the unique owner. A service restart never silently changes the
        # recipient of an in-flight write or causes automatic resubmission.
        return self.connection.call_sync(self.owner, OBJECT, BUS+'1', method,
            self.GLib.Variant(signature, values) if signature else None,
            self.GLib.VariantType('(s)'), self.Gio.DBusCallFlags.NO_AUTO_START,
            5000, None).unpack()[0]


def display(text, stream):
    # Provider/tool data must not emit terminal control sequences.
    stream.write(''.join(c for c in text if c in '\n\t' or
                        (ord(c) >= 32 and not 127 <= ord(c) <= 159)))
    stream.flush()


def follow(session, task_id, *, revision=None, output=sys.stdout, pause=time.sleep):
    if not isinstance(task_id, str) or not IDENTIFIER.fullmatch(task_id):
        raise ValueError('invalid_task_id')
    state = TaskState()
    state.task_id, state.profile_revision = task_id, revision
    text = TaskText(task_id)
    canceled = False
    while True:
        try:
            state.observe(session.call('GetTask', '(s)', (task_id,)))
            while True:
                previous = len(text.text)
                more = text.observe(session.call('GetTaskText', '(st)', (task_id, text.sequence)))
                display(text.text[previous:], output)
                if not more:
                    break
            if state.snapshot['state'] in TERMINAL or state.snapshot['state'] == 'waiting':
                if text.complete and text.sequence == text.latest_sequence:
                    body(session.call('AcknowledgeTaskText', '(st)', (task_id, text.sequence)), 32768)
                display('\n'+state.snapshot['state']+': '+state.snapshot['summary']+'\n', output)
                return 0 if state.snapshot['state'] == 'completed' and not state.snapshot['result_uncertain'] else 2
            pause(0.2)
        except KeyboardInterrupt:
            if canceled:
                # Detach; a second interrupt does not pretend cancellation has
                # completed. The durable task remains discoverable by ID.
                display('\nDetached; inspect task '+task_id+' before further work.\n', output)
                return 130
            canceled = True
            session.call('RequestCancel', '(ss)', (task_id, uuid.uuid4().hex))
            display('\nStop requested; waiting for a safe boundary.\n', output)


def submit(session, text, *, consent=False, request_id=None, output=sys.stdout):
    cap = capabilities(session.call('GetCapabilities'))
    if cap.get('agent_backend') is not True or 'agent-text-v1' not in cap['features']:
        raise ValueError('conversation_unavailable')
    if not 0 < len(text.encode('utf-8')) <= 16384:
        raise ValueError('prompt_bound')
    mode = cap.get('provider_mode')
    if mode not in ('local', 'remote') or (mode == 'remote' and not consent):
        raise ValueError('remote_consent_required')
    request_id = request_id or uuid.uuid4().hex
    display('Request '+request_id+'; profile '+cap['profile_id']+'\n', output)
    payload = json.dumps({'version':1, 'text':text, 'remote_consent':consent if mode == 'remote' else False},
                         ensure_ascii=False, allow_nan=False)
    try:
        task_id = session.call('SubmitTask', '(ssss)', (request_id, cap['profile_id'], cap['profile_revision'], payload))
    except Exception:
        # Read-only recovery is the only allowed next operation. Never retry
        # SubmitTask, even if its original reply was lost.
        try:
            found = body(session.call('LookupRequest', '(ss)', (cap['profile_id'], request_id)), 32768)
            if found.get('found') is not True or not isinstance(found.get('task'), dict):
                raise ValueError('acceptance_unknown')
            task_id = found['task']['task_id']
        except Exception:
            display('Acceptance unknown. Use lookup '+cap['profile_id']+' '+request_id+'; do not resubmit.\n', output)
            return 3
    if not isinstance(task_id, str) or not IDENTIFIER.fullmatch(task_id):
        raise ValueError('invalid_task_id')
    display('Task '+task_id+'\n', output)
    return follow(session, task_id, revision=cap['profile_revision'], output=output)


def configure_profile(session, profile_id, expected_revision, encoded):
    """Validate and apply in one authenticated connection, never retry a write."""
    if len(encoded.encode('utf-8'))>65536:raise ValueError('configuration_bound')
    staged=body(session.call('ValidateProfile','(sss)',(profile_id,expected_revision,encoded)),32768)
    token=staged.get('validated_revision')
    if staged.get('valid') is not True or staged.get('profile_revision')!=expected_revision or \
            not isinstance(token,str) or not 0<len(token)<=128:
        raise ValueError('configuration_not_validated')
    return body(session.call('ApplyProfile','(sss)',(profile_id,expected_revision,token)),32768)


def main(argv=None):
    parser = argparse.ArgumentParser(description='Toddy terminal assistant (same-user session service)')
    commands = parser.add_subparsers(dest='command', required=True)
    ask = commands.add_parser('ask'); ask.add_argument('text', nargs='?')
    ask.add_argument('--allow-remote', action='store_true', help='consent to sending this request to the configured remote provider')
    task = commands.add_parser('task'); task.add_argument('id')
    stop = commands.add_parser('stop'); stop.add_argument('id')
    lookup = commands.add_parser('lookup'); lookup.add_argument('profile'); lookup.add_argument('request')
    commands.add_parser('profiles')
    create = commands.add_parser('create-profile'); create.add_argument('id')
    select = commands.add_parser('select-profile'); select.add_argument('id'); select.add_argument('generation', type=int)
    history = commands.add_parser('history'); history.add_argument('profile'); history.add_argument('--before', type=int, default=0)
    clone=commands.add_parser('clone-profile');clone.add_argument('source');clone.add_argument('revision');clone.add_argument('target')
    for command in ('profile','memory','automation'):
        inspect=commands.add_parser(command);inspect.add_argument('profile')
        if command=='memory':
            inspect.add_argument('--after',default='');inspect.add_argument('--limit',type=int,choices=range(1,17),default=16)
    for command in ('configure-profile','memory-update','automation-update'):
        edit=commands.add_parser(command,help='explicit CAS update from bounded JSON on standard input')
        edit.add_argument('profile');edit.add_argument('expected_revision')
    restore=commands.add_parser('restore-profile');restore.add_argument('profile')
    restore.add_argument('expected_revision');restore.add_argument('revision')
    args = parser.parse_args(argv)
    try:
        session = Session()
        if args.command == 'ask':
            text = args.text if args.text is not None else sys.stdin.buffer.read(16385).decode('utf-8')
            return submit(session, text, consent=args.allow_remote)
        if args.command == 'task':
            return follow(session, args.id)
        if args.command in ('configure-profile','memory-update','automation-update'):
            maximum=4096 if args.command=='automation-update' else 65536
            encoded=sys.stdin.buffer.read(maximum+1).decode('utf-8')
            if len(encoded.encode('utf-8'))>maximum:raise ValueError('input_bound')
            if args.command=='configure-profile':
                value=configure_profile(session,args.profile,args.expected_revision,encoded)
            else:
                method='MutateMemory' if args.command=='memory-update' else 'ConfigureAutomation'
                value=body(session.call(method,'(sss)',(args.profile,args.expected_revision,encoded)),65536)
            display(json.dumps(value,ensure_ascii=False,indent=2)+'\n',sys.stdout)
            return 0
        calls = {
            'stop': ('RequestCancel', '(ss)', (getattr(args,'id',None), uuid.uuid4().hex)),
            'lookup': ('LookupRequest', '(ss)', (getattr(args,'profile',None), getattr(args,'request',None))),
            'profiles': ('ListProfiles', None, ()),
            'create-profile': ('CreateProfile', '(s)', (getattr(args,'id',None),)),
            'select-profile': ('SelectProfile', '(st)', (getattr(args,'id',None), getattr(args,'generation',0))),
            'history': ('ListTasks', '(st)', (getattr(args,'profile',None), getattr(args,'before',0))),
            'clone-profile':('CloneProfile','(sss)',(getattr(args,'source',None),getattr(args,'revision',None),getattr(args,'target',None))),
            'profile':('GetProfileConfig','(s)',(getattr(args,'profile',None),)),
            'memory':('ListMemory','(ssu)',(getattr(args,'profile',None),getattr(args,'after',''),getattr(args,'limit',16))),
            'automation':('GetAutomation','(s)',(getattr(args,'profile',None),)),
            'restore-profile':('RestoreProfile','(sss)',(getattr(args,'profile',None),getattr(args,'expected_revision',None),getattr(args,'revision',None))),
        }
        value = body(session.call(*calls[args.command]), 131072)
        display(json.dumps(value, ensure_ascii=False, indent=2)+'\n', sys.stdout)
        return 0
    except KeyboardInterrupt:
        return 130
    except Exception:
        # Do not echo provider exceptions, credentials, prompts or tracebacks.
        print('Service unavailable or request refused. Inspect known task/request IDs before retrying.', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
