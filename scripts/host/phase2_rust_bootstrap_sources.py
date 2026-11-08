#!/usr/bin/env python3
"""Cache only the x86_64 bootstrap artifacts authenticated by frozen Rust source."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tarfile

ROOT=Path(__file__).resolve().parents[2]
if __name__=='__main__':
    path=ROOT/'config/phase2/sources.lock.json';lock=json.loads(path.read_text())
    rust=next(r for r in lock['components'] if r['name']=='rustc')
    archive=ROOT/'.local/sources'/rust['filename']
    assert hashlib.sha256(archive.read_bytes()).hexdigest()==rust['sha256']
    with tarfile.open(archive,'r|xz') as source:
        for member in source:
            if member.name.endswith('/src/stage0'):
                metadata=source.extractfile(member).read();break
        else:raise ValueError('Frozen Rust stage0 manifest missing')
    values=dict(line.split('=',1) for line in metadata.decode().splitlines() if '=' in line and not line.startswith('#'))
    assert values['dist_server']=='https://static.rust-lang.org'
    version=values['compiler_version'];date=values['compiler_date']
    assert re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+',version) and re.fullmatch(r'\d{4}-\d{2}-\d{2}',date)
    for component in ['rustc','rust-std','cargo']:
        filename=f'{component}-{version}-x86_64-unknown-linux-gnu.tar.xz'
        key='dist/'+date+'/'+filename;expected=values[key]
        assert re.fullmatch('[a-f0-9]{64}',expected)
        url=values['dist_server']+'/'+key;destination=ROOT/'.local/sources'/filename
        part=destination.with_name(filename+'.part');assert not part.exists(),'Reconcile partial bootstrap download first'
        if not destination.exists():
            subprocess.run(['curl','--fail','--silent','--show-error','--location','--connect-timeout','15',
                            '--max-time','180','--output',str(part),url],check=True)
            assert hashlib.sha256(part.read_bytes()).hexdigest()==expected
            part.rename(destination)
        assert hashlib.sha256(destination.read_bytes()).hexdigest()==expected
        row={'name':component+'-stage0','version':version,'filename':filename,'url':url,'sha256':expected,
             'reference':'Rustc'+rust['version']+' authenticated src/stage0',
             'parent_source_sha256':rust['sha256'],'stage0_metadata_sha256':hashlib.sha256(metadata).hexdigest(),
             'compiler_git_commit_hash':values['compiler_git_commit_hash'],
             'scope':'x86_64 build bootstrap only; not final product compiler/runtime',
             'integrity':'Artifact SHA256 matched value inside frozen authenticated Rust source before any extraction/execution',
             'status':'source_verified'}
        previous=[r for r in lock['components'] if r['name']==row['name']]
        assert not previous or previous==[row],'Do not change frozen bootstrap silently'
        if not previous:lock['components'].append(row);path.write_text(json.dumps(lock,indent=2)+'\n')
        print(json.dumps({'name':row['name'],'version':version,'sha256':expected}),flush=True)
