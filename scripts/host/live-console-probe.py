#!/usr/bin/env python3
"""Executed through the real live serial login, never installed in the image."""
import json,os,pathlib,subprocess,sys,tempfile,time
P=pathlib.Path
def run(*args,timeout=45):
 r=subprocess.run(args,capture_output=True,text=True,timeout=timeout)
 if r.returncode:raise RuntimeError(json.dumps({'argv':args,'exit':r.returncode,'out':r.stdout,'err':r.stderr}))
 return r.stdout.strip()
def main():
 token,network=sys.argv[1:]
 assert os.getuid()==0 and os.uname().release=='7.1.8-toddy'
 assert P('/proc/1/comm').read_text().strip()=='systemd'
 assert run('tty')=='/dev/ttyS0'
 assert 'toddy.live' in P('/proc/cmdline').read_text().split()
 assert P('/run/toddy/live-session').is_file()
 assert run('systemd-detect-virt','--vm') in ('kvm','qemu')
 assert run('findmnt','-no','FSTYPE','/')=='overlay'
 assert run('findmnt','-no','FSTYPE','/run/toddy/media')=='iso9660'
 assert run('findmnt','-no','FSTYPE','/run/toddy/lower')=='squashfs'
 assert run('findmnt','-no','FSTYPE','/run')=='tmpfs'
 for directory in ['/run/toddy/media','/run/toddy/lower']:
  try:P(directory,'toddy-must-refuse-write').write_text(token)
  except OSError as e:assert e.errno==30
  else:raise AssertionError('Read-only live input accepted a write')
 proof=P('/root/toddy-volatile-proof')
 assert not proof.exists(),'Previous live write survived a fresh boot'
 proof.write_text(token)
 assert P('/run/toddy/upper/root/toddy-volatile-proof').read_text()==token
 assert not P('/sources').exists() or not any(P('/sources').iterdir())
 assert run('dpkg','--audit')==''
 run('apt-get','check')
 assert any(line=='root:!:::::::' for line in P('/etc/shadow').read_text().splitlines())
 with tempfile.TemporaryDirectory() as folder:
  source=P(folder,'hello.c');binary=P(folder,'hello')
  source.write_text('#include <stdio.h>\nint main(void){puts("TODDY_NATIVE_C_OK");return 0;}\n')
  run('cc','-Werror','-O2',str(source),'-o',str(binary))
  assert run(str(binary))=='TODDY_NATIVE_C_OK'
  linkage=run('ldd',str(binary));assert '/tools/' not in linkage and '/sources/' not in linkage
  assert '/lib64/ld-linux-x86-64.so.2' in linkage
 assert not P('/sys/module/dummy').exists()
 run('modprobe','dummy','numdummies=1')
 try:assert P('/sys/class/net/dummy0').exists()
 finally:run('modprobe','-r','dummy')
 assert not P('/sys/module/dummy').exists()
 services={unit:run('systemctl','is-active',unit) for unit in ['systemd-networkd','systemd-resolved','dbus.socket']}
 assert all(value=='active' for value in services.values())
 routes=[];dns=[]
 if network=='online':
  for attempt in range(30):
   routes=json.loads(run('ip','-4','-j','route','show','default'))
   if routes:break
   time.sleep(1)
  assert routes,'DHCP did not supply a default route'
  assert any(row.get('gateway')=='10.0.2.2' for row in routes)
  assert 'nameserver 127.0.0.53' in P('/etc/resolv.conf').read_text()
  dns=run('getent','ahostsv4','example.org').splitlines()
  assert dns,'Runtime resolved DNS lookup failed'
 else:
  assert network=='offline'
  assert not json.loads(run('ip','-4','-j','route','show','default'))
 report={'token':token,'kernel':os.uname().release,'pid1':'systemd','console':'ttyS0','real_console_login':True,
  'firmware':'uefi' if P('/sys/firmware/efi').is_dir() else 'bios','root':'overlay','volatile_write':True,
  'read_only_media':True,'read_only_lower':True,'native_compile_execute':True,'native_linkage':linkage,
  'module_load_unload':True,'package_audit':True,'locked_password':True,'services':services,
  'network':network,'dhcp_route':routes,'dns_records':len(dns),'uptime_seconds':float(P('/proc/uptime').read_text().split()[0])}
 print('TODDY_LIVE_TEST_OK '+json.dumps(report,sort_keys=True),flush=True)
 run('sync');run('systemctl','poweroff')
if __name__=='__main__':
 try:main()
 except BaseException as e:
  print('TODDY_LIVE_TEST_FAIL '+str(e),flush=True);raise
