"""Trusted scope launcher: no user command before parent verifies cgroup and opens gate."""
import json
import os
from pathlib import Path
import sys
import time

parent=int(sys.argv[1]);ticks=sys.argv[2];folder=Path(sys.argv[3]);command=sys.argv[4:]
assert folder.is_absolute() and folder.stat().st_uid==os.getuid() and folder.stat().st_mode&0o777==0o700
assert command and command[0].startswith('/')
with (folder/'ready.part').open('x') as f:
    json.dump({'pid':os.getpid(),'uid':os.getuid()},f);f.flush();os.fsync(f.fileno())
(folder/'ready.part').replace(folder/'ready')
until=time.monotonic()+15
while not (folder/'go').exists():
    assert time.monotonic()<until,'scope_gate_deadline'
    assert Path('/proc',str(parent),'stat').read_text().split()[21]==ticks,'scope_parent_lost'
    time.sleep(.01)
os.execv(command[0],command)
