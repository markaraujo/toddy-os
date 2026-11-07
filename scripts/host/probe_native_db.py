#!/usr/bin/env python3
"""Start/collect/resume a durable private fresh DB test compilation, not run_std."""
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
startlock=open('/var/log/toddy/build/db-native-start.lock','a')
fcntl.flock(startlock,fcntl.LOCK_EX|fcntl.LOCK_NB)
def alive(pid):
 proc=P('/proc')/str(pid)
 return proc.exists() and (proc/'stat').read_text().rsplit(')',1)[1].split()[0]!='Z'
def refuse_live(base):
 if (base/'driver.pid').exists():
  pid=int((base/'driver.pid').read_text())
  if alive(pid):raise ValueError('Private DB driver is live: '+str(pid))
 for record in (base/'attempts').glob('*/*.pid.json'):
  if record.with_name(record.name.replace('.pid.json','.exit.json')).exists():continue
  pid=json.loads(record.read_text())['pid']
  if alive(pid):raise ValueError('Private DB child still exists: '+str(pid))
if ACTION=='start':
 for old in parent.glob('db-native-*'):refuse_live(old)
 assert os.statvfs(parent).f_bavail*os.statvfs(parent).f_frsize>40*1024**3
 base=P(tempfile.mkdtemp(prefix='db-native-',dir=parent))
 code=base/'code';code.mkdir()
 for name,encoded in FILES.items():
  path=code/name;path.parent.mkdir(parents=True,exist_ok=True)
  path.write_bytes(base64.b64decode(encoded))
 (base/'evidence').mkdir();(base/'archives').mkdir()
 for name,encoded in PATCHES.items():(base/'archives'/name).write_bytes(base64.b64decode(encoded))
 for name in ('db5.3_5.3.28+dfsg2.orig.tar.xz','db5.3_5.3.28+dfsg2-12.debian.tar.xz'):
  (base/'archives'/name).symlink_to(P('/mnt/lfs/sources')/name)
 context=base/'build-context-status'
 context.write_bytes(P('/mnt/lfs/var/lib/dpkg/status').read_bytes());context.chmod(0o600)
 (base/'inputs.json').write_text(json.dumps({'code_files':{name:sha(code/name) for name in FILES},
  'native_status_sha256':sha(context)},indent=2)+'\n')
 (base/'inputs.json').chmod(0o600)
else:
 base=P(FIXTURE)
 assert base.resolve()==base and base.parent==parent and base.stat().st_uid==0 and not base.stat().st_mode&0o077
if ACTION in ('start','resume'):
 refuse_live(base)
 lock=(base/'lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert not (base/'result.json').exists(),'Build complete; collect instead'
 with tempfile.NamedTemporaryFile(prefix='driver-',suffix='.log',dir=base,delete=False) as log:
  fcntl.flock(lock,fcntl.LOCK_UN)
  child=subprocess.Popen(['python3','-B',str(base/'code/scripts/build/db_native_compile.py'),str(base)],
   stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
 (base/'driver.pid').write_text(str(child.pid)+'\n')
 print(json.dumps({'fixture':str(base),'pid':child.pid,'inputs_sha256':sha(base/'inputs.json')}))
else:
 pid=int((base/'driver.pid').read_text());live=alive(pid)
 if live:assert str(base/'code/scripts/build/db_native_compile.py').encode() in (P('/proc')/str(pid)/'cmdline').read_bytes()
 paths=list((base/'completed').glob('*.json'))+list((base/'attempts').glob('*/*.json'))
 records={str(p.relative_to(base)):json.loads(p.read_text()) for p in sorted(paths)}
 for name in ('result.json',):
  if (base/name).exists():records[name]=json.loads((base/name).read_text())
 logs=list((base/'attempts').glob('*/*.log'))+list(base.glob('driver-*.log'))
 print(json.dumps({'fixture':str(base),'pid':pid,'live':live,'records':records,
  'logs':{str(p.relative_to(base)):{'size':p.stat().st_size,'tail':p.read_text(errors='replace').splitlines()[-8:]} for p in logs}},indent=2))
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('start', 'collect', 'resume'))
    parser.add_argument('fixture', nargs='?')
    args = parser.parse_args()
    files, patches = {}, {}
    if args.action == 'start':
        if args.fixture:
            parser.error('Start allocates a fresh private generation')
        names = ['scripts/build/' + n for n in (
            'db_native_compile.py', 'db_standard_prepare.py', 'verify_db_tcl_tests.py',
            'apply_db_test_fixture.py', 'locked_inputs.py', 'source_filter.py', 'target.sh', 'h06/common.sh')]
        names += ['scripts/build/h07/' + n for n in (
            'berkeley-db-inner.sh', 'berkeley-db-private-build.sh', 'berkeley-db-test-helper.sh',
            'db_repsite.c', 'berkeley-db-isolated-tests.sh', 'berkeley-db-isolation-probe.py',
            'berkeley-db-standard-regression.tcl', 'berkeley-db-isolated-driver.py')]
        names += ['config/' + n for n in (
            'sources.lock.json', 'security-overlay.lock.json', 'supplemental-sources.lock.json')]
        files = {n: base64.b64encode((ROOT / n).read_bytes()).decode() for n in names}
        for name in ('db-5.3.28-test142-environment-1.patch', 'db-5.3.28-repmgr007-async-diagnostic-1.patch'):
            patches[name] = base64.b64encode((ROOT / '.local/sources' / name).read_bytes()).decode()
    elif (not args.fixture or Path(args.fixture).parent != Path('/mnt/lfs/sources/recovery') or
          not Path(args.fixture).name.startswith('db-native-')):
        parser.error('Exact private DB build generation required')
    header = 'ACTION, FIXTURE, FILES, PATCHES = ' + repr((args.action, args.fixture, files, patches)) + '\n'
    run = subprocess.run(ssh_args() + ['python3 -B -'], input=header + REMOTE,
                         capture_output=True, text=True, timeout=60)
    raw = (run.stdout + run.stderr).encode()
    sha = hashlib.sha256(raw).hexdigest()
    path = ROOT / '.local/logs' / ('h07-native-db-' + args.action + '-' + sha + '.log')
    path.write_bytes(raw)
    print(run.stdout + run.stderr)
    print('EVIDENCE_SHA256 ' + sha)
    if run.returncode:
        raise RuntimeError('Preserve private DB build observation: ' + str(path))


if __name__ == '__main__':
    main()
