"""Actual async/native UI against a synthetic service; never a provider success."""
import argparse
import copy
import json
import os
from pathlib import Path
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
import gi
gi.require_version('Gio','2.0')
from gi.repository import Gio,GLib
from runtime.ui.bridge import TaskClient,BUS,OBJECT,INTERFACE

parser=argparse.ArgumentParser()
parser.add_argument('--gtk',action='store_true')
parser.add_argument('--locale',default='en')
args=parser.parse_args()
if args.gtk:
    os.environ.setdefault('GTK_USE_PORTAL','0')
    os.environ.setdefault('GIO_USE_VFS','local')
    os.environ.setdefault('GTK_A11Y','none')
connection=Gio.bus_get_sync(Gio.BusType.SESSION,None)
xml=(ROOT/'runtime/broker/io.github.markaraujo.Toddy.Service1.xml').read_text()
extension='''
<method name="GetTaskText"><arg type="s" direction="in"/><arg type="t" direction="in"/><arg type="s" direction="out"/></method>
<method name="GetProfileConfig"><arg type="s" direction="in"/><arg type="s" direction="out"/></method>
<method name="RestoreProfile"><arg type="s" direction="in"/><arg type="s" direction="in"/><arg type="s" direction="in"/><arg type="s" direction="out"/></method>
<signal name="TaskTextChanged"><arg type="s"/><arg type="t"/></signal>
'''
# The source XML may already include extensions after integration. Add only
# absent entries, allowing the same fixture to run on a later combined checkout.
from xml.etree import ElementTree as ET
node=ET.fromstring(xml)
iface=node.find('interface')
for entry in ET.fromstring('<node>'+extension+'</node>'):
    if not any(old.tag==entry.tag and old.get('name')==entry.get('name') for old in iface):
        iface.append(entry)
info=Gio.DBusNodeInfo.new_for_xml(ET.tostring(node,encoding='unicode'))
counts={}
revision='a'*64
original=json.loads((ROOT/'config/phase2/profile/config.json').read_text())
config=copy.deepcopy(original)
previous=[]
staged=None
snapshot={'version':1,'task_id':'conversation-fixture','profile_revision':'a'*64,
          'sequence':1,'state':'running','cancel_requested':False,'result_uncertain':False,
          'summary':'running','operation_id':None}
chunks=[{'sequence':1,'text':'<b>Literal reply</b> '},{'sequence':2,'text':'Olá, Toddy.'}]


def reply(invocation,value):
    invocation.return_value(GLib.Variant('(s)',(json.dumps(value,separators=(',',':')),)))


def handle(_conn,_sender,_path,_interface,method,parameters,invocation):
    global revision,config,previous,staged
    counts[method]=counts.get(method,0)+1
    values=parameters.unpack()
    if method=='GetCapabilities':
        reply(invocation,{'version':1,'profile_id':'toddy-default','profile_revision':revision,
            'features':['native-tools','durable-tasks','cancel','profiles','agent-text-v1','profile-settings-v1'],
            'tools':['system-info'],'agent_backend':True,'provider_mode':'local'})
    elif method=='SubmitTask':
        request_id,profile,expected,encoded=values
        body=json.loads(encoded)
        assert body=={'version':1,'text':'<b>Fixture input</b>','agent':True,'remote_consent':False}
        assert expected==revision and profile=='toddy-default'
        invocation.return_value(GLib.Variant('(s)',(snapshot['task_id'],)))
    elif method=='GetTask': reply(invocation,snapshot)
    elif method=='GetTaskText':
        task_id,after=values
        assert task_id==snapshot['task_id']
        page=[chunk for chunk in chunks if chunk['sequence']>after][:1]
        next_sequence=page[-1]['sequence'] if page else after
        reply(invocation,{'version':1,'task_id':task_id,'chunks':page,'next_sequence':next_sequence,
                          'latest_sequence':2,'complete':True,'history_enabled':False})
    elif method=='RequestCancel':
        snapshot.update(sequence=2,state='canceled',cancel_requested=True,summary='canceled')
        reply(invocation,snapshot)
    elif method=='GetProfileConfig':
        reply(invocation,{'version':1,'profile_revision':revision,'config':config,'previous_revisions':previous})
    elif method=='ValidateProfile':
        assert values[1]==revision
        candidate=json.loads(values[2])
        if candidate['schema_version']!=1:
            invocation.return_dbus_error(INTERFACE+'.Rejected','invalid_profile')
            return
        staged=candidate
        reply(invocation,{'version':1,'valid':True,'validated_revision':'stage-fixture','profile_revision':'b'*64})
    elif method=='ApplyProfile':
        assert values[1]==revision and values[2]=='stage-fixture'
        previous=[revision]
        revision='b'*64
        config=staged
        reply(invocation,{'version':1,'applied':True,'profile_revision':revision})
    elif method=='RestoreProfile':
        assert values[1]==revision and values[2] in previous
        previous=[revision]
        revision=values[2]
        config=copy.deepcopy(original)
        reply(invocation,{'version':1,'restored':True,'profile_revision':revision})
    else: raise AssertionError(method)

