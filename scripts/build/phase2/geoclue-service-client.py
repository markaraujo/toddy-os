"""Real installed GeoClue protocol with a synthetic private consent agent."""
from pathlib import Path
import json,os,threading,time
import gi
gi.require_version('Gio','2.0')
from gi.repository import Gio,GLib
SERVICE='org.freedesktop.GeoClue2';MANAGER='/org/freedesktop/GeoClue2/Manager';CLIENT=SERVICE+'.Client';AGENT=SERVICE+'.Agent';APATH='/org/freedesktop/GeoClue2/Agent'
address=os.environ['DBUS_SYSTEM_BUS_ADDRESS'];assert os.getuid()==101
flags=Gio.DBusConnectionFlags.AUTHENTICATION_CLIENT|Gio.DBusConnectionFlags.MESSAGE_BUS_CONNECTION
def connection():return Gio.DBusConnection.new_for_address_sync(address,flags,None,None)
def call(c,path,interface,method,params=None):return c.call_sync(SERVICE,path,interface,method,params,None,Gio.DBusCallFlags.NONE,5000,None)
def prop(c,path,interface,name):return call(c,path,'org.freedesktop.DBus.Properties','Get',GLib.Variant('(ss)',(interface,name))).unpack()[0]
def setprop(c,path,name,value):call(c,path,'org.freedesktop.DBus.Properties','Set',GLib.Variant('(ssv)',(CLIENT,name,value)))
def denied(fn):
 try:fn()
 except GLib.Error as e:
  assert Gio.DBusError.get_remote_error(e)=='org.freedesktop.DBus.Error.AccessDenied',str(e);return
 raise AssertionError('Unauthorized operation unexpectedly accepted')
def until(fn,seconds=8):
 end=time.monotonic()+seconds
 while time.monotonic()<end:
  if fn():return
  time.sleep(.03)
 raise AssertionError('Bounded native postcondition not reached')
c=connection();until(lambda:c.call_sync('org.freedesktop.DBus','/org/freedesktop/DBus','org.freedesktop.DBus','NameHasOwner',GLib.Variant('(s)',(SERVICE,)),None,Gio.DBusCallFlags.NONE,1000,None).unpack()[0])
ready=threading.Event();state={'accuracy':8,'requests':[]};agent_context=GLib.MainContext.new();agent_loop=GLib.MainLoop.new(agent_context,False)
def agent_thread():
 try:
  agent_context.push_thread_default();a=connection();state['connection']=a
  info=Gio.DBusNodeInfo.new_for_xml(Path('/usr/share/dbus-1/interfaces/org.freedesktop.GeoClue2.Agent.xml').read_text()).lookup_interface(AGENT)
  def method(conn,sender,path,iface,name,params,invocation):
   assert name=='AuthorizeApp';app,accuracy=params.unpack();allow=app=='org.toddy.GeoAllowed'
   state['requests'].append({'desktop_id':app,'allowed':allow});invocation.return_value(GLib.Variant('(bu)',(allow,min(accuracy,state['accuracy']))))
  def getprop(conn,sender,path,iface,name):assert name=='MaxAccuracyLevel';return GLib.Variant('u',state['accuracy'])
  state['registration']=a.register_object(APATH,info,method,getprop,None);ready.set();agent_loop.run()
 except BaseException as e:state['error']=repr(e);ready.set()
 finally:agent_context.pop_thread_default()
t=threading.Thread(target=agent_thread,daemon=True);t.start();assert ready.wait(5) and 'error' not in state,state
connections=[c]
try:
 a=state['connection'];call(a,MANAGER,SERVICE+'.Manager','AddAgent',GLib.Variant('(s)',('org.toddy.GeoAgent',)))
 path=call(c,MANAGER,SERVICE+'.Manager','CreateClient').unpack()[0]
 denied(lambda:call(c,path,CLIENT,'Start'))
 setprop(c,path,'DesktopId',GLib.Variant('s','org.toddy.GeoDenied'));denied(lambda:call(c,path,CLIENT,'Start'))
 setprop(c,path,'DesktopId',GLib.Variant('s','org.toddy.GeoAllowed'));setprop(c,path,'RequestedAccuracyLevel',GLib.Variant('u',8))
 call(c,path,CLIENT,'Start');until(lambda:bool(prop(c,path,CLIENT,'Active')) and prop(c,path,CLIENT,'Location')!='/')
 location=prop(c,path,CLIENT,'Location');lat=prop(c,location,SERVICE+'.Location','Latitude');lon=prop(c,location,SERVICE+'.Location','Longitude')
 assert abs(lat+23.433333)<1e-6 and abs(lon+46.466667)<1e-6
 peer=connection();connections.append(peer);denied(lambda:prop(peer,path,CLIENT,'Active'))
 denied(lambda:peer.call_sync('org.freedesktop.DBus','/org/freedesktop/DBus','org.freedesktop.DBus','RequestName',GLib.Variant('(su)',(SERVICE,0)),None,Gio.DBusCallFlags.NONE,1000,None))
 def accuracy(value):
  state['accuracy']=value;a.emit_signal(None,APATH,'org.freedesktop.DBus.Properties','PropertiesChanged',GLib.Variant('(sa{sv}as)',(AGENT,{'MaxAccuracyLevel':GLib.Variant('u',value)},[])));a.flush_sync(None)
 accuracy(0);until(lambda:not prop(c,path,CLIENT,'Active'))
 accuracy(8);until(lambda:bool(prop(c,path,CLIENT,'Active')))
 call(c,path,CLIENT,'Stop');until(lambda:not prop(c,path,CLIENT,'Active'))
 call(c,MANAGER,SERVICE+'.Manager','DeleteClient',GLib.Variant('(o)',(path,)))
 assert state['requests']==[], 'Native non-sandboxed peer uses upstream system-app branch, not per-app agent prompts'
 print(json.dumps({'bus_guid':c.get_guid(),'actual_client_uid':os.getuid(),'synthetic_static_coordinates_match':True,'missing_DesktopId_refused':True,'config_denial_enforced':True,'per_app_agent_authorization':'not exercised: upstream native non-sandboxed peer uses system-app branch','cross_peer_property_refused':True,'service_name_ownership_refused':True,'agent_revoke_stops_client':True,'agent_restore_recovers_client':True,'explicit_Stop_inactive':True,'agent_fixture_requests':state['requests'],'real_GNOME_consent_or_owner_location_tested':False}))
finally:
 for p in connections:p.close_sync(None)
 agent_loop.quit();t.join(timeout=3);assert not t.is_alive();state['connection'].close_sync(None)
