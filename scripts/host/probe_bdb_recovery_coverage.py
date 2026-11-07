#!/usr/bin/env python3
"""Launch a bounded isolated native log-coverage experiment with durable evidence.

Copies only verified immutable inputs from the active corrected fixture. Does
not modify that fixture, install packages, accept run_std or run a duplicate suite.
"""
import argparse
import base64
import hashlib
import json
import subprocess
from pathlib import Path

from vm import ROOT, ssh_args


DRIVER = r'''
from pathlib import Path
import datetime, hashlib, json, os, subprocess, sys
base=Path(sys.argv[1])
def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()
def save(name,value):
    path=base/name
    with path.with_suffix('.part').open('w') as f:
        json.dump(value,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
    path.with_suffix('.part').chmod(0o600)
    path.with_suffix('.part').replace(path)
inputs=json.loads((base/'inputs.json').read_text())
record={'started':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'driver_pid':os.getpid(),'fixture':str(base),'suite_accepted':False,
        'package_accepted':False,'driver_sha256':sha(Path(__file__)),
        'input_sha256':sha(base/'inputs.json')}
def verify():
    for name,value in inputs['source_files'].items():
        p=base/'source'/name
        assert p.resolve().is_relative_to(base/'source') and sha(p)==value['sha256'],name
        assert (os.readlink(p) if p.is_symlink() else None)==value.get('symlink'),name
    for name,value in inputs['harness_sha256'].items():
        assert sha(base/name)==value,name
exitcode=1
save('running.json',record)
(base/'driver.pid').write_text(str(os.getpid())+'\n')
try:
    verify()
    command=['timeout','--kill-after=60','1800','bash',str(base/'isolate.sh'),str(base),'standard']
    record['command']=command
    process=subprocess.Popen(command)
    record['test_pid']=process.pid;save('running.json',record)
    record['test_exit']=process.wait()
    (base/'test.exit').write_text(str(record['test_exit'])+'\n')
    verify();record['inputs_unchanged']=True
    record['reports']={}
    for name in ('cutest.log','standard.log','isolation-standard.json','source/build-test/coverage-records.txt'):
        p=base/name
        if p.is_file():record['reports'][name]=sha(p)
    assert record['test_exit']==0,'Native diagnostic failed'
    assert (base/'standard.log').read_text().splitlines()[-1]=='Diagnostic native coverage cases completed; full suite and package remain unaccepted'
    assert not any(l.startswith('FAIL') for l in (base/'standard.log').read_text().splitlines())
    record['records']={line.split()[0]:int(line.split()[1]) for line in
                     (base/'source/build-test/coverage-records.txt').read_text().splitlines()}
    record['diagnostic_cases_passed']=True
    exitcode=0
except BaseException as error:
    record['error']=str(error)
finally:
    record['finished']=datetime.datetime.now(datetime.timezone.utc).isoformat()
    record['driver_exit']=exitcode
    save('result.json',record)
    (base/'driver.exit').write_text(str(exitcode)+'\n')
    (base/'running.json').unlink()
sys.exit(exitcode)
'''

