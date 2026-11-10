"""Run registered upstream programs in an isolated native PID/mount/net view."""
from pathlib import Path
import ctypes,json,os,re,signal,socket,subprocess,sys,tempfile,time

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
  r=run(test['cmd'],test_env,current,test['timeout'])
  r['name']=test['name'];matches=re.findall(r'^Ran (\d+) tests? in ',r['stderr'],re.M)
  r['cases']=int(matches[-1]) if matches else 0
  r['passed']=r['exit']==0 and not r['timed_out'] and r['cases']==fixture['expected_cases'][test['name']] and bool(re.search(r'^OK\s*$',r['stderr'],re.M))
  rows.append(r)
  if not r['passed']:break
report={'all_selected_passed':len(rows)==9 and all(r['passed'] for r in rows),'programs':len(rows),'cases':sum(r['cases'] for r in rows),'positive_control':baseline,'runs':rows}
print(json.dumps(report,sort_keys=True),flush=True)
raise SystemExit(0 if report['all_selected_passed'] else 1)
