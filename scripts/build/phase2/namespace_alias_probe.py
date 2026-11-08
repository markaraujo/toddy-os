#!/usr/bin/env python3
"""New namespace FD alias stays within the existing private proc authority."""
import errno
import json
import os
from pathlib import Path
import subprocess
import sys
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
print(json.dumps(report,indent=2))
