"""Real production daemon/store/lock/wrong-password/restart in private user data."""
from pathlib import Path
import hashlib,json,os,resource,secrets,shutil,signal,stat,subprocess,sys,tempfile,time
from gi.repository import Gio,GLib
resource.setrlimit(resource.RLIMIT_CORE,(0,0))
prefix=Path(sys.argv[1]);destination=Path(sys.argv[2]);assert not destination.exists()
daemon=prefix/'usr/bin/gnome-keyring-daemon';assert daemon.is_file() and os.geteuid()==101
version=subprocess.run([str(daemon),'--version'],capture_output=True,text=True,timeout=10,check=True)
assert 'gnome-keyring-daemon: 50.0' in version.stdout and 'testing: disabled' in version.stdout
bus=Gio.bus_get_sync(Gio.BusType.SESSION,None);service='org.freedesktop.secrets';root='/org/freedesktop/secrets'
def call(dest,path,iface,method,args=None):return bus.call_sync(dest,path,iface,method,args,None,Gio.DBusCallFlags.NO_AUTO_START,10000,None).unpack()
def has_owner():return call('org.freedesktop.DBus','/org/freedesktop/DBus','org.freedesktop.DBus','NameHasOwner',GLib.Variant('(s)',(service,)))[0]
def owner():return call('org.freedesktop.DBus','/org/freedesktop/DBus','org.freedesktop.DBus','GetNameOwner',GLib.Variant('(s)',(service,)))[0]
assert not has_owner()
master=secrets.token_urlsafe(32);wrong=secrets.token_urlsafe(32);value=secrets.token_urlsafe(48);process=None;owners=[];runs=[];logs=[]
with tempfile.TemporaryDirectory(prefix='toddy-keyring-production-',dir='/build') as directory:
 base=Path(directory);home=base/'home';data=base/'data';runtime=base/'runtime';schemas=base/'schemas'
 for p in [home,data,runtime,schemas]:p.mkdir(mode=0o700)
 for p in Path('/usr/share/glib-2.0/schemas').glob('*.xml'):shutil.copyfile(p,schemas/p.name)
 for p in (prefix/'usr/share/glib-2.0/schemas').glob('*.xml'):
  assert not (schemas/p.name).exists();shutil.copyfile(p,schemas/p.name)
 subprocess.run(['glib-compile-schemas','--strict',str(schemas)],check=True,capture_output=True)
 env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':str(home),'XDG_DATA_HOME':str(data),'XDG_CONFIG_HOME':str(base/'config'),'XDG_CACHE_HOME':str(base/'cache'),'XDG_RUNTIME_DIR':str(runtime),'GSETTINGS_SCHEMA_DIR':str(schemas),'DBUS_SESSION_BUS_ADDRESS':os.environ['DBUS_SESSION_BUS_ADDRESS'],'PYTHONDONTWRITEBYTECODE':'1'}
 assert not any(k.startswith('GNOME_KEYRING_TEST') or k in ['ROOTDIR','LD_PRELOAD'] for k in env)
 def start(password,label):
  global process
  control=base/('control-'+label);control.mkdir(mode=0o700)
  process=subprocess.Popen([str(daemon),'--foreground','--unlock','--components=secrets','--control-directory',str(control)],env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
  process.stdin.write(password.encode());process.stdin.close();process.stdin=None
  deadline=time.monotonic()+15
  while not has_owner() and process.poll() is None and time.monotonic()<deadline:time.sleep(.05)
  assert has_owner() and process.poll() is None,'Production daemon failed to acquire real service name; no private output retained'
  owners.append(owner())
 def stop():
  global process
  process.send_signal(signal.SIGTERM);out,err=process.communicate(timeout=10);assert process.returncode==0 and not has_owner(),'Daemon did not stop cleanly'
  # Digests only: do not persist daemon output, password, lookup data or ciphertext.
  logs.append({'stdout_sha256':hashlib.sha256(out).hexdigest(),'stderr_sha256':hashlib.sha256(err).hexdigest(),'exit':process.returncode});process=None
 def collection():
  path=call(service,root,'org.freedesktop.Secret.Service','ReadAlias',GLib.Variant('(s)',('default',)))[0];assert path!='/'
  return path
 def locked(path):return call(service,path,'org.freedesktop.DBus.Properties','Get',GLib.Variant('(ss)',('org.freedesktop.Secret.Collection','Locked')))[0]
 def lookup():
  r=subprocess.run(['secret-tool','lookup','owner','toddy-b02','purpose','private-production-probe'],env=env,capture_output=True,text=True,timeout=15)
  assert r.returncode==0 and r.stdout.rstrip('\n')==value,'Production secret lookup failed; values omitted'
 def refused_item(item):
  session=call(service,root,'org.freedesktop.Secret.Service','OpenSession',GLib.Variant('(sv)',('plain',GLib.Variant('s',''))))[1]
  try:call(service,item,'org.freedesktop.Secret.Item','GetSecret',GLib.Variant('(o)',(session,)))
  except GLib.Error as error:assert Gio.DBusError.get_remote_error(error)=='org.freedesktop.Secret.Error.IsLocked'
  else:raise AssertionError('Locked production secret was readable')
 try:
  start(master,'initial');path=collection();assert not locked(path)
  r=subprocess.run(['secret-tool','store','--label=Toddy private runtime test','owner','toddy-b02','purpose','private-production-probe'],input=value,env=env,capture_output=True,text=True,timeout=20);assert r.returncode==0,'Production store failed; values omitted'
  lookup();items=call(service,root,'org.freedesktop.Secret.Service','SearchItems',GLib.Variant('(a{ss})',({'owner':'toddy-b02','purpose':'private-production-probe'},)));assert len(items[0])==1 and items[1]==[];item=items[0][0]
  runs.append({'name':'production-create-store-and-real-client-lookup','passed':True})
  files=[p for p in data.rglob('*') if p.is_file() and not p.is_symlink()];assert files
  encrypted=0
  for p in files:
   assert p.resolve().is_relative_to(data.resolve());raw=p.read_bytes();assert master.encode() not in raw and value.encode() not in raw
   if p.suffix=='.keyring':assert stat.S_IMODE(p.stat().st_mode)==0o600 and p.stat().st_uid==101;encrypted+=1
  assert encrypted>=1
  runs.append({'name':'real-storage-nonplaintext-and-private-keyring-mode','passed':True,'keyring_files':encrypted})
  result=call(service,root,'org.freedesktop.Secret.Service','Lock',GLib.Variant('(ao)',([path],)));assert path in result[0] and result[1]=='/' and locked(path);refused_item(item)
  runs.append({'name':'lock-and-actual-secret-read-refused','passed':True});stop();runs.append({'name':'stop-removes-real-service-owner','passed':True})
  start(wrong,'wrong');assert locked(collection());refused_item(item);runs.append({'name':'wrong-master-on-restart-remains-locked','passed':True});stop()
  start(master,'recovery');assert not locked(collection());lookup();assert len(set(owners))==3
  runs.append({'name':'correct-master-restart-persistence-and-new-owner','passed':True});stop()
 finally:
  if process is not None:
   if process.poll() is None:
    process.terminate()
    try:process.wait(timeout=10)
    except subprocess.TimeoutExpired:process.kill();process.wait(timeout=5)
   process=None
assert not Path(directory).exists() and not has_owner()
master=wrong=value=None
destination.write_text(json.dumps({'scope':'Actual production Keyring/SecretTool/store/lock/wrong-master/Stop/persistence on isolated unprivileged builder kernel; synthetic private data only, NOT native GNOME/PAM/graphical acceptance','kernel':os.uname().release,'uid':os.geteuid(),'production_test_hooks_disabled':True,'no_mock_environment_supplied':True,'daemon_sha256':hashlib.sha256(daemon.read_bytes()).hexdigest(),'runs':runs,'distinct_bus_owners':owners,'daemon_output_digests_only':logs,'private_test_data_removed':True,'credential_values_or_ciphertext_retained':False},indent=2)+'\n')
