#!/usr/bin/env python3
"""Start/collect a private native production staging and source-preservation test."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import subprocess

from vm import ROOT, ssh_args

REMOTE = r'''
import base64,fcntl,hashlib,json,os,pathlib,subprocess,tempfile
P=pathlib.Path
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
parent=P('/mnt/lfs/sources/recovery')
assert parent.resolve()==parent and parent.stat().st_uid==0
lock=open('/var/log/toddy/build/db-production-probe.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
def alive(pid):
 proc=P('/proc')/str(pid)
 return proc.exists() and (proc/'stat').read_text().rsplit(')',1)[1].split()[0]!='Z'
if ACTION=='start':
 for old in parent.glob('db-production-*'):
  if (old/'driver.pid').exists() and alive(int((old/'driver.pid').read_text())):
   raise ValueError('Production probe driver still live')
  for record in old.glob('*.pid.json'):
   if not record.with_name(record.name.replace('.pid.json','.exit.json')).exists() and alive(json.loads(record.read_text())['pid']):
    raise ValueError('Production probe child still live')
 assert not P('/mnt/lfs/sources/stage/berkeley-db').exists()
 assert os.statvfs(parent).f_bavail*os.statvfs(parent).f_frsize>40*1024**3
 native=parent/'db-native-m3pjqwd2';source=native/'db-5.3.28'
 assert sha(native/'native-build.json')=='79bad3e947ece611149dac738c6cf0e0bca3addccbc7e92453923ad04ed416f5'
 provenance=json.loads((native/'native-build.json').read_text())
 for name,row in provenance['source_inputs'].items():assert sha(source/name)==row['sha256'],name
 base=P(tempfile.mkdtemp(prefix='db-production-',dir=parent))
 for name,data in FILES.items():(base/name).write_bytes(base64.b64decode(data))
 (base/'build-production').mkdir(mode=0o700);(base/'stage').mkdir(mode=0o700)
 (base/'inputs.json').write_text(json.dumps({'source':str(source),
  'native_status_sha256':sha(P('/mnt/lfs/var/lib/dpkg/status')),
  'native_build_sha256':sha(native/'native-build.json'),
  'files':{name:sha(base/name) for name in FILES}},indent=2)+'\n')
 (base/'inputs.json').chmod(0o600)
 with (base/'driver.log').open('xb') as log:
  process=subprocess.Popen(['python3','-B',str(base/'db_private_production.py')],
   stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
 (base/'driver.pid').write_text(str(process.pid)+'\n')
 print(json.dumps({'fixture':str(base),'pid':process.pid,'inputs_sha256':sha(base/'inputs.json')}))
else:
 base=P(FIXTURE)
 assert base.resolve()==base and base.parent==parent and base.stat().st_uid==0 and not base.stat().st_mode&0o077
 pid=int((base/'driver.pid').read_text());live=alive(pid)
 if live:assert str(base/'db_private_production.py').encode() in (P('/proc')/str(pid)/'cmdline').read_bytes()
 paths=list(base.glob('*.exit.json'))+list(base.glob('*.intent.json'))
 if (base/'result.json').exists():paths.append(base/'result.json')
 records={p.name:json.loads(p.read_text()) for p in paths}
 print(json.dumps({'fixture':str(base),'pid':pid,'live':live,'records':records,
  'logs':{p.name:{'sha256':sha(p),'size':p.stat().st_size,'tail':p.read_text(errors='replace').splitlines()[-6:]} for p in base.glob('*.log')}},indent=2))
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('start', 'collect'))
    parser.add_argument('fixture', nargs='?')
    args = parser.parse_args()
    files = {}
    if args.action == 'start':
        if args.fixture:
            parser.error('Start creates its own generation')
        names = {name: 'scripts/build/h07/' + name for name in (
            'berkeley-db-production-view.sh', 'berkeley-db-production-inner.sh',
            'berkeley-db-private-production.sh', 'berkeley-db-check-inner.sh')}
        names.update({'db_private_production.py': 'scripts/build/db_private_production.py',
                      'readonly-check.sh': 'scripts/build/h07/berkeley-db-readonly-check.sh'})
        files = {name: base64.b64encode((ROOT / path).read_bytes()).decode() for name, path in names.items()}
    elif (not args.fixture or Path(args.fixture).parent != Path('/mnt/lfs/sources/recovery') or
          not Path(args.fixture).name.startswith('db-production-')):
        parser.error('Supply the exact private generation path')
    header = 'ACTION, FIXTURE, FILES = ' + repr((args.action, args.fixture, files)) + '\n'
    run = subprocess.run(ssh_args() + ['python3 -B -'], input=header + REMOTE,
                         capture_output=True, text=True, timeout=60)
    raw = (run.stdout + run.stderr).encode()
    sha = hashlib.sha256(raw).hexdigest()
    path = ROOT / '.local/logs' / ('h07-db-production-' + args.action + '-' + sha + '.json')
    path.write_bytes(raw)
    print(run.stdout + run.stderr)
    print('EVIDENCE_SHA256 ' + sha)
    if run.returncode:
        raise RuntimeError('Preserve production probe evidence: ' + str(path))


if __name__ == '__main__':
    main()
