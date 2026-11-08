#!/usr/bin/env python3
"""Root system-D-Bus executor. No grant/import/model/provider interface here."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import resource
import sys

import gi
gi.require_version('Gio','2.0')
from gi.repository import Gio,GLib
from store import Store,PolicyError
from operations import validate,apply
def strict_json(data):
    # Executor arguments have a small independent schema: no floating values,
    # duplicate keys or nonfinite constants. No optional agent-package import.
    def pairs(items):
        result={}
        for key,value in items:
            if key in result:raise ValueError('duplicate_json_key')
            result[key]=value
        return result
    def reject(_):raise ValueError('noninteger_json_number')
    def number(value):
        result=int(value)
        if abs(result)>2**53-1:raise ValueError('json_integer_range')
        return result
    return json.loads(data.decode('utf-8',errors='strict'),object_pairs_hook=pairs,
        parse_constant=reject,parse_float=reject,parse_int=number)

BUS='io.github.markaraujo.Toddy.Executor'
OBJECT='/io/github/markaraujo/Toddy/Executor'
INTERFACE=BUS+'1'
INFO=Gio.DBusNodeInfo.new_for_xml(Path(__file__).with_name(INTERFACE+'.xml').read_text())


def identity(connection,sender):
    def credential(method):
        return connection.call_sync('org.freedesktop.DBus','/org/freedesktop/DBus','org.freedesktop.DBus',
            method,GLib.Variant('(s)',(sender,)),GLib.VariantType('(u)'),Gio.DBusCallFlags.NONE,3000,None).unpack()[0]
    uid=credential('GetConnectionUnixUser');pid=credential('GetConnectionUnixProcessID')
    session=None
    try:
        # Actual logind identity; absence cannot authorize a session grant.
        path=connection.call_sync('org.freedesktop.login1','/org/freedesktop/login1','org.freedesktop.login1.Manager',
            'GetSessionByPID',GLib.Variant('(u)',(pid,)),GLib.VariantType('(o)'),Gio.DBusCallFlags.NONE,1000,None).unpack()[0]
        session=connection.call_sync('org.freedesktop.login1',path,'org.freedesktop.DBus.Properties',
            'Get',GLib.Variant('(ss)',('org.freedesktop.login1.Session','Id')),GLib.VariantType('(v)'),Gio.DBusCallFlags.NONE,1000,None).unpack()[0]
    except GLib.Error:pass
    return uid,session


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state-dir',type=Path,default=Path('/var/lib/toddy/executor'))
    args=parser.parse_args()
    if os.getuid()!=0 or os.geteuid()!=0:raise SystemExit('root_executor_required')
    os.umask(0o077);resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    store=Store(args.state_dir);store.recover()
    connection=Gio.bus_get_sync(Gio.BusType.SYSTEM,None)
    # One pending operation, no unbounded thread/queue; the main loop remains
    # responsive for inspect and revocation through the independent policy client.
    pool=ThreadPoolExecutor(max_workers=1,thread_name_prefix='toddy-executor')
    pending=False
    def reply(invocation,result=None,error=None):
        nonlocal pending
        pending=False
        if error:invocation.return_dbus_error(INTERFACE+'.Rejected',error)
        else:invocation.return_value(GLib.Variant('(s)',(json.dumps(result,separators=(',',':')),)))
        return False
    def execute(invocation,sender,op,kind,arguments):
        try:
            uid,session=identity(connection,sender)
            result=store.dispatch(uid,session,op,kind,arguments,
                lambda selected,values:apply(selected,values,lambda:store.inspect(uid,op)['cancel_requested']))
            GLib.idle_add(reply,invocation,result,None)
        except PolicyError as error:GLib.idle_add(reply,invocation,None,str(error))
        except Exception:GLib.idle_add(reply,invocation,None,'executor_internal_error')
    def handle(conn,sender,_path,_interface,method,parameters,invocation):
        nonlocal pending
        try:
            uid,session=identity(conn,sender)
            values=parameters.unpack()
            if method in ('PlanOperation','DispatchOperation'):
                op,kind,encoded=values
                if len(encoded.encode())>65536:raise PolicyError('arguments_limit')
                arguments=strict_json(encoded.encode());validate(kind,arguments)
                if method=='PlanOperation':result=store.plan(uid,session,op,kind,arguments)
                else:
                    if pending:raise PolicyError('executor_busy')
                    pending=True;pool.submit(execute,invocation,sender,op,kind,arguments)
                    return
            elif method=='CancelOperation':result=store.cancel(uid,values[0])
            elif method=='GetOperation':result=store.inspect(uid,values[0])
            elif method=='GetAudit':result=store.audit(uid,values[0])
            else:raise PolicyError('method_unavailable')
            invocation.return_value(GLib.Variant('(s)',(json.dumps(result,separators=(',',':')),)))
        except PolicyError as error:invocation.return_dbus_error(INTERFACE+'.Rejected',str(error))
        except (ValueError,UnicodeError,RecursionError):invocation.return_dbus_error(INTERFACE+'.Rejected','invalid_request')
        except Exception:invocation.return_dbus_error(INTERFACE+'.Rejected','executor_internal_error')
    connection.register_object(OBJECT,INFO.interfaces[0],handle,None,None)
    Gio.bus_own_name_on_connection(connection,BUS,Gio.BusNameOwnerFlags.NONE,
        lambda *_:print('READY',flush=True),lambda *_:sys.exit(1))
    GLib.MainLoop().run()

if __name__=='__main__':main()
