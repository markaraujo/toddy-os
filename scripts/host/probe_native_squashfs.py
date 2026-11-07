#!/usr/bin/env python3
"""Start or collect a durable private source-built Squashfs experiment."""
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
    parser.add_argument('action', choices=('start', 'collect'))
    parser.add_argument('fixture', nargs='?')
    args = parser.parse_args()
    if args.action == 'start':
        if args.fixture:
            parser.error('Start always creates a fresh protected generation')
        lock = json.loads((ROOT / 'config/supplemental-sources.lock.json').read_text())
        row = next(row for row in lock['components'] if row['filename'] == 'squashfs-tools-4.7.5.tar.gz')
        archive = ROOT / '.local/sources' / row['filename']
        if lock['status'] != 'frozen_for_native_build' or hashlib.sha256(archive.read_bytes()).hexdigest() != row['sha256']:
            raise ValueError('Frozen Squashfs archive verification failed')
        files = {row['filename']: archive.read_bytes()}
        for name in ('squashfs_native_probe.py', 'squashfs-roundtrip.py'):
            files[name] = (ROOT / 'scripts/build/h10' / name).read_bytes()
        encoded = {name: base64.b64encode(body).decode() for name, body in files.items()}
        script = 'FILES=' + repr(encoded) + '\n' + r'''
import base64,hashlib,json,os,subprocess,tempfile
from pathlib import Path
subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
parent=Path('/mnt/lfs/sources/recovery')
assert parent.resolve()==parent and parent.stat().st_uid==0
base=Path(tempfile.mkdtemp(prefix='squashfs-native-',dir=parent))
hashes={}
for name,encoded in FILES.items():
 body=base64.b64decode(encoded);(base/name).write_bytes(body);hashes[name]=hashlib.sha256(body).hexdigest()
(base/'inputs.json').write_text(json.dumps({'files':hashes},indent=2)+'\n')
with (base/'driver.log').open('x') as output:
 process=subprocess.Popen(['python3','-B',str(base/'squashfs_native_probe.py')],stdin=subprocess.DEVNULL,stdout=output,stderr=subprocess.STDOUT,start_new_session=True)
(base/'driver.pid').write_text(str(process.pid)+'\n')
print(json.dumps({'fixture':str(base),'pid':process.pid,'input_sha256':hashlib.sha256((base/'inputs.json').read_bytes()).hexdigest()}))
'''
    else:
        if not args.fixture or not args.fixture.startswith('/mnt/lfs/sources/recovery/squashfs-native-') or Path(args.fixture).name != args.fixture.rsplit('/', 1)[1]:
            parser.error('Collect requires the exact printed private fixture path')
        script = 'FIXTURE=' + repr(args.fixture) + '\n' + r'''
import hashlib,json,os
from pathlib import Path
base=Path(FIXTURE)
assert base.resolve()==base and base.parent==Path('/mnt/lfs/sources/recovery')
pid=int((base/'driver.pid').read_text());proc=Path('/proc')/str(pid)
live=proc.exists() and (proc/'stat').read_text().rsplit(')',1)[1].split()[0]!='Z'
if live:assert str(base/'squashfs_native_probe.py') in (proc/'cmdline').read_bytes().decode()
files={name:path.read_text() for name in ['inputs.json','running.json','build.exit.json','version.exit.json','roundtrip.exit.json','result.json','driver.exit.json','driver.log','build.log','version.log','roundtrip.log'] if (path:=base/name).exists()}
print(json.dumps({'fixture':str(base),'pid':pid,'live':live,'files':files,'sha256':{name:hashlib.sha256(body.encode()).hexdigest() for name,body in files.items()}},indent=2))
'''
    run = subprocess.run(ssh_args() + ['python3 -B -'], input=script, text=True, capture_output=True, timeout=60)
    if run.returncode:
        print(run.stdout + run.stderr)
        raise SystemExit(run.returncode)
    report = json.loads(run.stdout)
    raw = run.stdout.encode()
    sha = hashlib.sha256(raw).hexdigest()
    path = ROOT / '.local/logs' / ('h10-native-squashfs-' + args.action + '-' + sha + '.json')
    path.write_bytes(raw)
    print(json.dumps({'report': str(path), 'sha256': sha, **{key: report[key] for key in ('fixture', 'pid', 'live') if key in report}}))
    if args.action == 'collect' and 'driver.exit.json' in report['files']:
        result = json.loads(report['files']['driver.exit.json'])
        print(json.dumps(json.loads(report['files']['result.json']), indent=2))
        sys.exit(result['exit'])


if __name__ == '__main__':
    main()
