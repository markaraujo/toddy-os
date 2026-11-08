#!/usr/bin/env python3
"""Reuse official frozen Rust seeds privately for source metadata, never install."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tarfile

ROOT=Path(__file__).resolve().parents[2]


def digest(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def main():
    root=ROOT/'.local/phase2/cargo-prefetch-tools-1'
    rows=json.loads((ROOT/'config/phase2/sources.lock.json').read_text())['components']
    selected=[next(r for r in rows if r['name']==name) for name in ['cargo-stage0','rustc-stage0']]
    for row in selected:
        assert row['version']=='1.96.0' and digest(ROOT/'.local/sources'/row['filename'])==row['sha256']
    if root.exists():
        assert root.is_dir() and not root.is_symlink() and (root/'proof.json').is_file(),'Reconcile partial tool preparation; no replay'
        proof=json.loads((root/'proof.json').read_text())
        assert proof['archives']==[{'filename':r['filename'],'sha256':r['sha256']} for r in selected]
        for name,row in proof['versions'].items():
            path=ROOT/row['path'];assert path.resolve().is_relative_to(root.resolve()) and not path.is_symlink()
            assert digest(path)==row['binary_sha256']
            assert subprocess.check_output([str(path),'--version'],text=True).strip()==row['stdout']
        print('Verified/reused exact private source-fetch tools; no host/global install or product compiler change')
        return
    assert shutil.disk_usage(ROOT).free>=100*1024**3
    root.mkdir()
    proof={'scope':'Private source-vendoring tools only, reused authenticated Rust bootstrap cache; no host/global install and no product compiler change',
           'archives':[],'versions':{}}
    for row in selected:
        path=ROOT/'.local/sources'/row['filename']
        with tarfile.open(path) as archive:archive.extractall(root,filter='data')
        proof['archives'].append({'filename':path.name,'sha256':row['sha256']})
    for name in ['cargo','rustc']:
        matches=list(root.glob(name+'-1.96.0-*/'+name+'/bin/'+name));assert len(matches)==1
        path=matches[0];result=subprocess.run([str(path),'--version'],text=True,capture_output=True,check=True)
        assert result.stdout.startswith(name+' 1.96.0 ')
        proof['versions'][name]={'path':str(path.relative_to(ROOT)),'stdout':result.stdout.strip(),
                                 'exit':result.returncode,'binary_sha256':digest(path)}
    (root/'proof.json').write_text(json.dumps(proof,indent=2)+'\n')
    print(json.dumps(proof))


if __name__=='__main__':main()
