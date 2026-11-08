#!/usr/bin/env python3
"""One-shot sequential B01 prerequisite builds/transactions; no retry or replay."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import phase2_vm

ROOT = phase2_vm.ROOT
STATE = ROOT/'.local/phase2'
COMPONENTS = ['qtsvg', 'qttools-linguist', 'extra-cmake-modules', 'kcoreaddons', 'yaml-cpp']


def inputs():
    paths = [p for p in (ROOT/'scripts/build').rglob('*') if p.is_file()
             and p.suffix in {'.sh', '.py', '.c', '.cpp', '.tcl'}]
    paths += [ROOT/'config/phase2/sources.lock.json', ROOT/'config/component-licenses.json']
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


def remote(code):
    return subprocess.run(phase2_vm.ssh_args()+['python3 -'], input=code.encode(),
                          capture_output=True, check=True).stdout.decode()


def save(data):
    part = STATE/'installer-prereqs.json.part'
    part.write_text(json.dumps(data, indent=2)+'\n')
    part.replace(STATE/'installer-prereqs.json')
    runtime = json.loads((STATE/'runtime.json').read_text())
    runtime.update(slice='B01-Calamares-prerequisites', job=data,
                   next_action='Inspect installer-prereqs.json and actual guest job/transaction markers. Never replay an uncertain operation. Continue from the first verified missing prerequisite only.')
    part = STATE/'runtime.json.part'
    part.write_text(json.dumps(runtime, indent=2)+'\n')
    part.replace(STATE/'runtime.json')
    print(json.dumps(data), flush=True)


if __name__ == '__main__':
    with (STATE/'installer-prereqs.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        assert not (STATE/'installer-prereqs.json').exists(), 'Inspect prior controller; do not replay'
        pinned = inputs()
        preflight = '''from pathlib import Path
import json
root=Path('/var/log/toddy')
d=json.loads((root/'build/b01-qtbase-probe-package.success.json').read_text())
assert d['recipe_exit']==0 and d['postcheck_exit']==0
assert not list((root/'build').glob('*.running.json'))
'''
        for name in COMPONENTS:
            preflight += f"assert not (root/'phase2/{name}-1.job.json').exists()\n"
            preflight += f"assert not list((root/'build').glob('b01-{name}-install.*json'))\n"
        remote(preflight)
        data = {'controller_pid': os.getpid(), 'state': 'preflight passed', 'verified': [],
                'source_commit': subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()}
        save(data)
        try:
            for name in COMPONENTS:
                assert inputs() == pinned, 'Reviewed build inputs changed; no next dispatch'
                data.update(component=name, state='isolated compile active',
                            guest_prefix='/var/log/toddy/phase2/'+name+'-1')
                save(data)
                command = ('python3 /opt/toddy-build/scripts/build/phase2/job.py '+name+'-1 '
                           '/mnt/lfs/sources/phase2/inputs/'+name+' '
                           '/mnt/lfs/sources/phase2/work/'+name+'-1 bash /src/toddy-build.sh')
                with (STATE/(name+'-compile-dispatch.log')).open('xb') as log:
                    subprocess.run(phase2_vm.ssh_args()+[command], stdout=log, stderr=subprocess.STDOUT, check=True)
                remote(f"from pathlib import Path\nassert Path('/var/log/toddy/phase2/{name}-1.exit').read_text().strip()=='0'\n")
                assert inputs() == pinned, 'Build inputs changed; no native transaction'
                data.update(state='native package transaction active',
                            guest_prefix='/var/log/toddy/build/b01-'+name+'-install')
                save(data)
                command = ('cd /opt/toddy-build/scripts/build && python3 run_step.py b01-'+name+
                           '-install phase2/'+name+'-install.sh phase2/'+name+'-check.sh --user root')
                with (STATE/(name+'-install.log')).open('xb') as log:
                    subprocess.run(phase2_vm.ssh_args()+[command], stdout=log, stderr=subprocess.STDOUT, check=True)
                report = json.loads(remote(f"""from pathlib import Path
import json
d=json.loads(Path('/var/log/toddy/build/b01-{name}-install.success.json').read_text())
assert d['recipe_exit']==0 and d['postcheck_exit']==0
print(json.dumps({{k:d[k] for k in ['step','recipe_exit','postcheck_exit','changed_paths','log_sha256']}}))
"""))
                data['verified'].append(report)
                data.update(state='native package and affected consumer verified')
                save(data)
            data.update(state='all five prerequisites verified; Calamares no-write probe next')
            save(data)
        except Exception as error:
            data.update(state='stopped; reconcile actual guest postconditions before any continuation',
                        error_type=type(error).__name__)
            save(data)
            raise
