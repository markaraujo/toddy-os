"""Run installed nonroot GeoClue/peer authorization with namespace-only fixtures."""
from pathlib import Path
import configparser,hashlib,json,os,shutil,signal,subprocess,time
T=Path('/mnt/lfs');R=Path('/opt/toddy-build');L=Path('/var/log/toddy/phase2')
run=os.environ.get('TODDY_GEO_SERVICE_RUN','3');assert run.isdigit()
receipt=L/('geoclue-installed-services-'+run+'.json');work=T/('tmp/toddy-geoclue-services-'+run);virtual='/tmp/'+work.name
assert not receipt.exists() and not work.exists(),'Inspect private state before any replay'
r=json.loads(Path('/var/log/toddy/build/b02-geoclue-verify-2.success.json').read_text());assert r['recipe_exit']==r['postcheck_exit']==0
public={name:(T/'etc'/name).read_bytes() for name in ['passwd','group','geoclue/geoclue.conf']}
original_hash=hashlib.sha256(public['geoclue/geoclue.conf']).hexdigest()
work.mkdir(mode=0o755)
for name in ['daemon-home','client-home','runtime']:
 p=work/name;p.mkdir(mode=0o700);os.chown(p,30 if name=='daemon-home' else 101,30 if name=='daemon-home' else 101)
shutil.copyfile(R/'scripts/build/phase2/geoclue-service-client.py',work/'client.py');(work/'client.py').chmod(0o444)
subprocess.run(['mount','-t','tmpfs','-o','nosuid,size=4m,mode=755','tmpfs',str(T/'etc')],check=True)
for name in ['passwd','group']:(T/'etc'/name).write_bytes(public[name])
(T/'etc/nsswitch.conf').write_text('passwd: files\ngroup: files\nhosts: files\n')
(T/'etc/hosts').write_text('127.0.0.1 localhost\n');(T/'etc/machine-id').write_text('00000000000000000000000000000030\n')
(T/'etc/geoclue/conf.d').mkdir(parents=True)
conf=configparser.ConfigParser(interpolation=None);conf.read_string(public['geoclue/geoclue.conf'].decode())
for section in ['wifi','ip','3g','cdma','modem-gps','network-nmea','compass']:conf.set(section,'enable','false')
conf.set('static-source','enable','true');conf.set('agent','whitelist','org.toddy.GeoAgent;')
conf['org.toddy.GeoDenied']={'allowed':'false','system':'false','users':'101'}
with (T/'etc/geoclue/geoclue.conf').open('w') as f:conf.write(f)
(T/'etc/geolocation').write_text('-23.433333\n-46.466667\n0\n5\n')
subprocess.run(['mount','-t','proc','-o','nosuid,nodev,noexec','proc',str(T/'proc')],check=True)
subprocess.run(['mount','-t','tmpfs','-o','nosuid,size=1m,mode=755','tmpfs',str(T/'dev')],check=True)
for name in ['null','zero','random','urandom']:
 p=T/'dev'/name;p.touch();subprocess.run(['mount','--bind','/dev/'+name,str(p)],check=True)
subprocess.run(['ip','link','set','lo','up'],check=True);assert not json.loads(subprocess.check_output(['ip','-j','route'],text=True))
assert {r['ifname'] for r in json.loads(subprocess.check_output(['ip','-j','link'],text=True))}=={'lo'}
base={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','PYTHONDONTWRITEBYTECODE':'1','GSETTINGS_BACKEND':'memory','TODDY_GEO_FIXTURE':virtual}
records=[];handles=[]
def stop(proc):
 if proc.poll() is None:proc.terminate()
 value=proc.wait(timeout=8);assert value in [0,-signal.SIGTERM];return value
try:
 for mode in ['first','reconnect']:
  directory=work/mode;directory.mkdir(mode=0o755);socket=virtual+'/'+mode+'/bus.sock';address='unix:path='+socket
  config=directory/'bus.conf';config.write_text('<busconfig><type>system</type><listen>'+address+'</listen><auth>EXTERNAL</auth><policy context="default"><allow user="*"/><allow send_destination="*"/><allow receive_sender="*"/><deny own="*"/></policy><include>/usr/share/dbus-1/system.d/org.freedesktop.GeoClue2.conf</include></busconfig>')
  env={**base,'DBUS_SYSTEM_BUS_ADDRESS':address}
  with (directory/'bus.log').open('xb') as log:
   bus=subprocess.Popen(['chroot',str(T),'dbus-daemon','--nofork','--config-file='+virtual+'/'+mode+'/bus.conf'],env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);handles.append(bus)
  deadline=time.monotonic()+5
  while not (directory/'bus.sock').exists() and bus.poll() is None and time.monotonic()<deadline:time.sleep(.02)
  assert (directory/'bus.sock').exists() and bus.poll() is None
  with (directory/'daemon.log').open('xb') as log:
   daemon=subprocess.Popen(['/usr/bin/setpriv','--no-new-privs','chroot','--userspec=30:30',str(T),'/usr/libexec/geoclue','--timeout=0'],env={**env,'HOME':virtual+'/daemon-home'},stdout=log,stderr=subprocess.STDOUT,start_new_session=True);handles.append(daemon)
  client=subprocess.Popen(['chroot','--userspec=101:101',str(T),'python3',virtual+'/client.py'],env={**env,'HOME':virtual+'/client-home','XDG_RUNTIME_DIR':virtual+'/runtime'},stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,start_new_session=True);handles.append(client)
  try:out,error=client.communicate(timeout=45)
  except subprocess.TimeoutExpired:
   client.terminate();out,error=client.communicate(timeout=8);raise AssertionError('Actual service client timeout; not success')
  (L/('geoclue-service-'+run+'-'+mode+'.stdout')).write_text(out);(L/('geoclue-service-'+run+'-'+mode+'.stderr')).write_text(error);(L/('geoclue-service-'+run+'-'+mode+'.exit')).write_text(str(client.returncode)+'\n')
  assert client.returncode==0,error[-2000:]
  result=json.loads(out);result['daemon_stop_exit']=stop(daemon);result['bus_stop_exit']=stop(bus)
  records.append(result)
 assert records[0]['bus_guid']!=records[1]['bus_guid']
 assert all(p.poll() is not None for p in handles)
 for mode in ['first','reconnect']:
  for name in ['bus.log','daemon.log']:shutil.copyfile(work/mode/name,L/('geoclue-service-'+run+'-'+mode+'-'+name))
 shutil.rmtree(work)
 receipt.write_text(json.dumps({'scope':'Actual installed nonroot GeoClue daemon and peer-UID policy/config deny/global agent revoke/restore/Stop/two buses with namespace-only static source and synthetic agent. Not GNOME consent UI, actual owner position, sensors or remote provider qualification.','daemon_uid':30,'client_uid':101,'network_interfaces':['lo'],'external_routes':0,'actual_owned_bus_policy_used':True,'production_config_before_sha256':original_hash,'production_config_mutated':False,'private_etc_device_proc_namespace':True,'private_profile_removed':True,'records':records},indent=2)+'\n')
finally:
 for proc in reversed(handles):
  if proc.poll() is None:proc.terminate();proc.wait(timeout=8)
