#!/usr/bin/env python3
"""Exercise the observer with real native credentials/filters, not APT acceptance."""
import base64
import hashlib
import json
from pathlib import Path
import subprocess
from vm import ssh_args

ROOT = Path(__file__).resolve().parents[2]
WORKER = r'''
#include <errno.h>
#include <grp.h>
#include <pwd.h>
#include <seccomp.h>
#include <stdlib.h>
#include <string.h>
#include <sys/prctl.h>
#include <sys/syscall.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>
int main(int argc,char **argv) {
 if(argc>2 && !strcmp(argv[1],"inherit")) {
  scmp_filter_ctx c=seccomp_init(SCMP_ACT_ALLOW);
  if(!c || seccomp_rule_add(c,SCMP_ACT_ERRNO(EPERM),SCMP_SYS(getppid),0) || seccomp_load(c))return 28;
  seccomp_release(c);execvp(argv[2],argv+2);return 29;
 }
 if(argc!=2 || geteuid()!=0)return 20;
 int mode=atoi(argv[1]);struct passwd *p=getpwnam("tester");if(!p)return 21;
 pid_t child=fork();if(child<0)return 22;
 if(child==0) {
  if(mode!=0 && mode!=4) {
   gid_t group=mode==3?0:p->pw_gid;
   if(setgroups(1,&group) || setresgid(p->pw_gid,p->pw_gid,p->pw_gid) ||
      setresuid(p->pw_uid,p->pw_uid,p->pw_uid))_exit(23);
  }
  if(mode!=0 && mode!=2) {
   if(prctl(PR_SET_NO_NEW_PRIVS,1,0,0,0))_exit(24);
   scmp_filter_ctx c=seccomp_init(SCMP_ACT_ALLOW);
   if(!c || seccomp_rule_add(c,SCMP_ACT_ERRNO(EPERM),SCMP_SYS(getppid),0) || seccomp_load(c))_exit(25);
   errno=0;if(syscall(SYS_getppid)!=-1 || errno!=EPERM)_exit(26);
   seccomp_release(c);
  }
  struct timespec duration={0,500000000};nanosleep(&duration,0);
  _exit(mode==5?7:0);
 }
 int status;if(waitpid(child,&status,0)!=child || !WIFEXITED(status))return 27;
 return WEXITSTATUS(status);
}
'''

REMOTE = r'''
import base64,hashlib,json,subprocess,tempfile
from pathlib import Path
subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
base=Path(tempfile.mkdtemp(prefix='toddy-apt-worker-',dir='/mnt/lfs/tmp'))
native='/'+str(base.relative_to('/mnt/lfs'))
(base/'observer.py').write_bytes(base64.b64decode(OBSERVER))
(base/'worker.c').write_bytes(base64.b64decode(WORKER))
environment=['chroot','/mnt/lfs','/usr/bin/env','-i','PATH=/usr/bin:/usr/sbin','LC_ALL=C','HOME=/root']
compiled=subprocess.run(environment+['cc','-D_GNU_SOURCE','-O2','-Wall','-Wextra','-Werror',native+'/worker.c','-lseccomp','-o',native+'/worker'],capture_output=True,text=True)
(base/'compile.log').write_text(compiled.stdout+compiled.stderr)
if compiled.returncode:raise RuntimeError(compiled.stderr)
cases=[]
for case,mode,label in [(1,1,'native filter and unprivileged identity'),(0,0,'root without filter'),
                   (2,2,'unprivileged without filter'),(3,3,'unexpected supplementary root group'),
                   (4,4,'filter with root identity'),(5,5,'sandboxed command failure'),
                   (6,2,'inherited filter alone'),(7,1,'new filter in already filtered environment')]:
 launcher=environment+([native+'/worker','inherit'] if case in (6,7) else [])
 command=launcher+['python3','-B',native+'/observer.py','--output',native+'/case-'+str(case)+'.json',
  '--user','tester','--executable',native+'/worker','--',native+'/worker',str(mode)]
 result=subprocess.run(command,text=True,capture_output=True,timeout=20)
 (base/('case-'+str(case)+'.log')).write_text(result.stdout+result.stderr)
 expected=0 if case in (1,7) else 1
 if result.returncode!=expected:raise RuntimeError((label,result.returncode,result.stdout,result.stderr))
 record=json.loads((base/('case-'+str(case)+'.json')).read_text())
 assert record['accepted']==(case in (1,7)) and record['command_exit']==(7 if mode==5 else 0),record
 assert record['inherited_seccomp_filters']==(1 if case in (6,7) else 0),record
 assert record['states'],record
 cases.append({'case':label,'observer_exit':result.returncode,'record':record})
print(json.dumps({'fixture':str(base),'native_compile_exit':compiled.returncode,
 'source_sha256':{name:hashlib.sha256((base/name).read_bytes()).hexdigest() for name in ['observer.py','worker.c']},
 'cases':cases,'actual_apt_acquisition_tested':False,'installed_target_modified':False},indent=2))
'''


def main():
    observer = (ROOT / 'scripts/build/h07/apt-worker-probe.py').read_bytes()
    script = REMOTE.replace('OBSERVER', repr(base64.b64encode(observer).decode()))
    script = script.replace('WORKER', repr(base64.b64encode(WORKER.encode()).decode()))
    result = subprocess.run(ssh_args() + ['python3 -B -'], input=script,
                            text=True, capture_output=True, timeout=120)
    if result.returncode:
        raise SystemExit(result.stdout + result.stderr)
    raw = result.stdout.encode()
    report = json.loads(raw)
    sha = hashlib.sha256(raw).hexdigest()
    path = ROOT / '.local/logs' / ('h07-apt-worker-observer-' + sha + '.json')
    path.write_bytes(raw)
    print(json.dumps({'report': str(path), 'sha256': sha, 'fixture': report['fixture'],
                      'cases': len(report['cases']), 'actual_apt_acquisition_tested': False}))


if __name__ == '__main__':
    main()
