"""Real native Linux UPower service, system-bus originals and bounded recovery."""
import base64,hashlib,json,os,re,shutil,subprocess,zlib
from pathlib import Path
from gi.repository import Gio,GLib
def output(args):return subprocess.check_output(args,text=True,timeout=15).strip()
def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 assert os.geteuid()==0 and os.uname().release=='7.1.8-toddy' and Path('/proc/1/comm').read_text().strip()=='systemd'
 assert output(['systemd-detect-virt','--vm']) in ['kvm','qemu']
 device=output(['findmnt','-n','-o','SOURCE','/']);assert re.fullmatch('/dev/[a-z0-9]+',device)
 parent=output(['lsblk','-ndo','PKNAME',device]);assert re.fullmatch('[a-z0-9]+',parent)
 assert output(['lsblk','-dnro','SERIAL','/dev/'+parent])=='TODDY-BOOT-TEST' and output(['blkid','-s','LABEL','-o','value',device])=='TODDY_LFS'
 fixture=Path('/sources/phase2/native-fixtures/upower-1');accepted=json.loads((fixture/'accepted.json').read_text())
 def verify():
  for name,row in accepted['files'].items():
   p=Path('/')/name
   if 'sha256' in row:assert not p.is_symlink() and digest(p)==row['sha256']
   else:assert p.is_symlink() and str(p.readlink())==row['symlink']
 verify();stage=Path('/')/accepted['stage'];assert not Path('/usr/libexec/upowerd').exists()
 for name in ['usr','etc','var']:
  if (stage/name).exists():shutil.copytree(stage/name,Path('/')/name,symlinks=True,dirs_exist_ok=True)
 subprocess.run(['ldconfig'],check=True)
 assert not Path('/src').exists();Path('/src/etc').mkdir(parents=True);shutil.copyfile(Path('/')/accepted['original_config'],'/src/etc/UPower.conf')
 subprocess.run(['dbus-send','--system','--type=method_call','--print-reply','--dest=org.freedesktop.DBus','/','org.freedesktop.DBus.ReloadConfig'],check=True,capture_output=True)
 subprocess.run(['systemctl','daemon-reload'],check=True);subprocess.run(['systemctl','start','systemd-logind.service','polkit.service'],check=True,timeout=30)
 runs=[]
 for name in ['polkit','daemon']:
  r=subprocess.run([str(Path('/')/accepted['original_client']),'--tap','-p','/power/'+name],user=101,group=101,extra_groups=[],env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8'},capture_output=True,text=True,timeout=30)
  assert r.returncode==0 and not re.search('skip|not ok',r.stdout+'\n'+r.stderr,re.I),name+' original failed: '+r.stdout+r.stderr
  assert len(re.findall(r'^ok \d+ /power/'+name+'$',r.stdout,re.M))==1
  runs.append({'name':'original-system-bus-'+name,'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr})
 subprocess.run(['systemctl','start','upower.service'],check=True,timeout=30)
 assert output(['systemctl','is-active','upower.service'])=='active'
 pid=int(output(['systemctl','show','-p','MainPID','--value','upower.service']));assert pid>1 and digest(Path('/proc/'+str(pid)+'/exe'))==digest(stage/'usr/libexec/upowerd')
 env=Path('/proc/'+str(pid)+'/environ').read_bytes().split(b'\0');assert not any(v.startswith((b'LD_PRELOAD=',b'UMOCKDEV_DIR=',b'DBUS_SYSTEM_BUS_ADDRESS=')) for v in env)
 bus=Gio.bus_get_sync(Gio.BusType.SYSTEM,None);destination='org.freedesktop.UPower';path='/org/freedesktop/UPower'
 def call(dest,p,iface,method,args=None):return bus.call_sync(dest,p,iface,method,args,None,Gio.DBusCallFlags.NO_AUTO_START,15000,None).unpack()
 def owner():return call('org.freedesktop.DBus','/org/freedesktop/DBus','org.freedesktop.DBus','GetNameOwner',GLib.Variant('(s)',(destination,)))[0]
 def props():return call(destination,path,'org.freedesktop.DBus.Properties','GetAll',GLib.Variant('(s)',(destination,)))[0]
 initial=owner();properties=props();assert properties['DaemonVersion']=='1.91.3' and isinstance(properties['OnBattery'],bool)
 devices=call(destination,path,destination,'EnumerateDevices')[0];assert isinstance(devices,list)
 version=subprocess.run(['upower','--version'],capture_output=True,text=True,timeout=15,check=True);assert 'UPower client version 1.91.3' in version.stdout and 'UPower daemon version 1.91.3' in version.stdout
 runs.append({'name':'real-linux-service-query-and-cli-version','exit':0,'on_battery':properties['OnBattery'],'observed_device_paths':devices})
 try:call(destination,path,destination,'ToddyInvalidMethod')
 except GLib.Error as error:assert Gio.DBusError.get_remote_error(error)=='org.freedesktop.DBus.Error.UnknownMethod'
 else:raise AssertionError('Invalid method accepted')
 assert props()['OnBattery']==properties['OnBattery'];runs.append({'name':'invalid-method-refused-state-preserved','exit':0})
 subprocess.run(['systemctl','stop','upower.service'],check=True,timeout=20)
 assert not call('org.freedesktop.DBus','/org/freedesktop/DBus','org.freedesktop.DBus','NameHasOwner',GLib.Variant('(s)',(destination,)))[0]
 runs.append({'name':'stop-removes-bus-owner','exit':0})
 subprocess.run(['systemctl','start','upower.service'],check=True,timeout=30)
 assert owner()!=initial and props()['DaemonVersion']=='1.91.3';runs.append({'name':'restart-reconnect-distinct-owner','exit':0})
 subprocess.run(['systemctl','stop','upower.service'],check=True,timeout=20);verify()
 raw=json.dumps({'scope':'Actual Linux UPower daemon/system-bus/CLI/Stop/reconnect and two original bus-dependent tests; no physical battery, suspend, power-off or graphical acceptance','kernel':os.uname().release,'fixture_manifest_sha256':digest(fixture/'accepted.json'),'unchanged_fixture_files':len(accepted['files']),'runs':runs,'service_has_no_mock_environment':True,'upstream_service_hardening_used':True},sort_keys=True).encode()
 encoded=base64.b64encode(zlib.compress(raw,9)).decode();chunks=[encoded[i:i+1024] for i in range(0,len(encoded),1024)]
 for i,chunk in enumerate(chunks):print('TODDY_B02_RUNTIME_DATA',i,chunk,flush=True)
 print('TODDY_B02_RUNTIME_RESULT',json.dumps({'kernel':os.uname().release,'all_selected_exits_zero':True,'report_sha256':hashlib.sha256(raw).hexdigest(),'chunks':len(chunks)}),flush=True)
if __name__=='__main__':
 try:main()
 except Exception as error:
  print('TODDY_B02_RUNTIME_FAIL',type(error).__name__,str(error),flush=True);raise
