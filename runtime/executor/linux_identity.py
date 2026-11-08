#!/usr/bin/env python3
"""Linux-only identity helper for the disposable native proof, not a grant API."""
import ctypes
import errno
import os
from pathlib import Path
import sys


def confine_root_fixture():
    assert os.getuid()==0 and os.getpid()==1
    libc=ctypes.CDLL(None,use_errno=True)
    allowed=sum(1<<number for number in (0,1,3,5,6,7))
    last=int(Path('/proc/sys/kernel/cap_last_cap').read_text())
    for number in range(last+1):
        if not allowed&(1<<number) and libc.prctl(24,number,0,0,0)!=0:
            raise OSError(ctypes.get_errno(),'fixture_capability_drop_failed')
    class Header(ctypes.Structure):_fields_=[('version',ctypes.c_uint32),('pid',ctypes.c_int)]
    class Data(ctypes.Structure):_fields_=[('effective',ctypes.c_uint32),('permitted',ctypes.c_uint32),('inheritable',ctypes.c_uint32)]
    data=(Data*2)(Data(allowed,allowed,0),Data(0,0,0));header=Header(0x20080522,0)
    if libc.capset(ctypes.byref(header),ctypes.byref(data))!=0 or libc.prctl(38,1,0,0,0)!=0:
        raise OSError(ctypes.get_errno(),'fixture_capability_drop_failed')


def identity_exec(uid,command):
    assert os.getuid()==0 and 1<=uid<=65534 and command
    os.setgroups([]);os.setresgid(uid,uid,uid);os.setresuid(uid,uid,uid)
    libc=ctypes.CDLL(None,use_errno=True)
    if libc.prctl(38,1,0,0,0)!=0:raise OSError(ctypes.get_errno(),'identity_drop_failed')
    os.execvpe(command[0],command,os.environ)

if __name__=='__main__':identity_exec(int(sys.argv[1]),sys.argv[2:])
