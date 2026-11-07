#!/usr/bin/env python3
"""Start, inspect or resume an isolated native kernel compilation experiment."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from vm import ssh_args

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('start', 'collect', 'resume'))
    parser.add_argument('fixture', nargs='?')
    args = parser.parse_args()
    files = {}
    if args.action == 'start':
        if args.fixture:
            parser.error('Start creates a fresh fixture')
        for name, path in {
            'kernel_native_probe.py': 'scripts/build/h09/kernel_native_probe.py',
            'check_kernel_config.py': 'scripts/build/h09/check_kernel_config.py',
            'requested.config': 'config/kernel.config.fragment',
        }.items():
            files[name] = base64.b64encode((ROOT / path).read_bytes()).decode()
    elif (not args.fixture or Path(args.fixture).parent != Path('/mnt/lfs/sources/recovery')
          or not Path(args.fixture).name.startswith('kernel-native-')):
        parser.error('Exact private fixture path required')
    script = 'ACTION, FIXTURE, FILES = ' + repr((args.action, args.fixture, files)) + '\n' + r'''
import base64,fcntl,hashlib,json,os,subprocess,tempfile
from pathlib import Path
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
parent=Path('/mnt/lfs/sources/recovery')
assert parent.resolve()==parent and parent.stat().st_uid==0
def refuse_live_children(base):
 # A driver can disappear while its detached make process continues. Never
 # resume over that process or infer that a missing supervisor ended the build.
 for record in (base/'attempts').glob('*/*.pid.json'):
  if record.with_name(record.name.replace('.pid.json','.exit.json')).exists():continue
  pid=json.loads(record.read_text())['pid'];proc=Path('/proc')/str(pid)
  if proc.exists() and (proc/'stat').read_text().rsplit(')',1)[1].split()[0]!='Z':
   raise ValueError('Unfinished kernel stage process still exists: '+str(pid))
if ACTION=='start':
 # Refuse duplicate work while any earlier fixture is live.
 for old in parent.glob('kernel-native-*'):
  refuse_live_children(old)
  if (old/'driver.pid').exists():
   proc=Path('/proc')/(old/'driver.pid').read_text().strip()
   if proc.exists() and (proc/'stat').read_text().rsplit(')',1)[1].split()[0]!='Z':
    assert str(old/'kernel_native_probe.py').encode() not in (proc/'cmdline').read_bytes(),'Kernel experiment already running'
 base=Path(tempfile.mkdtemp(prefix='kernel-native-',dir=parent))
 hashes={}
 for name,encoded in FILES.items():
  (base/name).write_bytes(base64.b64decode(encoded));hashes[name]=sha(base/name)
 (base/'inputs.json').write_text(json.dumps({'files':hashes,'native_status_sha256':sha(Path('/mnt/lfs/var/lib/dpkg/status'))},indent=2)+'\n')
else:
 base=Path(FIXTURE)
 assert base.resolve()==base and base.parent==parent and base.stat().st_uid==0 and not base.stat().st_mode&0o077
if ACTION in ('start','resume'):
 lock=(base/'lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 refuse_live_children(base)
 assert not (base/'result.json').exists(),'Already complete'
 # Keep a unique launcher log for every attempt. Driver acquires its own lock.
 with tempfile.NamedTemporaryFile(prefix='driver-',suffix='.log',dir=base,delete=False) as log:
  fcntl.flock(lock,fcntl.LOCK_UN)
  process=subprocess.Popen(['python3','-B',str(base/'kernel_native_probe.py')],stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
 (base/'driver.pid').write_text(str(process.pid)+'\n')
 print(json.dumps({'fixture':str(base),'pid':process.pid,'inputs_sha256':sha(base/'inputs.json')}))
else:
 pid=int((base/'driver.pid').read_text());proc=Path('/proc')/str(pid)
 live=proc.exists() and (proc/'stat').read_text().rsplit(')',1)[1].split()[0]!='Z'
 if live:assert str(base/'kernel_native_probe.py').encode() in (proc/'cmdline').read_bytes()
 paths=list(base.glob('*.json'))+list((base/'completed').glob('*.json'))+list((base/'attempts').glob('*/*.json'))
 records={str(p.relative_to(base)):json.loads(p.read_text()) for p in sorted(paths)}
 logs={str(p.relative_to(base)):{'size':p.stat().st_size,'tail':p.read_text(errors='replace').splitlines()[-8:]} for p in sorted((base/'attempts').glob('*/*.log'))}
 logs.update({p.name:{'size':p.stat().st_size,'tail':p.read_text(errors='replace').splitlines()[-8:]} for p in sorted(base.glob('driver-*.log'))})
 print(json.dumps({'fixture':str(base),'pid':pid,'live':live,'records':records,'logs':logs},indent=2))
'''
    run = subprocess.run(ssh_args() + ['python3 -B -'], input=script, text=True,
                         capture_output=True, timeout=60)
    if run.returncode:
        print(run.stdout + run.stderr)
        raise SystemExit(run.returncode)
    report = json.loads(run.stdout)
    raw = run.stdout.encode()
    sha = hashlib.sha256(raw).hexdigest()
    path = ROOT / '.local/logs' / ('h09-private-kernel-' + args.action + '-' + sha + '.json')
    path.parent.mkdir(exist_ok=True, parents=True)
    path.write_bytes(raw)
    print(json.dumps({'report': str(path), 'sha256': sha,
                     **{key: report[key] for key in ('fixture', 'pid', 'live') if key in report}}))
    if args.action == 'collect':
        for name, row in report['logs'].items():
            print(name, row['size'], '\n' + '\n'.join(row['tail']))
        print('Completed stages:', ', '.join(name for name in report['records'] if name.startswith('completed/')))
        if 'result.json' in report['records']:
            print(json.dumps(report['records']['result.json'], indent=2))


if __name__ == '__main__':
    main()
