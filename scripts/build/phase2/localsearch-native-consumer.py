"""Run registered upstream programs in an isolated native PID/mount/net view."""
from pathlib import Path
import ctypes,hashlib,json,os,re,signal,socket,subprocess,sys,tempfile,time

fixture=json.load(sys.stdin)
assert os.geteuid()==0 and os.getpid()==1 and os.uname().release=='7.1.8-toddy'
subprocess.run(['mount','--make-rprivate','/'],check=True)
subprocess.run(['mount','-t','proc','-o','nosuid,nodev,noexec','proc','/proc'],check=True)
for destination,key in [('/src','source_path'),('/build','work_path')]:
 path=Path(destination);assert not path.exists() and not path.is_symlink()
 path.mkdir()
 subprocess.run(['mount','--bind',fixture[key],destination],check=True)
 subprocess.run(['mount','-o','remount,bind,ro,nosuid,nodev',destination],check=True)
assert fixture['state']=='complete' and len(fixture['selected_tests'])==9
# Make absence distinguishable from Landlock denial; this is only the disposable
# native overlay, never the builder/host or a user-edited installed configuration.
motd=Path('/etc/motd')
if not motd.exists():motd.write_text('Toddy native sandbox positive-control fixture\n')

def nnp():
 assert os.geteuid()==os.getegid()==101
 assert ctypes.CDLL(None,use_errno=True).prctl(38,1,0,0,0)==0

def run(args,env,cwd,timeout):
 start=time.monotonic()
 p=subprocess.Popen(args,user=101,group=101,extra_groups=[],preexec_fn=nnp,env=env,cwd=cwd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,start_new_session=True)
 timed_out=False
 try:stdout,stderr=p.communicate(timeout=timeout)
 except subprocess.TimeoutExpired:
  timed_out=True;os.killpg(p.pid,signal.SIGTERM)
  try:stdout,stderr=p.communicate(timeout=5)
  except subprocess.TimeoutExpired:
   os.killpg(p.pid,signal.SIGKILL);stdout,stderr=p.communicate(timeout=5)
 return {'exit':p.returncode,'timed_out':timed_out,'stdout':stdout,'stderr':stderr,'elapsed_seconds':round(time.monotonic()-start,3)}

rows=[]
with tempfile.TemporaryDirectory(prefix='toddy-localsearch-',dir='/var/tmp') as folder:
 base=Path(folder);os.chown(base,101,101)
 home=base/'home';home.mkdir();os.chown(home,101,101)
 env={'PATH':'/usr/bin:/usr/sbin:/bin','LC_ALL':'C.UTF-8','HOME':str(home),'REAL_HOME':str(home),'PYTHONDONTWRITEBYTECODE':'1','TMPDIR':'/tmp'}
 positive=r'''import json,os,socket,subprocess,tempfile
from pathlib import Path
status=Path('/proc/self/status').read_text().splitlines()
assert all(next(r for r in status if r.startswith(k)).split()[1]=='0000000000000000' for k in ['CapEff:','CapPrm:'])
assert next(r for r in status if r.startswith('NoNewPrivs:')).split()[1]=='1'
assert not str(Path.cwd()).startswith(tempfile.gettempdir()), 'Monitored root must be outside the miner temporary-path exclusion'
assert Path('/proc/cmdline').read_bytes() and Path('/etc/motd').read_bytes()
fd=os.open(str(Path.home().parent),os.O_RDONLY|os.O_DIRECTORY);os.close(fd)
for family,kind in [(socket.AF_UNIX,socket.SOCK_STREAM),(socket.AF_INET,socket.SOCK_STREAM),(socket.AF_INET,socket.SOCK_DGRAM),(socket.AF_INET6,socket.SOCK_STREAM),(socket.AF_INET6,socket.SOCK_DGRAM)]:
 with socket.socket(family,kind):pass
subprocess.run(['/bin/true'],check=True)
p=Path.home()/'positive.txt';p.write_text('retained');fd=os.open(p,os.O_RDONLY|os.O_TRUNC);os.close(fd);assert not p.read_bytes();p.unlink()
print(json.dumps({'UID':os.geteuid(),'capabilities':False,'NoNewPrivs':True,'read_controls':3,'socket_controls':5,'exec_control':True,'write_truncate_control':True,'monitored_tree_outside_tmpdir':True}))
'''
 baseline=run(['python3','-B','-c',positive],env,base,15)
 assert baseline['exit']==0 and not baseline['timed_out'],baseline
 for test in fixture['selected_tests']:
  current=base/test['name'];current.mkdir();os.chown(current,101,101)
  test_env=dict(env);test_env.update(test['env'])
  runtime=current/'run';runtime.mkdir(mode=0o700);os.chown(runtime,101,101)
  binary=current/'bin';binary.mkdir(mode=0o755);os.chown(binary,101,101)
  wrapper=binary/'dbus-daemon';wrapper.write_text(PRIVATE_BUS_WRAPPER);wrapper.chmod(0o555)
  assert hashlib.sha256(wrapper.read_bytes()).hexdigest()=='f2cbb33c16752a89c69cf43d8325fd176b3717bdfa4d6066dced4904992389a4'
  test_env.update(PATH=str(binary)+':/usr/bin:/usr/sbin:/bin',XDG_RUNTIME_DIR=str(runtime))
  # Upstream watchdog/helper selection and Landlock in-tree rules require the
  # same cwd as Meson (BUILDROOT). Keep compiled inputs read-only; redirect
  # only the supported generated TEST_ROOT parameter to writable ext4 data.
  original_config=Path(test_env['TRACKER_FUNCTIONAL_TEST_CONFIG'])
  config=json.loads(original_config.read_text());original=dict(config)
  config['TEST_ROOT']=str(current)
  assert {k for k in config if config[k]!=original[k]}=={'TEST_ROOT'}
  private_config=current/'configuration.json';private_config.write_text(json.dumps(config))
  test_env['TRACKER_FUNCTIONAL_TEST_CONFIG']=str(private_config)
  r=run(test['cmd'],test_env,Path('/build/compile'),test['timeout'])
  r['cwd']='/build/compile';r['test_root']=str(current)
  r['name']=test['name'];matches=re.findall(r'^Ran (\d+) tests? in ',r['stderr'],re.M)
  r['cases']=int(matches[-1]) if matches else 0
  r['passed']=r['exit']==0 and not r['timed_out'] and r['cases']==fixture['expected_cases'][test['name']] and bool(re.search(r'^OK\s*$',r['stderr'],re.M))
  rows.append(r)
  if not r['passed']:break
report={'all_selected_passed':len(rows)==9 and all(r['passed'] for r in rows),'programs':len(rows),'cases':sum(r['cases'] for r in rows),'positive_control':baseline,'runs':rows}
print(json.dumps(report,sort_keys=True),flush=True)
raise SystemExit(0 if report['all_selected_passed'] else 1)
