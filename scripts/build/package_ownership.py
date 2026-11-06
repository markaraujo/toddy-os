"""Normalize build-user ownership without changing intended privileged helpers."""
import json
import os
from pathlib import Path
import stat


def ownership_action(package,virtual,uid,gid,mode,build_uid,build_gid,exceptions):
    privileged=bool(mode&(stat.S_ISUID|stat.S_ISGID))
    normalize=uid==build_uid or gid==build_gid
    if privileged and normalize:
        raise ValueError('Build-owned privileged payload requires explicit diagnosis: '+virtual)
    expected=exceptions.get((package,virtual))
    if normalize:
        uid=0 if uid==build_uid else uid
        gid=0 if gid==build_gid else gid
    if expected:
        if (uid,gid,stat.S_IMODE(mode))!=(expected['uid'],expected['gid'],expected['mode']):
            raise ValueError('Privileged helper identity/mode differs from reviewed policy: '+virtual)
    elif privileged or uid!=0 or gid!=0:
        raise ValueError('Unreviewed payload privilege or ownership: '+virtual)
    return uid,gid,normalize


def normalize_ownership(root,target,stage,package):
    policy_path=root/'config/package-ownership-policy.json'
    policy=json.loads(policy_path.read_text())
    user=next(line.split(':') for line in (target/'etc/passwd').read_text().splitlines()
              if line.split(':')[0]==policy['build_user'])
    build_uid,build_gid=int(user[2]),int(user[3])
    if build_uid==0 or build_gid==0:raise ValueError('Invalid build-user identity')
    exceptions={(r['package'],r['path']):r for r in policy['privileged_exceptions']}
    planned=[]
    for base,dirs,files in os.walk(stage,followlinks=False):
        for name in dirs+files:
            path=Path(base)/name;virtual='/'+str(path.relative_to(stage));current=path.lstat()
            uid,gid,change=ownership_action(package,virtual,current.st_uid,current.st_gid,current.st_mode,
                                          build_uid,build_gid,exceptions)
            planned.append((path,uid,gid,change,current.st_mode))
    # Validate every entry before changing staged metadata.
    for path,uid,gid,change,mode in planned:
        if change:
            os.chown(path,uid,gid,follow_symlinks=False)
            if not path.is_symlink():os.chmod(path,stat.S_IMODE(mode))
    return [{'path':'/'+str(path.relative_to(stage)),'uid':uid,'gid':gid}
            for path,uid,gid,change,mode in planned if change]
