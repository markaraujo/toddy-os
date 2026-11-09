"""Actual installed calendar persistence across private session-bus lifecycles."""
from pathlib import Path
import hashlib,json,os,sys,time
import gi
gi.require_version('EDataServer','1.2');gi.require_version('ECal','2.0');gi.require_version('ICalGLib','4.0')
from gi.repository import EDataServer,ECal,ICalGLib,Gio,GLib
mode=sys.argv[1];work=Path(sys.argv[2]);assert os.geteuid()==101 and mode in ['write','read']
assert not any(k in os.environ for k in ['EDS_TESTING','EDS_CALENDAR_MODULES','GSETTINGS_SCHEMA_DIR','LD_LIBRARY_PATH'])
bus_guid=Gio.bus_get_sync(Gio.BusType.SESSION,None).get_guid();assert bus_guid
registry=EDataServer.SourceRegistry.new_sync(None);source=registry.ref_builtin_calendar();assert source
client=ECal.Client.connect_sync(source,ECal.ClientSourceType.EVENTS,5,None);assert client
uid='toddy-native-eds-offline-1';marker=work/'created.json'
def disk_state(present):
    until=time.monotonic()+8
    while True:
        files=[p for p in (work/'data').rglob('*.ics') if p.is_file() and uid.encode() in p.read_bytes()]
        if bool(files)==present:return {str(p.relative_to(work)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
        assert time.monotonic()<until,'Calendar file postcondition did not become observable'
        time.sleep(0.05)
if mode=='write':
    assert not marker.exists()
    component=ICalGLib.Component.new_from_string('BEGIN:VEVENT\r\nUID:'+uid+'\r\nDTSTAMP:20261109T120000Z\r\nDTSTART:20261109T130000Z\r\nSUMMARY:Evento local Toddy\r\nEND:VEVENT\r\n');assert component
    ok,created=client.create_object_sync(component,ECal.OperationFlags.NONE,None)
    assert ok and created==uid
    ok,reopened=client.get_object_sync(uid,None,None);assert ok and reopened.get_uid()==uid
    files=disk_state(True);assert files
    marker.write_text(json.dumps({'uid':uid,'files':files})+'\n')
    result={'created_and_read':True,'actual_disk_file_observed':True,'source_uid':source.get_uid()}
else:
    previous=json.loads(marker.read_text());assert previous['uid']==uid
    ok,reopened=client.get_object_sync(uid,None,None)
    assert ok and reopened.get_uid()==uid and reopened.get_summary()=='Evento local Toddy'
    stop=Gio.Cancellable();stop.cancel()
    try:client.get_object_sync(uid,None,stop)
    except GLib.Error as error:assert error.matches(Gio.io_error_quark(),Gio.IOErrorEnum.CANCELLED)
    else:raise AssertionError('Pre-cancelled read was not refused')
    ok,recovered=client.get_object_sync(uid,None,None);assert ok and recovered.get_uid()==uid
    assert client.remove_object_sync(uid,None,ECal.ObjModType.ALL,ECal.OperationFlags.NONE,None)
    disk_state(False)
    result={'persisted_after_new_bus':True,'precancelled_read_refused':True,'post_cancel_recovery':True,'removed_and_disk_state_verified':True,'source_uid':source.get_uid()}
result['bus_guid']=bus_guid
print(json.dumps(result))
