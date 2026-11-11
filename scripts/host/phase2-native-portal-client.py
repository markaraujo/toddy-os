"""Normal-user real portal file chooser client; never a mock backend."""
from pathlib import Path
import json,os,sys,time
import gi
gi.require_version('Gio','2.0')
from gi.repository import Gio,GLib
assert os.getuid()==12402 and len(sys.argv)==3
mode,marker=sys.argv[1:];assert mode in ['allow','cancel','close']
marker=Path(marker);assert marker.parent==Path('/home/toddy-preview') and marker.name.startswith('portal-')
bus=Gio.bus_get_sync(Gio.BusType.SESSION,None);loop=GLib.MainLoop();responses=[];handle=None;closed=False;failure=None;deadline=time.monotonic()+180

def response(conn,sender,path,interface,name,params,data):
 if path==handle:responses.append(params.unpack());loop.quit()
subscription=bus.signal_subscribe('org.freedesktop.portal.Desktop','org.freedesktop.portal.Request','Response',None,None,Gio.DBusSignalFlags.NONE,response,None)
options={'handle_token':GLib.Variant('s','toddy_'+mode),'multiple':GLib.Variant('b',False)}
r=bus.call_sync('org.freedesktop.portal.Desktop','/org/freedesktop/portal/desktop','org.freedesktop.portal.FileChooser','OpenFile',GLib.Variant('(ssa{sv})',('', 'Toddy native portal '+mode,options)),GLib.VariantType.new('(o)'),Gio.DBusCallFlags.NONE,30000,None)
handle=r.unpack()[0];assert handle.startswith('/org/freedesktop/portal/desktop/request/')
print(json.dumps({'state':'request-open','mode':mode,'handle':handle}),flush=True)
def tick():
 global closed,failure
 if time.monotonic()>deadline:
  failure='Portal response deadline';loop.quit();return False
 if mode=='close' and marker.exists():
  bus.call_sync('org.freedesktop.portal.Desktop',handle,'org.freedesktop.portal.Request','Close',None,None,Gio.DBusCallFlags.NONE,10000,None);closed=True;loop.quit();return False
 return True
GLib.timeout_add(200,tick);loop.run();bus.signal_unsubscribe(subscription);assert failure is None,failure
if mode=='close':
 assert closed and not responses
 try:
  bus.call_sync('org.freedesktop.portal.Desktop',handle,'org.freedesktop.portal.Request','Close',None,None,Gio.DBusCallFlags.NONE,10000,None)
 except GLib.Error as error:
  assert Gio.DBusError.is_remote_error(error);remote=Gio.DBusError.get_remote_error(error);assert remote in ['org.freedesktop.DBus.Error.UnknownMethod','org.freedesktop.DBus.Error.UnknownObject'],remote
 else:raise AssertionError('Closed request remained callable')
 result={'close_exit':0,'closed_object_removed':True,'responses':responses}
else:
 assert len(responses)==1
 code,values=responses[0]
 if mode=='allow':assert code==0 and values.get('uris')==['file:///home/toddy-preview/portal-allowed.txt'],(code,values)
 else:assert code==1 and not values.get('uris'),(code,values)
 result={'response':code,'values':values}
print(json.dumps({'state':'complete','mode':mode,**result}),flush=True)
