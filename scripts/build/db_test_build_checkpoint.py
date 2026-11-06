#!/usr/bin/env python3
"""Capture/verify a local native DB test-build recovery checkpoint, not success."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

SOURCE=Path('/mnt/lfs/sources/db-5.3.28')
SEED=Path('/var/log/toddy/build/h07-berkeley-db.recovery-seed.json')
RECOVERY_SEED_SHA256='75d8c0e77db2c0b42af7de2ff813e908ee4f2d5cc470dcb62bb5082013937e63'

def digest(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('action',choices=['capture','verify']);args=parser.parse_args()
    subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
    if args.action=='capture':
        failed=Path('/var/log/toddy/build/h07-berkeley-db.failed.json');record=json.loads(failed.read_text())
        if record['changed_paths']!=0 or record['postcheck_exit'] is not None or record['recipe_exit']!=-15:
            raise SystemExit('Expected diagnosed zero-install interrupted test attempt')
        if SEED.exists():raise SystemExit('Preserve existing recovery seed')
        paths=[SOURCE/'build-test'/name for name in ['Makefile','config.status','db_config.h','cutest','include.tcl']]
        paths += [p for p in (SOURCE/'build-test/.libs').iterdir() if p.is_file() and (p.stat().st_mode & 0o111 or '.so' in p.name)]
        paths += [p for p in (SOURCE/'src').rglob('*') if p.is_file()]
        paths += [SOURCE/'dist/configure',SOURCE/'dist/config.hin']
        if any(not p.is_file() or not p.resolve().is_relative_to(SOURCE) for p in paths):raise SystemExit('Invalid cached DB build input')
        data={'scope':'Local recovery of compiled test-only build; no DB package or full suite acceptance',
              'failed_record_sha256':digest(failed),'files':{str(p.relative_to(SOURCE)):digest(p) for p in sorted(set(paths))}}
        with SEED.open('x') as stream:
            json.dump(data,stream,indent=2);stream.write('\n');stream.flush();os.fsync(stream.fileno())
        SEED.chmod(0o600)
    else:
        stat=SEED.lstat()
        if SEED.is_symlink() or stat.st_uid!=0 or stat.st_mode & 0o077 or digest(SEED)!=RECOVERY_SEED_SHA256:
            raise SystemExit('Recovery seed ownership, permissions or frozen digest changed')
        data=json.loads(SEED.read_text())
        for relative,sha in data['files'].items():
            path=SOURCE/relative
            if not path.resolve().is_relative_to(SOURCE) or digest(path)!=sha:raise SystemExit('Cached test build changed: '+relative)
    print(json.dumps({'action':args.action,'verified_files':len(data['files']),'seed_sha256':digest(SEED),'success_claimed':False}))
if __name__=='__main__':main()
