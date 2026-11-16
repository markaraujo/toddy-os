"""Run only inside its own disposable user-systemd unit, never another user's service."""
import json
import os
from pathlib import Path
import sys
import tempfile
import time
sys.path.insert(0,sys.argv[1])
from runtime.tools.scoped import ScopedShell
from runtime.tools.native import ToolError

unit=os.environ['TODDY_SCOPE_PARENT'];assert unit.startswith('toddy-scope-proof-')
runner=ScopedShell(unit)
with tempfile.TemporaryDirectory(prefix='toddy-managed-shell-') as folder:
    workspace=Path(folder)
    result=runner(workspace,['/usr/bin/python3','-c','import os;print(os.getuid())'],timeout_seconds=10)
    assert result['exit']==0 and result['output'].strip()==str(os.getuid()) and result['managed_processes_stopped']
    marker=workspace/'detached.pid'
    code='import os,time;from pathlib import Path;p=os.fork();\nif p==0:\n os.setsid();Path('+repr(str(marker))+').write_text(str(os.getpid()));time.sleep(60)\nelse:time.sleep(60)'
    try:runner(workspace,['/usr/bin/python3','-c',code],timeout_seconds=10,canceled=lambda:marker.exists())
    except ToolError as e:assert str(e)=='canceled_effects_unverified',str(e)
    else:raise AssertionError('Active Stop did not report uncertain effects')
    assert marker.exists();pid=int(marker.read_text())
    until=time.monotonic()+5
    while Path('/proc',str(pid)).exists() and time.monotonic()<until:time.sleep(.05)
    assert not Path('/proc',str(pid)).exists(),'Detached descendant remained after scope Stop'
print(json.dumps({'host_only':True,'uid':os.getuid(),'process_exit_and_output':True,
                  'actual_detached_descendant_stop':True,'arbitrary_side_effects_verified':False}))
