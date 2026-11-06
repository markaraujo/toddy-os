#!/usr/bin/env python3
"""Exercise actual native agetty/Shadow/Bash with fresh locked image accounts.

Private PID/mount namespaces and a new devpts instance isolate all login
sessions. This is not a Systemd, hardware-console or ISO boot test.
"""
from pathlib import Path
import base64
import hashlib
import json
import os
import subprocess

os.chdir(Path(__file__).resolve().parents[2])
sources = {name: base64.b64encode((Path('scripts/build/h10') / name).read_bytes()).decode()
           for name in ('live_accounts.py', 'live_console.py', 'initramfs_runtime.py')}
baseline = json.loads(Path('config/live-account-baseline.json').read_text())
inner = r'''from pathlib import Path
import base64,ctypes,errno,fcntl,hashlib,json,os,select,signal,shlex,shutil,stat,subprocess,sys,termios,time,types
base=Path(BASE);root=Path('/mnt/lfs');stage=base/'image'
assert os.getpid()==1 and base.resolve()==base and base.parent==root/'tmp'
def digest(path):
 with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
before={name:digest(root/name) for name in ('etc/passwd','etc/shadow','etc/group','etc/gshadow','var/lib/dpkg/status')}
for name,content in SOURCES.items():
 module=types.ModuleType(name[:-3]);module.__file__='/opt/toddy-build/scripts/build/h10/'+name
 sys.modules[name[:-3]]=module
 exec(compile(base64.b64decode(content),module.__file__,'exec'),module.__dict__)
runtime=sys.modules['initramfs_runtime']
# Reuse the native byte/loader verifier with this probe's explicit program set.
runtime.PROGRAMS=('/usr/sbin/agetty','/usr/bin/login','/usr/bin/bash','/usr/bin/id','/usr/bin/false')
runtime_report=runtime.stage_runtime(root,stage,Path('/var/log/toddy/packages'))
sys.modules['live_accounts'].stage_accounts(stage,BASELINE)
accounts={name:digest(stage/'etc'/name) for name in ('passwd','shadow','group','gshadow')}
owners=runtime.installed_records(root,Path('/var/log/toddy/packages'))
login_mode=stat.S_IMODE((root/'usr/bin/login').stat().st_mode)
assert login_mode==stat.S_IMODE(owners['/usr/bin/login'][3]['mode'])==0o755
assert stat.S_IMODE((stage/'usr/bin/login').stat().st_mode)==login_mode
assert digest(root/'etc/login.defs')==owners['/etc/login.defs'][3]['sha256']
shutil.copy2(root/'etc/login.defs',stage/'etc/login.defs')
for name in ('var/log','var/mail','dev/pts','etc/systemd/system/getty.target.wants'):
 (stage/name).mkdir(parents=True,exist_ok=True)
(stage/'etc/systemd/system/getty.target.wants/getty@tty1.service').symlink_to('/usr/lib/systemd/system/getty@.service')
profile=sys.modules['live_console'].stage_console(stage)
assert profile['retained_owned_links']==['etc/systemd/system/getty.target.wants/getty@tty1.service']
unit_path='/'+str((stage/'etc/systemd/system').relative_to(root))+':/usr/lib/systemd/system'
unit_check=subprocess.run(['chroot',str(root),'/usr/bin/env','-i','PATH=/usr/bin:/usr/sbin','LC_ALL=C',
 'SYSTEMD_UNIT_PATH='+unit_path,'/usr/bin/systemd-analyze','verify','--man=no','--generators=no',
 *sys.modules['live_console'].UNITS],text=True,capture_output=True)
(base/'unit-verify.log').write_text(unit_check.stdout+unit_check.stderr)
assert unit_check.returncode==0,(unit_check.returncode,unit_check.stdout,unit_check.stderr)
subprocess.run(['mount','-t','devpts','-o','newinstance,ptmxmode=0666,mode=0620','devpts',str(stage/'dev/pts')],check=True)
subprocess.run(['mount','-t','proc','-o','nosuid,nodev,noexec','proc',str(stage/'proc')],check=True)
(stage/'dev/ptmx').symlink_to('pts/ptmx')
os.mknod(stage/'dev/tty',stat.S_IFCHR|0o666,os.makedev(5,0))
libc=ctypes.CDLL(None,use_errno=True)
libc.ptsname_r.argtypes=[ctypes.c_int,ctypes.c_char_p,ctypes.c_size_t]
sessions=[]
def session(name,args,expect_shell=False,unprivileged=False,password_attempt=False):
 master=os.open(stage/'dev/ptmx',os.O_RDWR|os.O_NOCTTY)
 assert libc.grantpt(master)==0 and libc.unlockpt(master)==0
 buf=ctypes.create_string_buffer(128);assert libc.ptsname_r(master,buf,len(buf))==0
 slave=os.open(stage/buf.value.decode().lstrip('/'),os.O_RDWR|os.O_NOCTTY)
 def setup():
  os.setsid();fcntl.ioctl(0,termios.TIOCSCTTY,0)
  os.chroot(stage);os.chdir('/')
  if unprivileged:os.setgroups([]);os.setgid(101);os.setuid(101)
 process=subprocess.Popen(args,stdin=slave,stdout=slave,stderr=slave,preexec_fn=setup,
  env={'PATH':'/usr/bin:/usr/sbin','TERM':'vt100','LC_ALL':'C','HOME':'/'})
 os.close(slave);output=b'';sent=False;password_sent=False;deadline=time.monotonic()+20
 try:
  while time.monotonic()<deadline:
   ready,_,_=select.select([master],[],[],0.1)
   if ready:
    try:chunk=os.read(master,65536)
    except OSError as error:
     if error.errno==errno.EIO:break
     raise
    if not chunk:break
    output+=chunk
    if len(output)>65536:raise AssertionError('Unexpected excessive login output')
   if expect_shell and not sent and b'# ' in output:
    # Split the literal marker so terminal echo cannot satisfy the assertion.
    command="printf 'TODDY_%s uid=%s euid=%s home=%s shell=%s\\n' CONSOLE_OK \"$(id -u)\" \"$EUID\" \"$HOME\" \"$0\"; exit\n"
    os.write(master,command.encode());sent=True
   if password_attempt and not password_sent and b'Password:' in output:
    os.write(master,b'public-invalid-probe-input\n');password_sent=True
   if password_attempt and b'Login incorrect' in output:break
   if process.poll() is not None and not ready:break
  if expect_shell:
   assert b'TODDY_CONSOLE_OK uid=0 euid=0 home=/root shell=-bash' in output,output.decode(errors='replace')
   process.wait(timeout=5);assert process.returncode==0
  elif password_attempt:
   assert password_sent and b'Login incorrect' in output and b'TODDY_CONSOLE_OK' not in output,output
  else:
   process.wait(timeout=5);assert process.returncode!=0 and b'# ' not in output,output
 finally:
  if process.poll() is None:
   os.killpg(process.pid,signal.SIGKILL);process.wait(timeout=5)
  os.close(master)
 text=output.decode(errors='replace');(base/(name+'.log')).write_text(text)
 result={'case':name,'exit':process.returncode,'transcript':text,'private_devpts':True}
 sessions.append(result)
for unit in sys.modules['live_console'].UNITS:
 content=(stage/('etc/systemd/system/'+unit+'.d/50-toddy-live.conf')).read_text()
 command=next(line.removeprefix('ExecStart=-') for line in content.splitlines() if line.startswith('ExecStart=-'))
 args=shlex.split(command.replace('${TERM}','vt100'))
 session(unit+'-login-shell',args,expect_shell=True)
session('locked-password-refusal',['/usr/bin/login','root'],password_attempt=True)
session('unprivileged-preauthentication-refusal',['/usr/bin/login','-f','root'],unprivileged=True)
assert {name:digest(stage/'etc'/name) for name in accounts}==accounts
assert {name:digest(root/name) for name in before}==before
assert not (stage/'run/toddy/live-session').exists()
refusals=[]
for case in ('existing-profile','runtime-marker','redirected-parent','unlocked-root'):
 negative=base/case;negative.mkdir();sys.modules['live_accounts'].stage_accounts(negative,BASELINE)
 if case=='existing-profile':
  path=negative/'usr/share/toddy/live.issue';path.parent.mkdir(parents=True);path.write_text('public preservation sentinel\n')
 elif case=='runtime-marker':
  path=negative/'run/toddy/live-session';path.parent.mkdir(parents=True);path.write_text('public preservation sentinel\n')
 elif case=='redirected-parent':
  outside=base/'outside';outside.mkdir();path=outside/'keep';path.write_text('public preservation sentinel\n');(negative/'usr').symlink_to(outside)
 else:
  path=negative/'etc/shadow';path.write_text(path.read_text().replace('root:!:','root::'))
 saved=digest(path)
 try:sys.modules['live_console'].stage_console(negative)
 except ValueError as error:refusals.append({'case':case,'reason':str(error)})
 else:raise AssertionError('Unsafe console input accepted')
 assert digest(path)==saved
print(json.dumps({'profile':profile,'native_runtime':runtime_report,'sessions':sessions,'negative_cases':refusals,
 'native_systemd_unit_verify':{'exit':unit_check.returncode,'stdout':unit_check.stdout,'stderr':unit_check.stderr},
 'native_login_mode':oct(login_mode),
 'private_accounts_unchanged':True,'installed_accounts_and_dpkg_unchanged':True,
 'source_sha256':{name:hashlib.sha256(base64.b64decode(content)).hexdigest() for name,content in SOURCES.items()},
 'builder_kernel':os.uname().release,'systemd_unit_activation_verified':False,'native_kernel_or_iso_boot':False},indent=2))
'''
inner = inner.replace('BASELINE', repr(baseline)).replace('SOURCES', repr(sources))
outer = r'''from pathlib import Path
import base64,json,os,shutil,subprocess,tempfile
base=Path(tempfile.mkdtemp(prefix='toddy-live-console-',dir='/mnt/lfs/tmp'))
print('LIVE_CONSOLE_FIXTURE '+str(base),flush=True)
script=base64.b64decode(INNER).decode().replace('Path(BASE)', 'Path('+repr(str(base))+')')
result=subprocess.run(['unshare','--mount','--pid','--fork','--kill-child=KILL','--propagation','private','python3','-'],
 input=script,text=True,capture_output=True,timeout=90,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
print(result.stdout,result.stderr,flush=True)
if result.returncode:
 print('Preserved private fixture: '+str(base),flush=True)
 result.check_returncode()
assert not any((base/'image/dev/pts').iterdir()) and not any((base/'image/proc').iterdir())
shutil.rmtree(base)
print('PRIVATE_FIXTURE_REMOVED',flush=True)
'''.replace('INNER', repr(base64.b64encode(inner.encode()).decode()))
# Substitute only the payload identifiers; source text is transferred over stdin
# into the private process and never synchronized into the active build checkout.
result = subprocess.run(['python3', 'scripts/host/vm.py', 'ssh',
    'source /opt/toddy-build/scripts/build/target.sh; guard_target && python3 -'],
    input=outer, text=True, capture_output=True)
path = Path('.local/logs/h10-live-console-probe.json')
data = (json.dumps({'exit': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr}, indent=2) + '\n').encode()
sha = hashlib.sha256(data).hexdigest()
path.with_name(path.stem + '.' + sha + '.json').write_bytes(data)
path.write_bytes(data)
print(result.stdout, result.stderr)
print('exit', result.returncode, 'SHA256', sha)
result.check_returncode()
