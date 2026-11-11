"""Read actual persisted user data/configuration and restored network after cold boot."""
from pathlib import Path
import base64,gzip,hashlib,json,os,re,subprocess,tempfile,termios,time,traceback,zlib

def command(args,timeout=30):
 p=subprocess.run(args,capture_output=True,text=True,timeout=timeout);return {'args':args,'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
def main():
 assert os.getuid()==0 and os.uname().release=='7.1.8-toddy' and Path('/proc/1/comm').read_text().strip()=='systemd'
 source=command(['findmnt','-n','-o','SOURCE','/'])['stdout'].strip();assert re.fullmatch('/dev/[a-z0-9]+',source)
 parent=command(['lsblk','-ndo','PKNAME',source])['stdout'].strip();assert command(['lsblk','-dnro','SERIAL','/dev/'+parent])['stdout'].strip()=='TODDY-BOOT-TEST'
 report={'scope':'Actual later native cold boot of preserved Editor save/user preference/restored NetworkManager data. Existing normal GDM/offline Editor refusal/crash/recovery GUI proof reused; private real D-Bus for persisted dconf reads is not a new graphical login test. No physical/whole B02 acceptance.','all_selected_exits_zero':False}
 try:
  bootid=Path('/proc/sys/kernel/random/boot_id').read_text().strip();home=Path('/home/toddy-preview');marker=home/'b02-persistence.json';proof=json.loads(marker.read_text())
  assert proof['boot_id']!=bootid
  report.update(previous_boot_id=proof['boot_id'],current_boot_id=bootid,distinct_actual_boots=True)
  config=hashlib.sha256(gzip.decompress(Path('/proc/config.gz').read_bytes())).hexdigest();assert config=='952e7d9d6e5c8e523ebf128c220481bc29280424e0686e4b0903b518234bf77b';report['running_config_sha256']=config
  saved=home/'editor-recovered.txt';assert not saved.is_symlink() and saved.stat().st_uid==12402
  assert hashlib.sha256(saved.read_bytes()).hexdigest()==proof['saved_file_sha256']
  assert saved.read_bytes() in [b'Toddy editor recovery proof\n',b'Toddy editor recovery proof\n\n']
  assert hashlib.sha256((home/'refusal/read-only.txt').read_bytes()).hexdigest()==proof['protected_sha256']
  report['saved_file']={'sha256':proof['saved_file_sha256'],'bytes':saved.stat().st_size,'fixture_content_hex':saved.read_bytes().hex(),'protected_original_unchanged':True}
  values={}
  with tempfile.TemporaryDirectory(prefix='toddy-persisted-dconf-') as temporary:
   os.chown(temporary,12402,12402);os.chmod(temporary,0o700)
   for key,expected in [('accent-color',proof['accent_color']),('color-scheme',proof['color_scheme'])]:
    p=subprocess.run(['dbus-run-session','--','gsettings','get','org.gnome.desktop.interface',key],user=12402,group=12402,extra_groups=[],env={'HOME':str(home),'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','XDG_RUNTIME_DIR':temporary},capture_output=True,text=True,timeout=20)
    assert p.returncode==0 and p.stdout.strip()==repr(expected),(key,p.stdout,p.stderr);values[key]=p.stdout.strip()
  report['persisted_user_preferences']=values
  assert Path('/etc/toddy/network/use-networkmanager').read_text()=='NetworkManager\n'
  assert not Path('/etc/toddy/network/use-networkmanager.native-test-backup').exists()
  deadline=time.monotonic()+45
  while time.monotonic()<deadline:
   active=command(['systemctl','is-active','NetworkManager.service']);routes=command(['ip','-j','route','show','default'])
   if active['stdout'].strip()=='active' and json.loads(routes['stdout']):break
   time.sleep(.5)
  assert active['stdout'].strip()=='active' and json.loads(routes['stdout'])
  inactive=command(['systemctl','is-active','systemd-networkd.service']);assert inactive['stdout'].strip()=='inactive'
  report['restored_manager_after_reboot']={'active':active,'networkd':inactive,'routes':json.loads(routes['stdout'])}
  dhcp=command(['nmcli','-g','IP4.ADDRESS,IP4.GATEWAY,IP4.DNS','device','show']);assert dhcp['exit']==0 and dhcp['stdout'].strip();report['fresh_network_dhcp']=dhcp
  dns=command(['getent','ahostsv4','example.com']);assert dns['exit']==0 and dns['stdout'].strip();report['fresh_network_dns']=dns
  report['agent_package_absent']=command(['dpkg-query','-W','toddy-agent']);assert report['agent_package_absent']['exit']!=0
  report['all_selected_exits_zero']=True
 except Exception as error:report.update(error={'type':type(error).__name__,'message':str(error)},traceback=traceback.format_exc(),diagnostics=command(['journalctl','-b','--no-pager','-n','100']))
 finally:
  report['gdm_stop']=command(['systemctl','stop','gdm.service'],timeout=40);report['all_selected_exits_zero'] &= report['gdm_stop']['exit']==0
 raw=json.dumps(report,sort_keys=True).encode();packed=base64.b64encode(zlib.compress(raw,9)).decode();chunks=[packed[i:i+1024] for i in range(0,len(packed),1024)]
 fd=os.open('/dev/ttyS1',os.O_WRONLY|os.O_NOCTTY);attrs=termios.tcgetattr(fd);attrs[0]=attrs[1]=attrs[3]=0;attrs[2]|=termios.CLOCAL|termios.CREAD;attrs[4]=attrs[5]=termios.B115200;termios.tcsetattr(fd,termios.TCSANOW,attrs)
 with os.fdopen(fd,'w',buffering=1) as out:
  for i,part in enumerate(chunks):print('TODDY_B02_RUNTIME_DATA',i,part,file=out,flush=True)
  print('TODDY_B02_RUNTIME_RESULT',json.dumps({'kernel':os.uname().release,'all_selected_exits_zero':report['all_selected_exits_zero'],'report_sha256':hashlib.sha256(raw).hexdigest(),'chunks':len(chunks)}),file=out,flush=True);termios.tcdrain(out.fileno())
 assert report['all_selected_exits_zero'],'Actual persisted user/network state failed'
if __name__=='__main__':main()
