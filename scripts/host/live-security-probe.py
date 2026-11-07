#!/usr/bin/env python3
"""Final foundation XML boundary checks through the actual live console."""
import hashlib,json,os,pathlib,pwd,resource,subprocess,sys,tempfile
P=pathlib.Path

def main():
 token,network=sys.argv[1:]
 assert os.getuid()==0 and os.uname().release=='7.1.8-toddy'
 assert P('/proc/1/comm').read_text().strip()=='systemd'
 assert subprocess.check_output(['tty'],text=True).strip()=='/dev/ttyS0'
 assert P('/run/toddy/live-session').is_file()
 identity=pwd.getpwnam('nobody');assert identity.pw_uid!=0
 def restricted():
  os.setgroups([]);os.setgid(identity.pw_gid);os.setuid(identity.pw_uid)
  resource.setrlimit(resource.RLIMIT_CPU,(2,2));resource.setrlimit(resource.RLIMIT_AS,(128*1024**2,128*1024**2))
  resource.setrlimit(resource.RLIMIT_CORE,(0,0))
 trusted=[]
 for base in ('/etc/dbus-1','/usr/share/dbus-1'):
  for p in [P(base),*P(base).rglob('*')]:
   resolved=p.resolve();st=resolved.stat()
   assert st.st_uid==0 and not st.st_mode&0o022
   trusted.append({'path':str(p),'resolved':str(resolved),'uid':st.st_uid,'mode':oct(st.st_mode&0o7777)})
 cases=[]
 with tempfile.TemporaryDirectory(prefix='toddy-xml-bounds-') as directory:
  root=P(directory);root.chmod(0o755)
  for name,data,expected in [('malformed',b'<busconfig><type>session</type>',b'Error in file'),('oversized',b' '*(1024**2+1),b'is too large')]:
   source=root/name;source.write_bytes(data);source.chmod(0o644)
   r=subprocess.run(['/usr/bin/dbus-daemon','--nofork','--config-file='+str(source)],capture_output=True,timeout=5,preexec_fn=restricted)
   assert r.returncode==1 and expected in r.stderr,(name,r.returncode,r.stderr)
   cases.append({'case':name,'bytes':len(data),'exit':r.returncode,'stderr':r.stderr.decode(),'passed':True})
  code='import os,json,resource; print(json.dumps({"uid":os.getuid(),"cpu":resource.getrlimit(resource.RLIMIT_CPU),"as":resource.getrlimit(resource.RLIMIT_AS)}))'
  r=subprocess.run(['/usr/bin/python3','-c',code],capture_output=True,text=True,timeout=5,preexec_fn=restricted,check=True)
  limits=json.loads(r.stdout);assert limits=={'uid':identity.pw_uid,'cpu':[2,2],'as':[128*1024**2]*2}
 report={'token':token,'firmware':'uefi' if P('/sys/firmware/efi').is_dir() else 'bios','real_console_login':True,
  'scope':'Final live foundation trusted DBus XML configuration and bounded unprivileged rejection; not complete CVE mitigation or future desktop coverage',
  'trusted_configuration':trusted,'limits':limits,'cases':cases,'core_binary_sha256':{p:hashlib.sha256(P(p).read_bytes()).hexdigest() for p in ('/usr/lib/libc.so.6','/usr/lib/systemd/systemd','/usr/bin/dbus-daemon','/usr/lib/libexpat.so.1')}}
 print('TODDY_LIVE_TEST_OK '+json.dumps(report,sort_keys=True),flush=True)
 subprocess.run(['systemctl','poweroff'],check=True)
if __name__=='__main__':
 try:main()
 except BaseException as error:print('TODDY_LIVE_TEST_FAIL '+str(error),flush=True);raise
