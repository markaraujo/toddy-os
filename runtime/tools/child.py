#!/usr/bin/env python3
"""Trusted command launcher: die if the unprivileged tool service disappears before exec."""
import ctypes
import os
import resource
import signal
import sys

parent=int(sys.argv[1]);command=sys.argv[2:]
if not command:raise SystemExit(125)
libc=ctypes.CDLL(None,use_errno=True)
# Set after fork in this fresh interpreter, avoiding preexec_fn in a threaded
# service. Check after prctl closes the parent-death setup race.
if libc.prctl(1,signal.SIGKILL,0,0,0)!=0 or os.getppid()!=parent:
    raise SystemExit(125)
resource.setrlimit(resource.RLIMIT_CORE,(0,0))
os.execvpe(command[0],command,os.environ)
