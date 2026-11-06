#!/usr/bin/env python3
"""Check native unprivileged DBus rejection of malformed/oversized config XML."""
import json
import subprocess

PROGRAM = r'''import json,os,pathlib,pwd,resource,subprocess,tempfile
identity=pwd.getpwnam('tester')
def restricted():
 os.setgroups([])
 os.setgid(identity.pw_gid)
 os.setuid(identity.pw_uid)
 resource.setrlimit(resource.RLIMIT_CPU,(2,2))
 resource.setrlimit(resource.RLIMIT_AS,(128*1024*1024,128*1024*1024))
 resource.setrlimit(resource.RLIMIT_CORE,(0,0))
results=[]
with tempfile.TemporaryDirectory(prefix='toddy-dbus-xml-') as directory:
 root=pathlib.Path(directory);root.chmod(0o755)
 for name,data,expected in [('malformed',b'<busconfig><type>session</type>',b'Error in file'),
                            ('oversized',b' '*(1024*1024+1),b'is too large')]:
  source=root/name;source.write_bytes(data);source.chmod(0o644)
  result=subprocess.run(['/usr/bin/dbus-daemon','--nofork','--config-file='+str(source)],
                        capture_output=True,timeout=5,preexec_fn=restricted)
  passed=result.returncode==1 and expected in result.stderr
  results.append({'case':name,'bytes':len(data),'exit':result.returncode,
                  'stderr':result.stderr.decode(),'passed':passed})
print(json.dumps({'uid':identity.pw_uid,'cpu_limit_seconds':2,'address_space_limit_bytes':128*1024*1024,
                  'cases':results,'passed':all(r['passed'] for r in results)}))
raise SystemExit(0 if all(r['passed'] for r in results) else 1)
'''


def main():
    subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
    result=subprocess.run(['chroot','/mnt/lfs','/usr/bin/env','-i','HOME=/tmp','PATH=/usr/bin:/usr/sbin','LC_ALL=C',
                           '/usr/bin/python3','-'],input=PROGRAM,text=True,capture_output=True)
    print(json.dumps({'scope':'Native DBus daemon config XML only; no privileged helper execution or complete CVE mitigation claim',
                      'exit':result.returncode,'stdout':result.stdout,'stderr':result.stderr},indent=2))
    raise SystemExit(result.returncode)


if __name__=='__main__':main()
