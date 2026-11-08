#!/usr/bin/env python3
"""Run one native local-tool job plus a real other-UID socket/key denial probe."""
import json
import re
from pathlib import Path
import subprocess
import sys
import time

import phase2_vm

ROOT = phase2_vm.ROOT
STATE = ROOT/'.local/phase2'
NAME = sys.argv[1] if len(sys.argv)>1 else 'local-tool-1'
assert re.fullmatch(r'local-tool-[1-9][0-9]*', NAME)

if __name__ == '__main__':
    # The guest job helper refuses an existing receipt, including uncertain jobs.
    command = ('python3 /opt/toddy-build/scripts/build/phase2/job.py '+NAME+
               ' /mnt/lfs/sources/phase2/inputs/local-model-proof'
               ' /mnt/lfs/sources/phase2/work/'+NAME+' python3 /src/runtime/local/tool_probe.py')
    with (STATE/(NAME+'-dispatch.log')).open('xb') as log:
        process = subprocess.Popen(phase2_vm.ssh_args()+[command], stdout=log, stderr=subprocess.STDOUT)
        try:
            deadline = time.monotonic()+125
            while True:
                ready = subprocess.run(phase2_vm.ssh_args()+[
                    'test -f /mnt/lfs/sources/phase2/work/'+NAME+'/peer-ready.json'], capture_output=True)
                if ready.returncode == 0:
                    break
                assert process.poll() is None and time.monotonic() < deadline, 'Inspect job/readiness; no replay'
                time.sleep(.25)
            remote = r'''
from pathlib import Path
import json,os,re,stat,subprocess
root=Path('/mnt/lfs/sources/phase2/work/local-tool-1')
component=json.loads((root/'peer-ready.json').read_text())['component']
assert re.fullmatch(r'local-[a-z0-9_]{8}',component)
directory=root/'run'/component
assert directory.resolve()==directory and directory.stat().st_uid==101
assert stat.S_IMODE(directory.stat().st_mode)==0o700
assert stat.S_ISSOCK((directory/'server.sock').lstat().st_mode)
code=''' + '"""' + r'''
import errno,json,os,socket,sys
key_errno=socket_errno=0
try:
    with open(sys.argv[1]+'/key','rb') as source:source.read(1)
except OSError as error:key_errno=error.errno
with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as client:
    try:client.connect(sys.argv[1]+'/server.sock')
    except OSError as error:socket_errno=error.errno
print(json.dumps({'uid':os.getuid(),'key_errno':key_errno,'socket_errno':socket_errno}))
''' + '"""' + r'''
result=subprocess.run(['setpriv','--reuid=65534','--regid=65534','--clear-groups',
    '--no-new-privs','--inh-caps=-all','--ambient-caps=-all','--bounding-set=-all',
    'python3','-c',code,str(directory)],capture_output=True,text=True,check=True)
report=json.loads(result.stdout)
assert report['uid']==65534
with (root/'peer-release').open('x') as output:json.dump(report,output)
print(json.dumps(report))
assert report['key_errno']==13 and report['socket_errno']==13
'''
            result = subprocess.run(phase2_vm.ssh_args()+['python3 -'], input=remote.replace('local-tool-1', NAME).encode(),
                                    capture_output=True, check=True)
            (STATE/(NAME+'-other-uid.json')).write_bytes(result.stdout)
        finally:
            code = process.wait(timeout=180)
            (STATE/(NAME+'-dispatch.exit')).write_text(str(code)+'\n')
        if code:
            raise SystemExit(code)
    collect = '''from pathlib import Path
import json,hashlib
p=Path('/var/log/toddy/phase2/local-tool-1')
assert p.with_suffix('.exit').read_text().strip()=='0'
d=json.loads(p.with_suffix('.log').read_text())
assert d['task']['actual_file_content_matched'] and d['task']['actual_tool_executions']==1
assert d['stop']['exit']==0 and not d['stop']['forced']
root=Path('/mnt/lfs/sources/phase2/inputs/local-model-proof')
files=['runtime/local/server.py','runtime/local/tool_probe.py','runtime/engine/provider.mjs',
       'runtime/engine/local-transport.mjs','runtime/engine/local-tool-spike.mjs',
       'runtime/engine/local-cancel-spike.mjs']
d['own_input_sha256']={name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in files}
d['native_job']='local-tool-1'
print(json.dumps(d,indent=2))
'''
    result = subprocess.run(phase2_vm.ssh_args()+['python3 -'], input=collect.replace('local-tool-1', NAME).encode(), capture_output=True, check=True)
    import hashlib
    report=json.loads(result.stdout)
    assert all(hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==sha for name,sha in report['own_input_sha256'].items()), 'Source changed since native proof; do not publish mismatched evidence'
    (ROOT/'docs/evidence/B03-native-local-tool.json').write_bytes(result.stdout)
    print(result.stdout.decode())
