#!/usr/bin/env python3
"""Reconcile only reviewed build-owned directories after native metadata closure."""
import argparse
from collections import defaultdict
import json
import os
from pathlib import Path
import stat
import subprocess

from package_ownership import ownership_action

ROOT=Path('/mnt/lfs')
PROJECT=Path(__file__).resolve().parents[2]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply',action='store_true')
    args=parser.parse_args()
    subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
    if os.geteuid()!=0:raise ValueError('Disposable builder root required')
    policy=json.loads((PROJECT/'config/package-ownership-policy.json').read_text())
    user=next(line.split(':') for line in (ROOT/'etc/passwd').read_text().splitlines() if line.split(':')[0]==policy['build_user'])
    uid,gid=int(user[2]),int(user[3]);assert uid and gid
    exceptions={(r['package'],r['path']):r for r in policy['privileged_exceptions']}
    output=subprocess.check_output(['chroot',str(ROOT),'dpkg-query','-W','-f=${Package}\t${Version}\t${Architecture}\t${Status}\n'],text=True)
    owners=defaultdict(list)
    for line in output.splitlines():
        name,version,arch,status=line.split('\t')
        if status!='install ok installed' or '+toddy' not in version:
            raise ValueError('All package metadata must be complete before directory reconciliation')
        record=json.loads((Path('/var/log/toddy/packages')/f'{name}_{version}_{arch}.json').read_text())
        for virtual,row in record['payload'].items():
            if row.get('directory'):owners[virtual].append((name,row['uid'],row['gid']))
    changes=[]
    for virtual,entries in sorted(owners.items()):
        if not virtual.startswith('/') or '..' in Path(virtual).parts:raise ValueError('Unsafe recorded directory')
        identities={(u,g) for _,u,g in entries}
        if len(identities)!=1:raise ValueError('Conflicting recorded directory owners: '+virtual)
        wanted=next(iter(identities));path=ROOT/virtual.lstrip('/')
        info=path.lstat()
        if not stat.S_ISDIR(info.st_mode) or path.resolve()!=path:
            raise ValueError('Redirected or missing owned directory: '+virtual)
        if (info.st_uid,info.st_gid)==wanted:continue
        target_uid,target_gid,normalize=ownership_action(entries[0][0],virtual,info.st_uid,info.st_gid,info.st_mode,uid,gid,exceptions)
        if not normalize or (target_uid,target_gid)!=wanted:
            raise ValueError('Unreviewed directory identity difference: '+virtual)
        changes.append({'path':virtual,'before':[info.st_uid,info.st_gid],
                        'after':list(wanted),'mode':stat.S_IMODE(info.st_mode)})
    receipt=ROOT/'sources/evidence/h07-metadata-closure/directory-ownership.json'
    if changes and not args.apply:raise ValueError('Unreconciled build-owned directories: '+json.dumps(changes))
    if changes:
        if receipt.exists():raise ValueError('Preserve earlier reconciliation receipt before a changed retry')
        # Validate the complete set above before mutating any target directory.
        intent=receipt.with_suffix('.intent.json')
        with intent.open('x') as stream:
            json.dump({'complete':False,'changes':changes},stream,indent=2);stream.flush();os.fsync(stream.fileno())
        for row in changes:
            path=ROOT/row['path'].lstrip('/')
            os.chown(path,*row['after'],follow_symlinks=False)
            os.chmod(path,row['mode'])
            info=path.lstat();assert [info.st_uid,info.st_gid]==row['after']
        with receipt.open('x') as stream:
            json.dump({'complete':True,'changes':changes},stream,indent=2);stream.flush();os.fsync(stream.fileno())
    print(json.dumps({'owned_directories':len(owners),'normalized_directories':len(changes),
                      'unreviewed_changes':False,'passed':True}))


if __name__=='__main__':main()
