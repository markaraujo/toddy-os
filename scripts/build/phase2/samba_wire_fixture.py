from pathlib import Path
import ctypes
import hashlib
import json
import os
import secrets
import signal
import socket
import subprocess
import time

assert os.getuid() == 0
libc = ctypes.CDLL(None, use_errno=True)
for capability in (18, 8):
    assert libc.prctl(24, capability, 0, 0, 0) == 0, ctypes.get_errno()
class Header(ctypes.Structure):
    _fields_ = [('version',ctypes.c_uint32),('pid',ctypes.c_int)]
class Data(ctypes.Structure):
    _fields_ = [('effective',ctypes.c_uint32),('permitted',ctypes.c_uint32),('inheritable',ctypes.c_uint32)]
bits = sum(1 << cap for cap in (0,1,3,6,7,24))
header = Header(0x20080522,0)
data = (Data*2)(Data(bits,bits,0),Data(0,0,0))
assert libc.capset(ctypes.byref(header),ctypes.byref(data)) == 0, ctypes.get_errno()
status = dict(line.split(':',1) for line in Path('/proc/self/status').read_text().splitlines() if ':' in line)
assert int(status['CapEff'],16) == bits == int(status['CapBnd'],16)
assert status['NoNewPrivs'].strip() == '1'
base = Path('/fixture')
for part in ('private','state','cache','lock','pid','logs','share','client'):
    (base/part).mkdir(mode=0o700)
for part in ('share','client'):
    os.chown(base/part,101,101)
secret = secrets.token_urlsafe(24)
config = base/'smb.conf'
config.write_text('''[global]
server role = standalone server
workgroup = WORKGROUP
netbios name = TODDYSMBTEST
security = user
passdb backend = smbpasswd:/fixture/private/smbpasswd
private dir = /fixture/private
state directory = /fixture/state
cache directory = /fixture/cache
lock directory = /fixture/lock
pid directory = /fixture/pid
log file = /fixture/logs/server.log
interfaces = lo
bind interfaces only = yes
smb ports = 1445
server min protocol = SMB2_02
server max protocol = SMB3_11
load printers = no
printing = bsd
printcap name = /dev/null
disable spoolss = yes
map to guest = Never
[proof]
path = /fixture/share
read only = no
valid users = tester
''')
server_env = dict(os.environ,LD_LIBRARY_PATH='/stage/usr/lib:/stage/usr/lib/samba',LD_BIND_NOW='1')
client_env = dict(os.environ,LD_LIBRARY_PATH='/candidate/usr/lib:/candidate/usr/lib/samba',LD_BIND_NOW='1',HOME='/fixture/client')
account = subprocess.run(['/stage/usr/bin/smbpasswd','-s','-a','tester','-c',str(config)],input=secret+'\n'+secret+'\n',text=True,capture_output=True,env=server_env)
(base/'account.stdout').write_text(account.stdout)
(base/'account.stderr').write_text(account.stderr)
assert account.returncode == 0, (account.returncode,account.stdout,account.stderr)
auths = []
for name,password in (('auth',secret),('wrong-auth',secrets.token_urlsafe(24))):
    path=base/name
    with path.open('x') as stream:stream.write('username = tester\npassword = '+password+'\ndomain = WORKGROUP\n')
    path.chmod(0o600)
    os.chown(path,101,101)
    auths.append(path)
payload=b'Toddy SMB native exchange\nUTF-8 a\xc3\xa7\xc3\xa3o\n'
(base/'client/input.txt').write_bytes(payload)
os.chown(base/'client/input.txt',101,101)

def as_client():
    os.setgroups([101])
    os.setgid(101)
    os.setuid(101)

def request(label,command,auth='auth'):
    result=subprocess.run(['/candidate/usr/bin/smbclient','//127.0.0.1/proof','-p','1445','-t','3','-A',str(base/auth),'-s',str(config),'-c',command],
                          cwd=base/'client',env=client_env,preexec_fn=as_client,text=True,capture_output=True,timeout=15)
    (base/(label+'.stdout')).write_text(result.stdout)
    (base/(label+'.stderr')).write_text(result.stderr)
    return result

server=None
stream=None

def start_server(index):
    global server,stream
    stream=(base/f'server{index}.stdout').open('xb')
    server=subprocess.Popen(['/stage/usr/sbin/smbd','--foreground','--no-process-group','--debug-stdout','-d','0','-s',str(config)],env=server_env,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
    deadline=time.monotonic()+8
    while time.monotonic()<deadline:
        assert server.poll() is None, ('server exited',server.returncode)
        try:
            with socket.create_connection(('127.0.0.1',1445),timeout=0.15):return
        except OSError:time.sleep(0.05)
    raise AssertionError('SMB fixture did not listen within bounded startup window')

def stop_server():
    global server,stream
    if server is not None:
        if server.poll() is None:server.terminate()
        try:server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait(timeout=3)
            raise AssertionError('SMB fixture required forced termination')
        server=None
    if stream is not None:
        stream.close()
        stream=None

results={}
try:
    start_server(1)
    wrong=request('wrong','ls','wrong-auth')
    assert wrong.returncode != 0 and 'NT_STATUS_LOGON_FAILURE' in wrong.stdout+wrong.stderr, (wrong.returncode,wrong.stdout,wrong.stderr)
    assert not list((base/'share').iterdir())
    results['wrong_auth_refused_without_effect']=True
    good=request('roundtrip','put input.txt payload.txt; get payload.txt fetched.txt; del payload.txt')
    assert good.returncode == 0, (good.returncode,good.stdout,good.stderr)
    assert (base/'client/fetched.txt').read_bytes() == payload
    assert not list((base/'share').iterdir())
    results['upload_download_delete_sha256']=hashlib.sha256(payload).hexdigest()
    stop_server()
    stopped=request('stopped','ls')
    assert stopped.returncode != 0, (stopped.returncode,stopped.stdout,stopped.stderr)
    results['stopped_server_refused']=True
    start_server(2)
    recovered=request('reconnected','ls')
    assert recovered.returncode == 0, (recovered.returncode,recovered.stdout,recovered.stderr)
    results['reconnected_after_restart']=True
finally:
    stop_server()
    for path in auths:path.unlink(missing_ok=True)
    for path in (base/'private').glob('*'):
        if path.is_file():path.unlink()
results.update(scope='Actual loopback SMB2/3 fixture inside isolated VM with staged client and server; no desktop or installed-package acceptance',capabilities=bits)
(base/'results.json').write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps(results))
