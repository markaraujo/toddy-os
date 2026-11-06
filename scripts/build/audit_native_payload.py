#!/usr/bin/env python3
"""Verify installed payload SHA-256/link/mode ownership against native records."""
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import stat
import subprocess


def main():
    subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
    root=Path('/mnt/lfs');owners=defaultdict(set);findings=[];modified_conffiles=[];files=0
    rows=subprocess.check_output(['dpkg-query','--admindir='+str(root/'var/lib/dpkg'),'-W','-f=${Package}\t${Version}\t${Architecture}\t${Status}\n'],text=True)
    for row in rows.splitlines():
        name,version,arch,status=row.split('\t')
        if status!='install ok installed':continue
        record=json.loads((Path('/var/log/toddy/packages')/f'{name}_{version}_{arch}.json').read_text())
        conf=root/'var/lib/dpkg/info'/(name+'.conffiles')
        conffiles=set(conf.read_text().splitlines()) if conf.is_file() else set()
        for virtual,entry in record['payload'].items():
            if entry.get('directory'):continue
            owners[virtual].add(name);path=root/virtual.lstrip('/');files+=1
            if not path.exists() and not path.is_symlink():
                findings.append({'package':name,'path':virtual,'problem':'recorded payload missing'});continue
            problems=[]
            if 'symlink' in entry:
                if not path.is_symlink() or path.readlink().as_posix()!=entry['symlink']:problems.append('symlink target mismatch')
            elif entry.get('sha256'):
                if path.is_symlink() or not path.is_file():problems.append('regular file type mismatch')
                else:
                    with path.open('rb') as stream:actual=hashlib.file_digest(stream,'sha256').hexdigest()
                    if actual!=entry['sha256']:problems.append('file SHA-256 mismatch')
            current=path.lstat()
            if stat.S_IMODE(current.st_mode)!=stat.S_IMODE(entry['mode']):problems.append('mode mismatch')
            if (current.st_uid,current.st_gid)!=(entry['uid'],entry['gid']):problems.append('owner/group mismatch')
            if problems:
                result={'package':name,'path':virtual,'problems':problems}
                if virtual in conffiles:modified_conffiles.append(result)
                else:findings.append(result)
    duplicates=[{'path':p,'owners':sorted(names)} for p,names in sorted(owners.items()) if len(names)>1]
    print(json.dumps({'scope':'Installed native recorded regular/link payload; generated/unowned state separately audited','files':files,'findings':findings,'modified_conffiles':modified_conffiles,'duplicate_owners':duplicates},indent=2))

if __name__=='__main__':main()
