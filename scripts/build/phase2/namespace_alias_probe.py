#!/usr/bin/env python3
"""New namespace FD alias stays within the existing private proc authority."""
import errno
import json
import os
from pathlib import Path
import subprocess
import sys
shared_memory=None
if '--private-shm' in sys.argv:
    sys.argv.remove('--private-shm')
    marker=Path('/dev/shm/toddy-namespace-shm-probe-1');marker.write_text('private native fixture')
    work=Path('/build');source=work/'shm-probe.c';binary=work/'shm-probe'
    source.write_text(r"""#include <sys/mman.h>
#include <sys/wait.h>
#include <fcntl.h>
#include <unistd.h>
#include <string.h>
int main(void) {
 int fd=shm_open("/toddy-native-jit-proof",O_CREAT|O_EXCL|O_RDWR,0600),status;
 if(fd<0 || ftruncate(fd,4096))return 1;
 void *p=mmap(0,4096,PROT_READ|PROT_WRITE,MAP_SHARED,fd,0);
 if(p==MAP_FAILED)return 2;
 unsigned char code[]={0xb8,42,0,0,0,0xc3};memcpy(p,code,sizeof(code));
 if(mprotect(p,4096,PROT_READ|PROT_EXEC))return 3;
 pid_t child=fork();if(child<0)return 4;
 if(child==0)_exit(((int(*)(void))p)()==42?0:5);
 if(waitpid(child,&status,0)!=child || !WIFEXITED(status) || WEXITSTATUS(status))return 6;
 if(munmap(p,4096) || close(fd) || shm_unlink("/toddy-native-jit-proof"))return 7;
 return 0;
}
""")
    subprocess.run(['cc',str(source),'-lrt','-o',str(binary)],check=True)
    subprocess.run([str(binary)],check=True)
    shared_memory={'native_posix_shared_child_rx_execution':True,'private_tmpfs_bytes':os.statvfs('/dev/shm').f_blocks*os.statvfs('/dev/shm').f_frsize}
    assert shared_memory['private_tmpfs_bytes']==256*1024**2
font_config=None
if '--font-config' in sys.argv:
    import hashlib
    sys.argv.remove('--font-config')
    path=Path('/etc/fonts/fonts.conf');data=path.read_bytes();assert data
    try: fd=os.open(path,os.O_WRONLY|os.O_CLOEXEC)
    except OSError as error:assert error.errno in (errno.EROFS,errno.EACCES)
    else:os.close(fd);raise AssertionError('Installed font configuration became writable')
    links=list(Path('/etc/fonts/conf.d').glob('*.conf'));assert links
    for link in links:
        assert link.is_symlink() and link.resolve().is_relative_to('/usr/share/fontconfig/conf.avail')
        assert link.read_bytes()
    font_config={'sha256':hashlib.sha256(data).hexdigest(),'write_denied':True,'config_links_read':len(links)}
assert os.readlink('/dev/fd')=='/proc/self/fd'
assert set(os.listdir('/dev/fd'))==set(os.listdir('/proc/self/fd'))
fd=os.open('/src/isolation_probe.py',os.O_RDONLY|os.O_CLOEXEC)
try:
    try:extra=os.open('/dev/fd/'+str(fd),os.O_WRONLY|os.O_CLOEXEC)
    except OSError as error:assert error.errno in (errno.EROFS,errno.EACCES)
    else:os.close(extra);raise AssertionError('read-only source became writable through fd alias')
finally:os.close(fd)
result=subprocess.run(['python3','/src/isolation_probe.py',*sys.argv[1:]],capture_output=True,text=True,check=True)
report=json.loads(result.stdout);report['dev_fd_alias']='private /proc/self/fd'
report['source_fd_write_denied']=True
if font_config: report['font_configuration']=font_config
if shared_memory:
    report['private_shared_memory']=shared_memory
    marker.unlink()
print(json.dumps(report,indent=2))
