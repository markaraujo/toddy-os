#!/usr/bin/env python3
"""Fixed trusted voice launcher: no engine exec after its actual parent is lost."""
import ctypes
import os
import resource
import signal
import sys

parent=int(sys.argv[1]);command=sys.argv[2:]
if not command or not os.path.isabs(command[0]):raise SystemExit(125)
libc=ctypes.CDLL(None,use_errno=True)
# No preexec_fn in the threaded GTK process. A death before this fresh
# interpreter arms prctl changes getppid and prevents microphone activation.
if libc.prctl(1,signal.SIGKILL,0,0,0)!=0 or os.getppid()!=parent:
    raise SystemExit(125)
resource.setrlimit(resource.RLIMIT_CORE,(0,0))
os.execvpe(command[0],command,os.environ)
