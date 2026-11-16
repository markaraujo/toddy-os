"""Trusted B05 disposable native recovery hook, after actual owner authentication."""
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time

assert os.geteuid()==0 and os.uname().release=='7.1.8-toddy' and uid==12405
sys.path.insert(0,'/usr/lib/toddy/executor')
from configuration import ConfigurationManager,qualified_bytes,digest
manager=ConfigurationManager()
target=Path('/etc/toddy/managed/preview-service.json')
assert not target.exists() and not target.parent.exists()
target.parent.mkdir(parents=True,mode=0o755)
with socket.socket() as probe:
    probe.bind(('127.0.0.1',0));port=probe.getsockname()[1]
initial={'version':1,'enabled':True,'listen_port':port}
target.write_bytes(qualified_bytes(initial));target.chmod(0o644)
original=target.read_bytes()
consumer=Path('/usr/lib/toddy/executor/qualification-consumer.py')
assert not consumer.exists()
consumer.write_text('''import json,socket,time
from pathlib import Path
c=json.loads(Path('/etc/toddy/managed/preview-service.json').read_bytes())
assert c['enabled'] is True
s=socket.socket();s.bind(('127.0.0.1',c['listen_port']));s.listen(1)
while True:time.sleep(1)
''')
unit='toddy-config-qualification.service'
unitpath=Path('/etc/systemd/system')/unit
assert not unitpath.exists()
unitpath.write_text('[Unit]\nDescription=Disposable Toddy configuration qualification only\n[Service]\nExecStart=/usr/bin/python3 '+str(consumer)+'\nRestart=no\n')
run(['systemctl','daemon-reload']);run(['systemctl','start',unit])
def reachable():
    try:
        with socket.create_connection(('127.0.0.1',port),timeout=.3):return True
    except OSError:return False
for _ in range(20):
    if reachable():break
    time.sleep(.05)
assert reachable()
ipc=Path('/tmp/toddy-managed-config-ipc.py')
ipc.write_text('''import gi,json,sys
from gi.repository import Gio,GLib
c=Gio.bus_get_sync(Gio.BusType.SYSTEM,None)
method,op=sys.argv[1:3]
if method=='GetOperation':v=GLib.Variant('(s)',(op,))
else:v=GLib.Variant('(sss)',(op,sys.argv[3],sys.argv[4]))
r=c.call_sync('io.github.markaraujo.Toddy.Executor','/io/github/markaraujo/Toddy/Executor','io.github.markaraujo.Toddy.Executor1',method,v,GLib.VariantType('(s)'),Gio.DBusCallFlags.NONE,15000,None)
print(r.unpack()[0])
''');ipc.chmod(0o644)
def call(method,op,kind=None,args=None):
    argv=['/usr/bin/python3',str(ipc),method,op]
    if kind is not None:argv += [kind,json.dumps(args)]
    result=subprocess.run(argv,user=uid,group=uid,extra_groups=[],capture_output=True,text=True,timeout=20)
    assert result.returncode==0,('native_recovery_ipc_failed',method,result.returncode,result.stderr[-400:])
    return json.loads(result.stdout)
def transaction(op,kind,args):
    call('PlanOperation',op,kind,args)
    return call('DispatchOperation',op,kind,args)
bad={**initial,'enabled':False}
arguments={'config_id':'managed-preview','configuration':bad,'expected_sha256':digest(original)}
assert transaction('breakconfig','managed_config_apply',arguments)['state']=='completed'
failed=run(['systemctl','restart',unit],check=False)
for _ in range(40):
    if run(['systemctl','is-failed',unit],check=False).stdout.strip()=='failed':break
    time.sleep(.05)
assert run(['systemctl','is-failed',unit],check=False).stdout.strip()=='failed' and not reachable(),'Broken consumer did not reach failed state'
rescue=manager.rescue_manifest('breakconfig')
assert Path(rescue['backup_file']).read_bytes()==original and rescue['backup_sha256']==digest(original)
restored=transaction('restoreconfig','managed_config_restore',{'config_id':'managed-preview','revision_id':'breakconfig','expected_sha256':digest(target.read_bytes())})
assert restored['state']=='completed' and target.read_bytes()==original
assert transaction('restartconsumer','service_operation',{'action':'restart','unit':unit})['state']=='completed'
for _ in range(40):
    if reachable():break
    time.sleep(.05)
assert reachable()
passed('native-broken-consumer-config-rollback-restores-service-and-manual-backup',consumer='loopback-only disposable qualification',backup_sha256=rescue['backup_sha256'])
# A trusted fixture child uses the actual durable store and manager, then dies
# after the effect and before the outer completion record. No service test hook
# or production environment switch is installed.
run(['systemctl','stop','toddy-executor.service'])
crash_args={'config_id':'managed-preview','configuration':bad,'expected_sha256':digest(target.read_bytes())}
store.plan(uid,session,'crashconfig','managed_config_apply',crash_args)
crasher=Path('/tmp/toddy-config-after-effect.py')
crasher.write_text('''import json,os,sys
from pathlib import Path
sys.path.insert(0,'/usr/lib/toddy/executor')
from store import Store
from configuration import ConfigurationManager
s=Store(Path('/var/lib/toddy/executor'));m=ConfigurationManager()
uid,session,args=int(sys.argv[1]),sys.argv[2],json.loads(sys.argv[3])
def effect(kind,a):
 m.apply('crashconfig',a['config_id'],a['configuration'],a['expected_sha256'])
 os._exit(29)
s.dispatch(uid,session,'crashconfig','managed_config_apply',args,effect)
''')
crashed=run(['/usr/bin/python3','-I',str(crasher),str(uid),session,json.dumps(crash_args)],check=False)
assert crashed.returncode==29 and store.inspect(uid,'crashconfig')['state']=='running'
after=target.stat();run(['systemctl','start','toddy-executor.service'])
recovered=call('GetOperation','crashconfig')
assert recovered['state']=='completed' and recovered['result']['verified']
assert target.stat().st_mtime_ns==after.st_mtime_ns
assert transaction('crashconfig','managed_config_apply',crash_args)==recovered
assert target.stat().st_mtime_ns==after.st_mtime_ns
passed('native-after-effect-process-crash-restart-owned-readback-no-replay')
# A manual valid edit is drift, never an automatic invitation to rewrite it.
manual={**initial,'listen_port':port+1 if port<65535 else port-1}
target.write_bytes(qualified_bytes(manual));manual_bytes=target.read_bytes()
assert manager.inspect('managed-preview')['drift'] is True
time.sleep(.1);assert target.read_bytes()==manual_bytes
passed('native-manual-drift-observed-without-fighting-owner')
run(['systemctl','stop',unit])
# Read-only inventory answers the next Qt native-closure question without
# rebuilding or changing any accepted package in this disposable guest.
qt={}
for pattern in ('**/libqwayland*.so','**/libQt6WaylandClient.so*','**/qtgui-config.h'):
    for path in Path('/usr').glob(pattern):
        if path.is_file():
            qt[str(path)]={'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bytes':path.stat().st_size}
            if path.name=='qtgui-config.h':qt[str(path)]['wayland_features']=[line for line in path.read_text().splitlines() if 'wayland' in line.lower()]
report['qt_readonly_inventory']=qt
