"""Run with dbus-run-session; actual client/IPC, synthetic service/tool result."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
import gi
gi.require_version('Gio','2.0')
from gi.repository import Gio, GLib
from runtime.ui.bridge import TaskClient, BUS, OBJECT, INTERFACE

connection = Gio.bus_get_sync(Gio.BusType.SESSION, None)
info = Gio.DBusNodeInfo.new_for_xml((ROOT/'runtime/broker/io.github.markaraujo.Toddy.Service1.xml').read_text())
counts = {'SubmitTask':0,'GetTask':0,'RequestCancel':0,'GetCapabilities':0}
snapshot = {'version':1,'task_id':'task-native-fixture','profile_revision':'a'*64,
            'sequence':1,'state':'running','cancel_requested':False,'result_uncertain':False,
            'summary':'running','operation_id':None}


def handle(_conn, _sender, _path, _interface, method, parameters, invocation):
    counts[method] += 1
    if method == 'GetCapabilities':
        response = json.dumps({'version':1,'profile_id':'toddy-default','profile_revision':'a'*64,
            'features':['native-tools','durable-tasks','cancel'],'tools':['system-info'],
            'agent_backend':False})
    elif method == 'SubmitTask':
        request, profile, revision, body = parameters.unpack()
        assert request and profile=='toddy-default' and revision=='a'*64
        payload = json.loads(body)
        assert payload['tool']=={'kind':'system-info','arguments':{}}
        response = snapshot['task_id']
    elif method == 'GetTask':
        assert parameters.unpack()==(snapshot['task_id'],)
        response = json.dumps(snapshot)
    elif method == 'RequestCancel':
        assert parameters.unpack()[0]==snapshot['task_id']
        snapshot.update(sequence=2,state='canceled',cancel_requested=True,summary='canceled')
        response = json.dumps(snapshot)
    else:
        raise AssertionError(method)
    invocation.return_value(GLib.Variant('(s)',(response,)))

registration = connection.register_object(OBJECT,info.interfaces[0],handle,None,None)
name_id = Gio.bus_own_name_on_connection(connection,BUS,Gio.BusNameOwnerFlags.NONE,None,None)
loop = GLib.MainLoop()
stage = 0
outcome = {}


def reown():
    global name_id
    name_id = Gio.bus_own_name_on_connection(connection,BUS,Gio.BusNameOwnerFlags.NONE,None,None)
    return False


def changed():
    global stage
    if stage==0 and client.phase=='ready':
        stage=1
        client.submit_system_info('Harmless native IPC fixture')
    elif stage==1 and client.state.snapshot is not None:
        assert client.state.snapshot['state']=='running'
        stage=2
        client.stop()
    elif stage==2 and client.state.snapshot['state']=='canceled':
        stage=3
        Gio.bus_unown_name(name_id)
        GLib.timeout_add(100,reown)
    elif stage==3 and client.phase=='ready' and counts['GetTask']>=2:
        assert counts['SubmitTask']==1 and counts['RequestCancel']==1
        assert client.state.task_id=='task-native-fixture'
        assert client.state.snapshot['state']=='canceled'
        outcome.update(status='passed',scope='host-actual-client-synthetic-service',counts=counts)
        loop.quit()


def timeout():
    outcome.update(status='failed',reason='deadline',stage=stage,phase=client.phase,counts=counts)
    loop.quit()
    return False

client=TaskClient(changed)
timer=GLib.timeout_add(5000,timeout)
try:
    loop.run()
finally:
    client.close()
    Gio.bus_unown_name(name_id)
    connection.unregister_object(registration)
print(json.dumps(outcome,sort_keys=True))
raise SystemExit(0 if outcome.get('status')=='passed' else 1)
