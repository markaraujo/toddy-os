"""Actual isolated mock process, typed RPC, refusal and restart; not authorization."""
import importlib.metadata
import json
import subprocess
import dbus
import dbus.mainloop.glib
import dbusmock

dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
assert importlib.metadata.version('python-dbusmock') == '0.38.1'
records = []
with dbusmock.PrivateDBus(dbusmock.BusType.SESSION) as bus:
    connection = dbus.bus.BusConnection(bus.address)
    for cycle in range(2):
        with dbusmock.SpawnedMock.spawn_for_name('org.toddy.Test', '/', 'org.toddy.Test') as server:
            control = dbus.Interface(server.obj, dbusmock.MOCK_IFACE)
            control.AddMethod('', 'Echo', 'u', 'u', 'ret = args[0]')
            iface = dbus.Interface(server.obj, 'org.toddy.Test')
            assert iface.Echo(dbus.UInt32(42)) == 42
            try:
                iface.Missing()
            except dbus.DBusException as error:
                assert error.get_dbus_name() == 'org.freedesktop.DBus.Error.UnknownMethod'
            else:
                raise AssertionError('Unknown method accepted')
            owner = connection.get_name_owner('org.toddy.Test')
            assert iface.Echo(dbus.UInt32(7)) == 7
            records.append({'cycle':cycle, 'owner':str(owner), 'typed_echo':42, 'unknown_method_refused':True, 'recovery':True})
        assert not connection.name_has_owner('org.toddy.Test')
    assert records[0]['owner'] != records[1]['owner']
    connection.close()
print(json.dumps({'scope':'Private mock service only, no real authorization or device acceptance', 'version':'0.38.1', 'cycles':records}))
