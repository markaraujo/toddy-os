#!/usr/bin/env python3
"""Start/collect a private native APT build against the measured production DB."""
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
lock=open('/var/log/toddy/build/apt-native-probe.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
def alive(pid):
 proc=P('/proc')/str(pid)
 return proc.exists() and (proc/'stat').read_text().rsplit(')',1)[1].split()[0]!='Z'
if ACTION=='start':
 for old in parent.glob('apt-native-*'):
  if (old/'driver.pid').exists() and alive(int((old/'driver.pid').read_text())):
   raise ValueError('Production probe driver still live')
  for record in old.glob('*.pid.json'):
   if not record.with_name(record.name.replace('.pid.json','.exit.json')).exists() and alive(json.loads(record.read_text())['pid']):
    raise ValueError('Production probe child still live')
 assert os.statvfs(parent).f_bavail*os.statvfs(parent).f_frsize>20*1024**3
 production=parent/'db-production-nlsr4aoj'
 assert sha(production/'result.json')=='3bb71fcb31431196a580900a30999b73689b9819cb26866f5d136b5aac82d5db'
 assert json.loads((production/'driver.exit.json').read_text())['exit']==0
 original=production/'stage/berkeley-db/usr'
 assert sha(original/'lib/libdb-5.3.so')=='945ad70683f03cd27630336ac003beba9c5c87e64e4251764c23231658bad42c'
 base=P(tempfile.mkdtemp(prefix='apt-native-',dir=parent));base.chmod(0o755)
 import shutil
 db=base/'berkeley/usr';shutil.copytree(original,db,symlinks=True)
 for path in [base/'berkeley',db,*db.rglob('*')]:
  if path.is_dir():path.chmod(0o755)
 db_files={str(p.relative_to(db)):sha(p) for p in db.rglob('*') if p.is_file()}
 for name,digest in db_files.items():assert sha(original/name)==digest
 for name,data in FILES.items():(base/name).write_bytes(base64.b64decode(data))
 (base/'inputs.json').write_text(json.dumps({'berkeley_prefix':str(db),
  'berkeley_files':db_files,'production_result_sha256':sha(production/'result.json'),
  'native_status_sha256':sha(P('/mnt/lfs/var/lib/dpkg/status')),
  'files':{name:sha(base/name) for name in FILES}},indent=2)+'\n')
 (base/'inputs.json').chmod(0o600)
 with (base/'driver.log').open('xb') as log:
  process=subprocess.Popen(['python3','-B',str(base/'apt_native_probe.py')],
   stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
 (base/'driver.pid').write_text(str(process.pid)+'\n')
 print(json.dumps({'fixture':str(base),'pid':process.pid,'inputs_sha256':sha(base/'inputs.json')}))
elif ACTION=='cache-check':
 base=P(FIXTURE)
 assert base.resolve()==base and base.parent==parent and base.stat().st_uid==0 and not base.stat().st_mode&0o022
 assert not alive(int((base/'driver.pid').read_text()))
 for name in ('source','configure','build','check'):
  row=json.loads((base/(name+'.exit.json')).read_text())
  assert row['exit']==0 and row['timed_out'] is False and sha(base/(name+'.log'))==row['log_sha256']
 script_bytes=base64.b64decode(FILES['apt-cache-check.py'])
 digest=hashlib.sha256(script_bytes).hexdigest()
 script=base/('consumer-'+digest+'.py')
 with script.open('xb') as stream:stream.write(script_bytes)
 work=P(tempfile.mkdtemp(prefix='toddy-apt-cache-',dir='/mnt/lfs/tmp'))
 uid=int(subprocess.check_output(['chroot','/mnt/lfs','id','-u','tester']))
 gid=int(subprocess.check_output(['chroot','/mnt/lfs','id','-g','tester']))
 os.chown(work,uid,gid)
 native='/'+str(base.relative_to('/mnt/lfs'))
 command=['chroot','/mnt/lfs','/usr/bin/env','-i','PATH=/usr/bin:/usr/sbin','LC_ALL=C','HOME=/tmp',
  '/usr/bin/su','tester','-c','python3 -B '+native+'/'+script.name+' --work /tmp/'+work.name+'/check --ftparchive '+native+'/apt-3.0.4/build/ftparchive/apt-ftparchive']
 log=base/('consumer-'+digest+'.log')
 with log.open('xb') as stream:
  result=subprocess.run(command,stdin=subprocess.DEVNULL,stdout=stream,stderr=subprocess.STDOUT,timeout=45)
 proof=work/'check/result.json'
 report={'fixture':str(base),'work':str(work),'exit':result.returncode,'command':command,
  'script_sha256':digest,'log_sha256':sha(log),'result_sha256':sha(proof) if proof.exists() else None,
  'result':json.loads(proof.read_text()) if proof.exists() else None,
  'log_tail':log.read_text().splitlines()[-8:]}
 (base/('consumer-'+digest+'.result.json')).write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(report,indent=2))
 assert result.returncode==0,'Actual consumer check failed; retained evidence'
else:
 base=P(FIXTURE)
 assert base.resolve()==base and base.parent==parent and base.stat().st_uid==0 and not base.stat().st_mode&0o022
 pid=int((base/'driver.pid').read_text());live=alive(pid)
 if live:assert str(base/'apt_native_probe.py').encode() in (P('/proc')/str(pid)/'cmdline').read_bytes()
 paths=list(base.glob('*.exit.json'))+list(base.glob('*.intent.json'))
 if (base/'result.json').exists():paths.append(base/'result.json')
 records={p.name:json.loads(p.read_text()) for p in paths}
 print(json.dumps({'fixture':str(base),'pid':pid,'live':live,'records':records,
  'logs':{p.name:{'sha256':sha(p),'size':p.stat().st_size,'tail':p.read_text(errors='replace').splitlines()[-6:]} for p in base.glob('*.log')}},indent=2))
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('start', 'collect', 'cache-check'))
    parser.add_argument('fixture', nargs='?')
    args = parser.parse_args()
    files = {}
    if args.action == 'start':
        if args.fixture:
            parser.error('Start creates its own generation')
        names = {'apt-inner.sh':'scripts/build/h07/apt-inner.sh',
                 'apt_native_probe.py':'scripts/build/apt_native_probe.py'}
        files = {name: base64.b64encode((ROOT / path).read_bytes()).decode() for name, path in names.items()}
    elif (not args.fixture or Path(args.fixture).parent != Path('/mnt/lfs/sources/recovery') or
          not Path(args.fixture).name.startswith('apt-native-')):
        parser.error('Supply the exact private generation path')
    if args.action == 'cache-check':
        files={'apt-cache-check.py':base64.b64encode((ROOT/'scripts/build/h07/apt-cache-check.py').read_bytes()).decode()}
    header = 'ACTION, FIXTURE, FILES = ' + repr((args.action, args.fixture, files)) + '\n'
    run = subprocess.run(ssh_args() + ['python3 -B -'], input=header + REMOTE,
                         capture_output=True, text=True, timeout=60)
    raw = (run.stdout + run.stderr).encode()
    sha = hashlib.sha256(raw).hexdigest()
    path = ROOT / '.local/logs' / ('h07-native-apt-' + args.action + '-' + sha + '.json')
    path.write_bytes(raw)
    print(run.stdout + run.stderr)
    print('EVIDENCE_SHA256 ' + sha)
    if run.returncode:
        raise RuntimeError('Preserve production probe evidence: ' + str(path))


if __name__ == '__main__':
    main()