PREPARE = r'''
import base64,datetime,hashlib,json,os,pathlib,shutil,subprocess,tempfile
P=pathlib.Path
root=P('/mnt/lfs');origin=root/'sources/recovery/db-standard-nfv62s4o'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
assert sha(origin/'inputs.json')=='336abd7ca1442e5102249da2f774b30326e06d268cd2b16b65fc81e8c333e6f9'
assert shutil.disk_usage(root).free>30*1024**3
for old in (root/'sources/recovery').glob('db-standard-coverage-*'):
    if (old/'running.json').exists():raise ValueError('Inspect existing diagnostic before another launch: '+str(old))
base=P(tempfile.mkdtemp(prefix='db-standard-coverage-',dir=root/'sources/recovery'));base.chmod(0o755)
source=base/'source';source.mkdir()
original=json.loads((origin/'inputs.json').read_text())
for name,entry in original['source_files'].items():
    old=origin/'source'/name;new=source/name
    assert old.resolve().is_relative_to(origin/'source') and sha(old)==entry['sha256'],name
    new.parent.mkdir(parents=True,exist_ok=True)
    if old.is_symlink():
        assert os.readlink(old)==entry['symlink'],name
        new.symlink_to(os.readlink(old))
    else:shutil.copy2(old,new)
for name in ('isolate.sh','isolation-probe.py'):
    shutil.copy2(origin/name,base/name)
for name in ('tmp','var-tmp','shm'):
    p=base/'runtime'/name;p.mkdir(parents=True);p.chmod(0o1777)
(base/'outer-namespaces.json').write_text(json.dumps({n:os.readlink('/proc/self/ns/'+n) for n in ('pid','ipc','net','mnt')}))
(source/'build-test/standard-regression.tcl').write_bytes(base64.b64decode(ENTRY))
(base/'driver.py').write_bytes(base64.b64decode(DRIVER))
subprocess.run(['chroot',str(root),'/usr/bin/chown','-R','tester:tester','/'+str(source.relative_to(root))],check=True)
files={}
for name in original['source_files']:
    p=source/name;row={'sha256':sha(p)}
    if p.is_symlink():row['symlink']=os.readlink(p)
    files[name]=row
assert sum(files[n]!=e for n,e in original['source_files'].items())==1
record={'created':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_files':files,
        'origin_input_sha256':sha(origin/'inputs.json'),'frozen_test_bodies_unchanged':True,
        'diagnostic_entry_only_change':True,'suite_accepted':False,
        'harness_sha256':{n:sha(base/n) for n in ('driver.py','isolate.sh','isolation-probe.py','outer-namespaces.json')}}
(base/'inputs.json').write_text(json.dumps(record,indent=2)+'\n');(base/'inputs.json').chmod(0o600)
with (base/'driver.log').open('xb') as log:
    process=subprocess.Popen(['python3','-B',str(base/'driver.py'),str(base)],
                             stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
print(json.dumps({'fixture':str(base),'driver_pid':process.pid,'input_sha256':sha(base/'inputs.json'),
                 'driver_sha256':sha(base/'driver.py'),'test_entry_sha256':sha(source/'build-test/standard-regression.tcl'),
                 'suite_accepted':False,'package_accepted':False},indent=2))
'''


COLLECT = r'''
from pathlib import Path
import hashlib,json
base=Path(FIXTURE)
assert base.resolve()==base and base.stat().st_uid==0
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
pid=int((base/'driver.pid').read_text())
proc=Path('/proc')/str(pid)
live=False
if proc.exists():
    command=(proc/'cmdline').read_bytes()
    live=bool(command) and (proc/'stat').read_text().rsplit(')',1)[1].split()[0]!='Z'
    if live:assert str(base/'driver.py').encode() in command.split(b'\0'),'PID identity changed'
if live:
    result={'live':True,'driver_pid':pid,'fixture':str(base),
            'tail':(base/'driver.log').read_text().splitlines()[-8:]}
else:
    assert not (base/'running.json').exists(),'Unfinished driver requires diagnosis'
    result=json.loads((base/'result.json').read_text())
    assert str(result['driver_exit'])==(base/'driver.exit').read_text().strip()
    assert str(result['test_exit'])==(base/'test.exit').read_text().strip()
    assert sha(base/'inputs.json')==result['input_sha256']
    for name,value in result['reports'].items():assert sha(base/name)==value,name
    inputs=json.loads((base/'inputs.json').read_text())
    for name,value in inputs['source_files'].items():
        p=base/'source'/name
        assert p.resolve().is_relative_to(base/'source') and sha(p)==value['sha256'],name
    result.update(live=False,result_sha256=sha(base/'result.json'),
                  terminal_reports_reverified=True)
print(json.dumps(result,indent=2))
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--collect', type=Path, help='Observe/verify an existing diagnostic; never launch another')
    args = parser.parse_args()
    if args.collect:
        if (args.collect.parent != Path('/mnt/lfs/sources/recovery')
                or not args.collect.name.startswith('db-standard-coverage-')):
            raise ValueError('Supply the exact printed private diagnostic fixture')
        script = 'FIXTURE=' + repr(str(args.collect)) + '\n' + COLLECT
    else:
        script = 'ENTRY=' + repr(base64.b64encode((ROOT / 'scripts/build/h07/berkeley-db-coverage.tcl').read_bytes()).decode())
        script += '\nDRIVER=' + repr(base64.b64encode(DRIVER.encode()).decode()) + '\n' + PREPARE
    run = subprocess.run(ssh_args() + ['python3 -B -'], input=script, text=True,
                         capture_output=True, timeout=180)
    raw = (run.stdout + run.stderr).encode()
    sha = hashlib.sha256(raw).hexdigest()
    kind = 'result' if args.collect else 'launch'
    path = ROOT / '.local/logs' / ('h07-db-coverage-' + kind + '-' + sha + '.json')
    path.write_bytes(raw)
    if run.returncode:
        raise RuntimeError('Preserve diagnostic launch failure: ' + str(path))
    print(json.dumps(json.loads(run.stdout), indent=2))
    print('EVIDENCE_SHA256 ' + sha)


if __name__ == '__main__':
    main()