registration=connection.register_object(OBJECT,info.interfaces[0],handle,None,None)
name_id=Gio.bus_own_name_on_connection(connection,BUS,Gio.BusNameOwnerFlags.NONE,None,None)
loop=GLib.MainLoop()
stage=0
outcome={}
window=None
model=None
scratch=None
if args.gtk:
    gi.require_version('Gtk','4.0')
    gi.require_version('Adw','1')
    from gi.repository import Gtk,Adw
    from runtime.ui.app import ToddyApplication,SetupWindow
    from runtime.ui.model import SetupModel
    Gtk.init();Adw.init()
    scratch=tempfile.TemporaryDirectory()
    model=SetupModel(ROOT,Path(scratch.name)/'setup',args.locale)
    app=ToddyApplication(model)
    app.register(None)
    window=SetupWindow(app,model)
    client=window.client
else:
    client=TaskClient(lambda:None)


def reown():
    global name_id
    name_id=Gio.bus_own_name_on_connection(connection,BUS,Gio.BusNameOwnerFlags.NONE,None,None)
    return False


def poll():
    global stage
    try:
        if stage==0 and client.phase=='ready' and client.profile is not None:
            stage=1
            if window:
                assert window.entry.get_sensitive() and window.send_button.get_sensitive()
                window.entry.set_text('<b>Fixture input</b>')
                window.send_button.emit('clicked')
            else: client.submit_text('<b>Fixture input</b>')
        elif stage==1 and client.text is not None and client.text.sequence==2:
            assert client.text.text=='<b>Literal reply</b> Olá, Toddy.'
            stage=2
            if window:
                # Text updates are intentionally coalesced up to100ms.
                window._task_changed()
                begin,end=window.conversation_buffer.get_bounds()
                assert '<b>Literal reply</b>' in window.conversation_buffer.get_text(begin,end,True)
                window.conversation_stop.emit('clicked')
            else: client.stop()
        elif stage==2 and client.state.snapshot['state']=='canceled':
            stage=3
            invalid=copy.deepcopy(config);invalid['schema_version']=2
            if window:
                window.profile_buffer.set_text(json.dumps(invalid))
                window.profile_validate.emit('clicked')
            else: client.validate_profile(json.dumps(invalid))
        elif stage==3 and client.profile_status=='failed':
            assert revision=='a'*64
            stage=4
            candidate=copy.deepcopy(config);candidate['display_name']='Toddy fixture edit'
            if window:
                window.profile_buffer.set_text(json.dumps(candidate))
                window.profile_validate.emit('clicked')
            else: client.validate_profile(json.dumps(candidate))
        elif stage==4 and client.profile_status=='validated':
            stage=5
            if window: window.profile_apply.emit('clicked')
            else: client.apply_profile()
        elif stage==5 and client.profile and client.profile['profile_revision']=='b'*64:
            stage=6
            if window:
                window._task_changed()
                window.profile_restore.emit('clicked')
            else: client.restore_profile('a'*64)
        elif stage==6 and client.profile and client.profile['profile_revision']=='a'*64:
            stage=7
            Gio.bus_unown_name(name_id)
            GLib.timeout_add(100,reown)
        elif stage==7 and client.phase=='ready' and counts.get('GetTask',0)>=2 and counts.get('GetTaskText',0)>=3:
            assert counts['SubmitTask']==1 and counts['RequestCancel']==1
            assert client.state.task_id=='conversation-fixture'
            assert client.text.sequence==2
            outcome.update(status='passed',scope='host-actual-client-synthetic-service',
                           native_widgets=args.gtk,locale=args.locale,counts=counts)
            loop.quit()
            return False
    except Exception as exc:
        outcome.update(status='failed',reason=type(exc).__name__,stage=stage,counts=counts)
        loop.quit()
        return False
    return True


def timeout():
    outcome.update(status='failed',reason='deadline',stage=stage,phase=client.phase,counts=counts)
    loop.quit()
    return False

GLib.timeout_add(10,poll)
GLib.timeout_add(10000,timeout)
try: loop.run()
finally:
    if window:
        window._close()
        window.destroy()
        model.close()
        scratch.cleanup()
    else: client.close()
    Gio.bus_unown_name(name_id)
    connection.unregister_object(registration)
print(json.dumps(outcome,sort_keys=True))
raise SystemExit(0 if outcome.get('status')=='passed' else 1)
