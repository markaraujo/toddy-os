"""Real private D-Bus typed owner/error/connection recovery, no mock authority."""
import importlib.metadata,json,os
import dbus
assert dbus.__version__=='1.4.0' and importlib.metadata.version('dbus-python')=='1.4.0'
rows=[];names=[]
for cycle in [1,2]:
    bus=dbus.SessionBus(private=True);name=bus.get_unique_name();names.append(name)
    remote=dbus.Interface(bus.get_object('org.freedesktop.DBus','/org/freedesktop/DBus'),'org.freedesktop.DBus')
    uid=remote.GetConnectionUnixUser(name);assert isinstance(uid,dbus.UInt32) and int(uid)==os.getuid()
    assert remote.NameHasOwner('org.toddy.Absent')==False
    try:remote.GetConnectionUnixUser('org.toddy.Absent')
    except dbus.DBusException as error:assert error.get_dbus_name()=='org.freedesktop.DBus.Error.NameHasNoOwner'
    else:raise AssertionError('Missing peer must refuse')
    assert bus.request_name('org.toddy.NativeDbusPythonProbe')==dbus.bus.REQUEST_NAME_REPLY_PRIMARY_OWNER
    assert 'org.toddy.NativeDbusPythonProbe' in remote.ListNames()
    assert bus.release_name('org.toddy.NativeDbusPythonProbe')==dbus.bus.RELEASE_NAME_REPLY_RELEASED
    assert remote.NameHasOwner('org.freedesktop.DBus')
    rows.append({'cycle':cycle,'uid':int(uid),'typed_uid':True,'missing_peer_refused':True,'name_acquire_release':True,'recovery_call':True})
    bus.close()
assert names[0]!=names[1]
print(json.dumps({'scope':'Actual private native dbus-daemon/Python extension owner UID/typed errors/name ownership/reconnect; no Polkit or physical device claim','version':dbus.__version__,'cycles':rows,'distinct_connections':True}))
