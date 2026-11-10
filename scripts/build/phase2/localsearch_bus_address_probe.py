"""Qualify only private bus address override with original readonly test helper."""
from pathlib import Path
import hashlib,json,os,signal,sys
from gi.repository import Gio,GLib
sys.path.insert(0,'/src/utils')
from trackertestutils.dbusdaemon import DBusDaemon
assert os.geteuid()==os.getegid()==101 and Path.cwd()==Path('/src')
assert 'NoNewPrivs:\t1' in Path('/proc/self/status').read_text()
config=Path('/src/test-bus.conf');before=hashlib.sha256(config.read_bytes()).hexdigest();assert '<listen>unix:tmpdir=./</listen>' in config.read_text()
run=Path('/build/run');run.mkdir(mode=0o700)
os.environ.update(PATH='/src/bin:/usr/bin:/usr/sbin',XDG_RUNTIME_DIR=str(run),PYTHONDONTWRITEBYTECODE='1')
def timeout(signum,frame):raise TimeoutError('bounded independent bus qualification deadline')
signal.signal(signal.SIGALRM,timeout);signal.alarm(25)
rows=[]
for cycle in range(2):
 daemon=DBusDaemon(config_file=str(config),name='toddy-address-qualification')
 try:
  daemon.start(env=dict(os.environ),new_session=True);daemon.ping_sync();conn=daemon.get_connection();assert conn.get_unique_name().startswith(':')
  address=daemon.get_address();assert '=/build/run/' in address,address
  names=conn.call_sync('org.freedesktop.DBus','/org/freedesktop/DBus','org.freedesktop.DBus','ListNames',None,None,Gio.DBusCallFlags.NONE,3000,None).unpack()[0];assert 'org.freedesktop.DBus' in names
  refused=conn.call_sync('org.freedesktop.DBus','/org/freedesktop/DBus','org.freedesktop.DBus','NameHasOwner',GLib.Variant('(s)',('org.toddy.NoSuchService',)),None,Gio.DBusCallFlags.NONE,3000,None).unpack()[0];assert refused is False
  pid=daemon.pid;command=Path('/proc',str(pid),'cmdline').read_bytes().split(b'\0');assert b'--address=unix:tmpdir=/build/run' in command
  rows.append({'cycle':cycle+1,'real_GDBus_connection':True,'ping_and_list_names':True,'unknown_name_unowned':True,'explicit_private_address':True})
 finally:daemon.stop()
 assert not Path('/proc',str(pid)).exists();rows[-1]['own_daemon_stopped']=True
assert hashlib.sha256(config.read_bytes()).hexdigest()==before
signal.alarm(0)
Path('/build/result.json').write_text(json.dumps({'scope':'Independent original helper/private D-Bus address qualification only; readonly source cwd and unmodified config/helper, actual owned daemon/GIO, two cycles. Not LocalSearch search/extractor/install/GUI acceptance and not a reopening of its native test budget.','UID':101,'NoNewPrivs':True,'readonly_config_sha256':before,'original_helper_unmodified':True,'runs':rows,'source_and_config_unchanged':True},indent=2)+'\n')
print('Independent original-helper/private-address qualification passed')
