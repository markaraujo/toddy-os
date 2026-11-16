#!/usr/bin/env python3
"""Authenticated per-user broker with captured named-profile task routing."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import fcntl
import json
import os
from pathlib import Path
import resource
import signal
import stat
import sys
import time
import uuid

import gi
gi.require_version('Gio', '2.0')
from gi.repository import Gio, GLib

from profiles import ProfileError, ProfileStore
from protocol import strict_json
from tasks import TaskError, TaskJournal
from core import BrokerCore, BrokerError, NATIVE_TOOLS
from tools.scoped import ScopedShell
from tools.native import ToolError
from engine import EngineError
from text import TaskText, TextError
from configured_engine import ConfiguredEngine, ADAPTERS
from profile_registry import ProfileRegistry, RegistryError
from profile_runtime import ProfileRuntime
from types import SimpleNamespace
from memory_api import MemoryAPI, MemoryEngine, MemoryAPIError
from memory import MemoryError
from memory_control import MemoryControl

BUS = 'io.github.markaraujo.Toddy.Service'
OBJECT = '/io/github/markaraujo/Toddy/Service'
INTERFACE = BUS + '1'
ROOT_BUS = 'io.github.markaraujo.Toddy.Executor'
ROOT_OBJECT = '/io/github/markaraujo/Toddy/Executor'
ROOT_INTERFACE = ROOT_BUS + '1'


class RootClient:
    def __init__(self, connection):
        self.connection = connection

    def call(self, method, values, signature, timeout=5000):
        # Independent bus owner check; root policy still authenticates our actual
        # connection UID/session, never a JSON-provided identity or grant.
        uid = self.connection.call_sync('org.freedesktop.DBus', '/org/freedesktop/DBus',
            'org.freedesktop.DBus', 'GetConnectionUnixUser', GLib.Variant('(s)', (ROOT_BUS,)),
            GLib.VariantType('(u)'), Gio.DBusCallFlags.NONE, 3000, None).unpack()[0]
        if uid != 0:
            raise BrokerError('executor_owner_invalid')
        response = self.connection.call_sync(ROOT_BUS, ROOT_OBJECT, ROOT_INTERFACE, method,
            GLib.Variant(signature, values), GLib.VariantType('(s)'),
            Gio.DBusCallFlags.NONE, timeout, None).unpack()[0]
        if len(response.encode()) > 65536:
            raise BrokerError('executor_response_limit')
        result = strict_json(response.encode())
        if not isinstance(result, dict):
            raise BrokerError('executor_response_invalid')
        return result

    def dispatch(self, operation_id, kind, arguments, canceled):
        values = (operation_id, kind, json.dumps(arguments, separators=(',', ':'), allow_nan=False))
        self.call('PlanOperation', values, '(sss)')
        if canceled():
            self.cancel(operation_id)
            raise BrokerError('interactive_dispatch_stopped')
        result = self.call('DispatchOperation', values, '(sss)', timeout=3600000)
        # Only a root adapter's actual verified postcondition proves an effect;
        # arbitrary root command exit explicitly leaves side effects unverified.
        postcondition = result.get('result')
        return {'verified': result.get('state') == 'completed'
                and isinstance(postcondition, dict) and postcondition.get('verified') is True}

    def inspect(self, operation_id):
        return self.call('GetOperation', (operation_id,), '(s)')

    def cancel(self, operation_id):
        return self.call('CancelOperation', (operation_id,), '(s)')


class ActiveSession:
    """Native logind account session; unavailable/remote/locked fails closed."""
    def __init__(self, connection, uid):
        self.connection, self.uid = connection, uid

    def __call__(self):
        try:
            user = self.connection.call_sync('org.freedesktop.login1', '/org/freedesktop/login1',
                'org.freedesktop.login1.Manager', 'GetUser', GLib.Variant('(u)', (self.uid,)),
                GLib.VariantType('(o)'), Gio.DBusCallFlags.NONE, 1000, None).unpack()[0]
            display = self.connection.call_sync('org.freedesktop.login1', user,
                'org.freedesktop.DBus.Properties', 'Get', GLib.Variant('(ss)',
                ('org.freedesktop.login1.User', 'Display')), GLib.VariantType('(v)'),
                Gio.DBusCallFlags.NONE, 1000, None).unpack()[0]
            session_id, path = display
            if not session_id or path == '/':
                return False
            properties = self.connection.call_sync('org.freedesktop.login1', path,
                'org.freedesktop.DBus.Properties', 'GetAll', GLib.Variant('(s)',
                ('org.freedesktop.login1.Session',)), GLib.VariantType('(a{sv})'),
                Gio.DBusCallFlags.NONE, 1000, None).unpack()[0]
            return (properties.get('User', (None,))[0] == self.uid
                    and properties.get('Active') is True
                    and properties.get('Remote') is False
                    and properties.get('LockedHint') is False)
        except (GLib.Error, ValueError, TypeError, IndexError):
            return False


def peer_uid(connection, sender):
    uid = connection.call_sync('org.freedesktop.DBus', '/org/freedesktop/DBus',
        'org.freedesktop.DBus', 'GetConnectionUnixUser', GLib.Variant('(s)', (sender,)),
        GLib.VariantType('(u)'), Gio.DBusCallFlags.NONE, 3000, None).unpack()[0]
    if uid != os.getuid() or uid == 0:
        raise BrokerError('wrong_peer')
    return uid


def lifetime_lock(path):
    fd=os.open(path,os.O_RDWR|os.O_CREAT|os.O_CLOEXEC|os.O_NOFOLLOW,0o600)
    info=os.fstat(fd)
    if not stat.S_ISREG(info.st_mode) or info.st_nlink!=1 or info.st_uid!=os.getuid() or stat.S_IMODE(info.st_mode)!=0o600:
        os.close(fd)
        raise SystemExit('unsafe_broker_lock')
    try:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except BlockingIOError:
        os.close(fd)
        raise SystemExit('broker_already_running') from None
    return fd


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    source_default=Path(__file__).resolve().parents[2]/'config/phase2'
    parser.add_argument('--data-dir',type=Path,default=Path(os.environ.get('XDG_DATA_HOME',
        str(Path.home()/'.local/share')))/'toddy/profiles/toddy-default')
    parser.add_argument('--registry-dir',type=Path)
    parser.add_argument('--workspace',type=Path,default=Path.home()/'Toddy')
    parser.add_argument('--defaults',type=Path,default=source_default if source_default.is_dir() else Path('/usr/share/toddy/profiles'))
    args=parser.parse_args()
    if os.getuid()==0 or os.geteuid()==0:raise SystemExit('unprivileged_broker_required')
    os.umask(0o077)
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    registry_directory=args.registry_dir or (args.data_dir.parent if args.data_dir.name=='toddy-default' else args.data_dir/'profiles')
    for directory in (args.data_dir,args.workspace,registry_directory):
        if not directory.is_absolute() or directory.resolve()!=directory:raise SystemExit('unsafe_broker_directory')
        directory.mkdir(mode=0o700,parents=True,exist_ok=True)
    # Preserve the old leaf lock as well as one registry-wide owner lock. A new
    # registry service cannot recover jobs while a pre-registry broker owns them.
    owner_fd=lifetime_lock(args.data_dir/'broker.lock')
    registry_owner_fd=lifetime_lock(registry_directory/'.broker-instance.lock')
    schema=strict_json((args.defaults/'profile.schema.json').read_bytes())
    template=args.defaults/'profile'
    files={path.name:path.read_bytes() for path in template.iterdir()
           if path.name in {'config.json','SOUL.md','IDENTITY.md','USER.md','AGENTS.md'}
           and path.is_file() and not path.is_symlink()}
    capabilities={'adapters':ADAPTERS,'tools':NATIVE_TOOLS,'skills':{'explain-system'},'extensions':set(),'workflows':set()}
    legacy=ProfileStore(args.data_dir,'toddy-default',schema,capabilities=capabilities)
    if legacy.current() is None:legacy.apply(files,expected_revision=None)
    registry=ProfileRegistry(registry_directory,schema,files,capabilities=capabilities,
                             legacy_default_directory=args.data_dir)
    registry.adopt_existing('toddy-default',allow_recovery=True)
    if registry.active()['profile_id'] is None:
        try:registry.select('toddy-default',expected_generation=0)
        except ProfileError:pass  # Recovery metadata/UI remains usable; no dispatch selection.
    session_connection=Gio.bus_get_sync(Gio.BusType.SESSION,None)
    system_connection=Gio.bus_get_sync(Gio.BusType.SYSTEM,None)
    root_client=RootClient(system_connection)
    allowed=ActiveSession(system_connection,os.getuid())

    def factory(profiles):
        journal=TaskJournal(profiles)
        journal.recover()
        text=TaskText(journal)
        text.recover();text.purge_transient();text.purge_expired()
        memory=MemoryAPI(profiles,owner_allowed=allowed)
        memory_control=MemoryControl(memory)
        core=BrokerCore(profiles,journal,args.workspace,root_client=root_client,
            dispatch_allowed=allowed,shell_runner=ScopedShell(),
            engine_runner=MemoryEngine(ConfiguredEngine(args.defaults),memory),text_store=text, memory_api=memory)
        return SimpleNamespace(profiles=profiles,journal=journal,text_store=text,core=core,
                               memory=memory,memory_control=memory_control)

    runtime=ProfileRuntime(registry,factory)
    # Recover every registered profile exactly once under lifetime ownership.
    # This never replays a task, even if the last selected profile changed.
    for row in registry.list_profiles()['profiles']:
        try:runtime.context(row['profile_id'])
        except (ProfileError,TaskError,TextError,OSError):pass
    info=Gio.DBusNodeInfo.new_for_xml(Path(__file__).with_name(INTERFACE+'.xml').read_text())
    loop=GLib.MainLoop()
    pool=ThreadPoolExecutor(max_workers=1,thread_name_prefix='toddy-broker')
    pending=None  # Immutable (captured context,task_id), independent of selection.
    stopping=False
    stages={};emitted={};emitted_text={}

    def emit(context,task_id):
        snapshot=runtime.snapshot(context,task_id)
        if emitted.get(task_id)!=snapshot['sequence']:
            session_connection.emit_signal(None,OBJECT,INTERFACE,'TaskChanged',
                GLib.Variant('(sts)',(task_id,snapshot['sequence'],json.dumps(snapshot,separators=(',',':')))))
            emitted[task_id]=snapshot['sequence']
        marker=context.text_store.marker(task_id)
        if emitted_text.get(task_id)!=marker:
            session_connection.emit_signal(None,OBJECT,INTERFACE,'TaskTextChanged',GLib.Variant('(st)',(task_id,marker[0])))
            emitted_text[task_id]=marker
        if len(emitted)>256:
            old=next(iter(emitted));emitted.pop(old);emitted_text.pop(old,None)
        return False

    def profiles_changed():
        selected=registry.active()
        session_connection.emit_signal(None,OBJECT,INTERFACE,'ProfilesChanged',
            GLib.Variant('(st)',(selected['profile_id'] or '',selected['generation'])))

    last_purge=time.monotonic()
    def poll():
        nonlocal last_purge
        if time.monotonic()-last_purge>=10:
            for context in runtime.contexts.values():context.text_store.purge_expired()
            last_purge=time.monotonic()
        if pending:
            context,task_id=pending
            current=context.journal.inspect(task_id)
            if not current['cancel_requested'] and (context.journal.remaining_seconds(task_id)<=0 or not context.core.dispatch_allowed()):
                context.core.cancel(task_id)
            emit(context,task_id)
        return True

    def finished(context,task_id):
        nonlocal pending
        emit(context,task_id)
        if pending==(context,task_id):pending=None
        if stopping and pending is None:loop.quit()
        return False

    def execute(context,task_id,request):
        try:context.core.execute(task_id,request)
        except Exception:context.journal.hold(task_id)
        finally:GLib.idle_add(finished,context,task_id)

    def reply(invocation,result):
        invocation.return_value(GLib.Variant('(s)',(json.dumps(result,ensure_ascii=False,separators=(',',':')),)))

    def export_fd(invocation,descriptor):
        try:
            descriptors=Gio.UnixFDList.new();index=descriptors.append(descriptor)
            invocation.return_value_with_unix_fd_list(GLib.Variant('(h)',(index,)),descriptors)
        finally:os.close(descriptor)

    def input_fd(invocation,index):
        descriptors=invocation.get_message().get_unix_fd_list()
        if descriptors is None or descriptors.get_length()>4:raise BrokerError('missing_or_excess_input_fd')
        return descriptors.get(index)

    def existing_files(profiles,expected):
        if profiles.current()!=expected:raise BrokerError('stale_profile_revision')
        try:return profiles.snapshot(expected)
        except ProfileError:return profiles.recovery_snapshot()['files']

    def stage_files(sender,profile_id,expected,files):
        profiles=registry.store(profile_id,allow_recovery=True)
        if profiles.current()!=expected:raise BrokerError('stale_profile_revision')
        now=time.monotonic()
        for token in list(stages):
            if stages[token]['expires']<=now:del stages[token]
        if len(stages)>=8:raise BrokerError('profile_stage_limit')
        revision,_,_=profiles.validate(files)
        token='stage-'+uuid.uuid4().hex
        stages[token]={'sender':sender,'profile_id':profile_id,'expected':expected,'files':files,'revision':revision,'expires':now+600}
        return {'version':1,'validated_revision':token,'profile_revision':revision,'valid':True}

    def handle(conn,sender,_path,_interface,method,parameters,invocation):
        nonlocal pending
        try:
            peer_uid(conn,sender)
            values=parameters.unpack()
            if any(isinstance(value,str) and len(value.encode())>65536 for value in values):raise BrokerError('request_limit')
            if method=='GetCapabilities':reply(invocation,runtime.capabilities())
            elif method=='ListProfiles':reply(invocation,runtime.list_profiles())
            elif method=='CreateProfile':
                result=registry.create(values[0]);profiles_changed();reply(invocation,{'version':1,**result})
            elif method=='CloneProfile':
                source,expected,target=values
                result=registry.clone(source,target,expected_revision=expected);profiles_changed();reply(invocation,{'version':1,**result})
            elif method=='SelectProfile':
                result=registry.select(values[0],expected_generation=values[1])
                runtime.context(values[0]);profiles_changed();reply(invocation,{'version':1,**result})
            elif method=='ImportProfile':
                descriptor=input_fd(invocation,values[1])
                try:result=registry.import_fd(values[0],descriptor)
                finally:os.close(descriptor)
                profiles_changed();reply(invocation,{'version':1,**result})
            elif method=='ExportProfile':
                profile_id,expected=values
                if registry.store(profile_id).current()!=expected:raise BrokerError('stale_profile_revision')
                export_fd(invocation,registry.export_fd(profile_id,revision=expected))
            elif method=='ListTasks':
                reply(invocation,runtime.context(values[0]).journal.list_metadata(values[1]))
            elif method=='LookupRequest':
                profile_id,request_id=values
                task=runtime.context(profile_id).journal.lookup_request(request_id)
                if task is not None:
                    task={**task,'profile_id':profile_id}
                reply(invocation,{'version':1,'profile_id':profile_id,'request_id':request_id,'found':task is not None,'task':task})
            elif method in ('GetTask','GetTaskText','AcknowledgeTaskText','RequestCancel'):
                task_id=values[0];context=runtime.task(task_id)
                if method=='GetTask':reply(invocation,runtime.snapshot(context,task_id,reconcile=True))
                elif method=='GetTaskText':
                    context.text_store.purge_expired();reply(invocation,context.text_store.page(task_id,values[1]))
                elif method=='AcknowledgeTaskText':reply(invocation,context.text_store.acknowledge(task_id,values[1]))
                else:
                    request_id=values[1]
                    if not request_id or len(request_id)>128:raise BrokerError('invalid_cancel_request')
                    context.core.cancel(task_id);reply(invocation,runtime.snapshot(context,task_id));emit(context,task_id)
            elif method=='GetProfileConfig':
                profiles=registry.store(values[0],allow_recovery=True)
                try:settings=profiles.settings()
                except ProfileError:
                    recovery=profiles.recovery_snapshot()
                    with profiles._db() as db:
                        previous=[row[0] for row in db.execute('SELECT revision FROM profile_revisions WHERE revision!=? ORDER BY created DESC,rowid DESC LIMIT 32',(profiles.current(),))]
                    settings={'version':1,'profile_revision':profiles.current(),'config':strict_json(recovery['files']['config.json']),
                              'previous_revisions':previous,'recovery_required':True}
                reply(invocation,settings)
            elif method=='RestoreProfile':
                profile_id,expected,revision=values
                profiles=registry.store(profile_id,allow_recovery=True)
                restored=runtime.context(profile_id).memory.restore_profile(revision,expected_revision=expected)
                profiles_changed();reply(invocation,{'version':1,**restored})
            elif method in ('GetMemory','ListMemory','MutateMemory','ExportMemory','ExportMemoryDocument','RestoreMemory'):
                profile_id=values[0];context=runtime.context(profile_id)
                if method=='GetMemory':reply(invocation,context.memory_control.page())
                elif method=='ListMemory':reply(invocation,context.memory_control.page(values[1],values[2]))
                elif method=='MutateMemory':
                    result=context.memory_control.mutate(values[1],values[2])
                    if pending and pending[0] is context:context.core.cancel(pending[1])
                    profiles_changed();reply(invocation,result)
                elif method in ('ExportMemory','ExportMemoryDocument'):
                    method_fn=context.memory_control.export if method=='ExportMemory' else context.memory_control.export_document
                    export_fd(invocation,method_fn(values[1],values[2]))
                else:
                    descriptor=input_fd(invocation,values[3])
                    try:result=context.memory_control.restore(values[1],values[2],descriptor)
                    finally:os.close(descriptor)
                    if pending and pending[0] is context:context.core.cancel(pending[1])
                    profiles_changed();reply(invocation,result)
            elif method=='SubmitTask':
                request_id,profile_id,revision,encoded=values
                context=runtime.context(profile_id)
                existing,_=context.core.accepted_request(request_id,revision,encoded)
                if existing is not None:
                    invocation.return_value(GLib.Variant('(s)',(existing['task_id'],)));return
                # Preserve44f210c: exact acceptance lookup precedes busy/session
                # admission, and terminal/held old work cannot strand the flag.
                if registry.active()['profile_id']!=profile_id:raise BrokerError('profile_not_selected')
                if pending and pending[0].journal.inspect(pending[1])['state'] in {'completed','failed','canceled','waiting'}:pending=None
                if stopping or pending:raise BrokerError('broker_busy')
                snapshot,request=context.core.submit(request_id,revision,encoded)
                task_id=snapshot['task_id']
                try:registry.bind_task(task_id,profile_id)
                except Exception:
                    context.journal.hold(task_id)
                    raise
                invocation.return_value(GLib.Variant('(s)',(task_id,)));emit(context,task_id)
                if snapshot['state']=='queued':
                    pending=(context,task_id);pool.submit(execute,context,task_id,request)
            elif method in ('ValidateProfile','StageProfileBundle','ApplyProfile'):
                profile_id,expected,candidate=values
                profiles=registry.store(profile_id,allow_recovery=True)
                if method=='ValidateProfile':
                    files=existing_files(profiles,expected);files['config.json']=candidate.encode()
                    reply(invocation,stage_files(sender,profile_id,expected,files))
                elif method=='StageProfileBundle':
                    descriptor=input_fd(invocation,candidate)
                    try:files=registry.decode_bundle(profile_id,registry.read_fd(descriptor))
                    finally:os.close(descriptor)
                    # Portable bundles deliberately contain no memory. Applying
                    # config/persona cannot clear or restore canonical USER.
                    files['USER.md']=existing_files(profiles,expected).get('USER.md',b'')
                    reply(invocation,stage_files(sender,profile_id,expected,files))
                else:
                    stage=stages.get(candidate)
                    if not stage or stage['sender']!=sender or stage['profile_id']!=profile_id or \
                            stage['expected']!=expected or stage['expires']<=time.monotonic():raise BrokerError('profile_stage_unavailable')
                    applied=runtime.context(profile_id).memory.apply_profile(stage['files'],expected_revision=expected,validated_revision=stage['revision']);del stages[candidate]
                    profiles_changed();reply(invocation,{'version':1,'profile_revision':applied['profile_revision'],'applied':True})
            else:raise BrokerError('method_unavailable')
        except (ProfileError,TaskError,BrokerError,TextError,MemoryAPIError,MemoryError) as error:
            invocation.return_dbus_error(INTERFACE+'.Rejected',str(error))
        except (ValueError,UnicodeError,RecursionError,OverflowError,GLib.Error,OSError):
            invocation.return_dbus_error(INTERFACE+'.Rejected','invalid_or_unavailable_request')
        except Exception:invocation.return_dbus_error(INTERFACE+'.Rejected','broker_internal_error')

    def stop():
        nonlocal stopping
        stopping=True
        if pending:pending[0].core.cancel(pending[1])
        else:loop.quit()
        return False

    session_connection.register_object(OBJECT,info.interfaces[0],handle,None,None)
    Gio.bus_own_name_on_connection(session_connection,BUS,Gio.BusNameOwnerFlags.NONE,
        lambda *_:print('READY',flush=True),lambda *_:stop())
    GLib.timeout_add(100,poll)
    GLib.unix_signal_add(GLib.PRIORITY_DEFAULT,signal.SIGTERM,stop)
    GLib.unix_signal_add(GLib.PRIORITY_DEFAULT,signal.SIGINT,stop)
    try:loop.run()
    finally:
        pool.shutdown(wait=True,cancel_futures=True)
        for context in runtime.contexts.values():context.text_store.purge_transient()
        os.close(registry_owner_fd);os.close(owner_fd)


if __name__=='__main__':main()
