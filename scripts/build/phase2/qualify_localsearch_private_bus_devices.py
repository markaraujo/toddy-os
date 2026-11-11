"""Qualify the exact native-path wrapper with an unchanged original bus helper."""
from pathlib import Path
import fcntl,hashlib,json,os,shutil,subprocess,tempfile
ROOT=Path('/opt/toddy-build');TARGET=Path('/mnt/lfs');LOG=Path('/var/log/toddy/phase2')
def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def device_identity(path):
 if not path.exists() and not path.is_symlink():return {'exists':False}
 s=path.lstat();return {'inode':s.st_ino,'device':s.st_dev,'mode':s.st_mode,'uid':s.st_uid,'gid':s.st_gid,'bytes':s.st_size,'mtime_ns':s.st_mtime_ns,'rdev':s.st_rdev}
def main():
 assert os.geteuid()==0
 subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
 lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
 receipt=LOG/'localsearch-private-bus-qualified-5.json';assert not receipt.exists() and not receipt.with_suffix('.part').exists() and not (LOG/'localsearch-private-bus-qualified-5.log').exists()
 device_proof=json.loads((LOG/'private-target-device-profile-1.json').read_text());assert device_proof['state']=='qualified' and device_proof['target_devices_unchanged']
 fixture=json.loads((TARGET/'sources/phase2/native-fixtures/localsearch-1.json').read_text())
 def verify():
  for base,key in [(TARGET/fixture['source_path'].lstrip('/'),'source_files'),(TARGET/fixture['work_path'].lstrip('/')/'compile','compile_files'),(TARGET/fixture['work_path'].lstrip('/')/'stage','stage_files')]:
   assert {str(p.relative_to(base)):digest(p) for p in base.rglob('*') if p.is_file() and not p.is_symlink()}==fixture[key]
 verify();before_devices={n:device_identity(TARGET/'dev'/n) for n in ['null','zero','random','urandom']};wrapper=ROOT/'scripts/build/phase2/localsearch-private-dbus.sh';wrapper_sha=digest(wrapper)
 with tempfile.TemporaryDirectory(prefix='toddy-localsearch-bus-qualification-',dir=TARGET/'var/tmp') as directory:
  base=Path(directory);os.chown(base,101,101);base.chmod(0o700);(base/'run').mkdir(mode=0o700);os.chown(base/'run',101,101);(base/'bin').mkdir();shutil.copyfile(wrapper,base/'bin/dbus-daemon');(base/'bin/dbus-daemon').chmod(0o555)
  virtual='/var/tmp/'+base.name
  usercode=r'''import ctypes,hashlib,json,os,sys
from pathlib import Path
from gi.repository import Gio,GLib
assert os.geteuid()==os.getegid()==101 and set(os.getgroups())<={101}
assert ctypes.CDLL(None,use_errno=True).prctl(38,1,0,0,0)==0
status=Path('/proc/self/status').read_text();assert 'NoNewPrivs:\t1' in status and 'CapEff:\t0000000000000000' in status and 'CapPrm:\t0000000000000000' in status
home=sys.argv[1];source=Path('/sources/phase2/inputs/localsearch-3.11.1');build=Path('/sources/phase2/work/localsearch-1/compile');os.chdir(build);assert Path.cwd()==build
sys.path.insert(0,str(source/'utils'));from trackertestutils.dbusdaemon import DBusDaemon
os.environ.update(PATH=home+'/bin:/usr/bin:/usr/sbin',HOME=home,XDG_RUNTIME_DIR=home+'/run',PYTHONDONTWRITEBYTECODE='1')
config=build/'tests/test-bus.conf';before=hashlib.sha256(config.read_bytes()).hexdigest();rows=[]
for cycle in range(2):
 daemon=DBusDaemon(config_file=str(config),name='toddy-native-path-bus')
 try:
  daemon.start(env=dict(os.environ),new_session=True);daemon.ping_sync();conn=daemon.get_connection();assert conn.get_unique_name().startswith(':')
  assert home+'/run/' in daemon.get_address()
  args=Path('/proc',str(daemon.pid),'cmdline').read_bytes().split(b'\0');assert ('--address=unix:tmpdir='+home+'/run').encode() in args
  result=conn.call_sync('org.freedesktop.DBus','/org/freedesktop/DBus','org.freedesktop.DBus','NameHasOwner',GLib.Variant('(s)',('org.toddy.NoSuchService',)),None,Gio.DBusCallFlags.NONE,3000,None).unpack()[0];assert result is False
  pid=daemon.pid
 finally:daemon.stop()
 assert not Path('/proc',str(pid)).exists();rows.append({'cycle':cycle+1,'original_helper_private_address_GIO_and_cleanup':True})
assert hashlib.sha256(config.read_bytes()).hexdigest()==before
print(json.dumps({'cycles':rows,'UID':101,'NoNewPrivs':True,'compiled_cwd':str(build),'original_config_sha256':before,'readonly_compiled_cwd':True,'functional_LocalSearch_tested':False}))
'''
  child=r'''from pathlib import Path
import subprocess,sys
subprocess.run(['mount','--make-rprivate','/'],check=True)
subprocess.run(['mount','-t','tmpfs','-o','size=1M,mode=0755,nosuid,noexec','toddy-private-devices','/mnt/lfs/dev'],check=True)
for name in ['null','zero','random','urandom']:
 p=Path('/mnt/lfs/dev')/name;p.touch();subprocess.run(['mount','--bind','/dev/'+name,str(p)],check=True)
for name,target in [('fd','/proc/self/fd'),('stdin','/proc/self/fd/0'),('stdout','/proc/self/fd/1'),('stderr','/proc/self/fd/2')]:
 (Path('/mnt/lfs/dev')/name).symlink_to(target)
for relative in ['sources/phase2/inputs/localsearch-3.11.1','sources/phase2/work/localsearch-1/compile']:
 p='/mnt/lfs/'+relative;subprocess.run(['mount','--bind',p,p],check=True);subprocess.run(['mount','-o','remount,bind,ro,nosuid,nodev',p],check=True)
 assert 'ro' in subprocess.check_output(['findmnt','-n','-o','OPTIONS','--mountpoint',p],text=True).strip().split(',')
subprocess.run(['mount','-t','proc','-o','nosuid,nodev,noexec','proc','/mnt/lfs/proc'],check=True)
usercode=sys.argv[1];home=sys.argv[2]
sys.exit(subprocess.run(['chroot','--userspec=101:101','--groups=101','/mnt/lfs','python3','-B','-c',usercode,home],env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','PYTHONDONTWRITEBYTECODE':'1'},cwd='/mnt/lfs/sources/phase2/work/localsearch-1/compile').returncode)
'''
  compile(child,'qualified-private-bus-namespace','exec')
  r=subprocess.run(['unshare','--mount','--pid','--net','--ipc','--fork','--kill-child=SIGKILL','python3','-B','-c',child,usercode,virtual],text=True,capture_output=True,timeout=35)
  (LOG/'localsearch-private-bus-qualified-5.log').open('x').write(r.stdout+r.stderr)
  assert r.returncode==0,(r.returncode,r.stdout,r.stderr)
  actual=json.loads(r.stdout)
 verify();assert digest(wrapper)==wrapper_sha
 assert before_devices=={n:device_identity(TARGET/'dev'/n) for n in before_devices}
 result={'state':'qualified','scope':'Independent exact private PATH wrapper/per-test-style /var/tmp XDG_RUNTIME_DIR; unchanged original helper/config and read-only original compiled cwd, UID101/NNP/no external network/two GIO cycles/own cleanup. Builder kernel/target userspace, NOT cold native LocalSearch functional acceptance.','wrapper_sha256':wrapper_sha,'actual':actual,'original_source_compile_stage_unchanged':True,'target_devices_unchanged':True,'qualified_private_device_profile':'private-target-device-profile-1.json','bounded_reopening':'One new exact-path qualification after independent private-device proof. Preserve all SDK2-4 and native1-3 failures/budgets. No native LocalSearch4 dispatched here.'}
 receipt.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
