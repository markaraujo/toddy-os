#!/usr/bin/env python3
"""Partition own staged CPython QA data without altering runtime code or tests."""
from pathlib import Path
import hashlib
import json
import shutil

QA_ROOTS=('/usr/lib/python3.14/test','/usr/lib/python3.14/idlelib/idle_test','/usr/lib/python3.14/tkinter/test')


def manifest(root):
    result={}
    for path in root.rglob('*'):
        relative='/'+str(path.relative_to(root));info=path.lstat()
        entry={'mode':info.st_mode,'uid':info.st_uid,'gid':info.st_gid,'mtime_ns':info.st_mtime_ns}
        if path.is_symlink():entry['link']=path.readlink().as_posix()
        elif path.is_file():
            with path.open('rb') as stream:entry['sha256']=hashlib.file_digest(stream,'sha256').hexdigest()
        elif not path.is_dir():raise ValueError('Unexpected staged node: '+relative)
        result[relative]=entry
    return result


def partition(runtime,qa):
    runtime=Path(runtime);qa=Path(qa)
    if runtime.is_symlink() or not runtime.is_dir():raise ValueError('Runtime staging must be a real directory')
    if qa.exists() or qa.is_symlink():raise ValueError('Preserve existing QA staging before retry')
    runtime=runtime.resolve();qa=qa.resolve()
    if qa.is_relative_to(runtime) or runtime.is_relative_to(qa):raise ValueError('Runtime and QA staging must be disjoint')
    roots=[]
    for virtual in QA_ROOTS:
        source=runtime/virtual.lstrip('/')
        if not source.exists() and not source.is_symlink():continue
        if source.is_symlink() or not source.is_dir() or not source.resolve().is_relative_to(runtime):
            raise ValueError('Redirected QA source tree: '+virtual)
        info=source.stat()
        roots.append((virtual,source,manifest(source),(info.st_mode,info.st_uid,info.st_gid,info.st_mtime_ns)))
    if not roots or roots[0][0]!=QA_ROOTS[0]:raise ValueError('Expected frozen CPython regression tree is absent')
    # Validate every source/root before moving; failures preserve all bytes and
    # the original archive remains the caller's recovery ingredient.
    qa.mkdir(mode=0o700)
    for virtual,source,expected,root_info in roots:
        destination=qa/virtual.lstrip('/');destination.parent.mkdir(parents=True,exist_ok=True)
        shutil.move(source,destination)
        if manifest(destination)!=expected:raise ValueError('QA staging metadata/content changed during move')
        info=destination.stat()
        if (info.st_mode,info.st_uid,info.st_gid,info.st_mtime_ns)!=root_info:
            raise ValueError('QA root directory metadata changed during move')
    return {'roots':[r[0] for r in roots],
            'regular_files':sum(sum('sha256' in e for e in r[2].values()) for r in roots),
            'entries':sum(len(r[2])+1 for r in roots),'runtime_code_changed':False,
            'tests_modified':False,'native_package_transfer_validated':False}


if __name__=='__main__':
    import subprocess
    subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
    states={r['id']:r['status'] for r in json.loads(Path('/opt/toddy-build/status.json').read_text())['milestones']}
    if states['H10']!='completed' or states['H11']!='in_progress':
        raise SystemExit('Release QA partition requires H10 completed and H11 in_progress')
    runtime=Path('/mnt/lfs/sources/stage/h11-python-runtime')
    qa=Path('/mnt/lfs/sources/stage/h11-python-tests')
    if runtime.resolve()!=runtime or qa.resolve()!=qa:
        raise SystemExit('Release QA staging parents must not redirect')
    print(json.dumps(partition(runtime,qa)))
