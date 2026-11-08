#!/usr/bin/env python3
"""Prepare authenticated cargo-c source, published lock and offline vendor input."""
import hashlib
import inspect
import io
import json
from pathlib import Path
import shlex
import subprocess
import zipfile

import phase2_vm
from phase2_rust_vendor import digest,verify_vendor
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'build/phase2'))
from public_vendor_readability import readable_vendor


def prepare_remote():
    from pathlib import Path
    import fcntl,hashlib,io,json,os,subprocess,sys,tarfile,tomllib,zipfile
    subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
    lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
    source=Path('/mnt/lfs/sources/phase2/inputs/cargo-c-tool-0.10.24')
    work=Path('/mnt/lfs/sources/phase2/work/cargo-c-1')
    assert not source.exists() and not work.exists(),'Reconcile existing input/work before any continuation'
    fs=os.statvfs('/mnt/lfs');assert fs.f_bavail*fs.f_frsize>=20*1024**3
    with zipfile.ZipFile(io.BytesIO(sys.stdin.buffer.read())) as outer:
        config_bytes=outer.read('toddy-crates.json');config=json.loads(config_bytes)
        assert Path('/opt/toddy-build/config/phase2/rust-crates.lock.json').read_bytes()==config_bytes
        parent=next(p for p in config['parents'] if p['name']=='cargo-c');assert parent['version']=='0.10.24'
        rows=json.loads(outer.read('toddy-sources.json'))
        frozen=json.loads(Path('/opt/toddy-build/config/phase2/sources.lock.json').read_text())['components']
        assert len(rows)==3 and all(r in frozen for r in rows)
        assert {r['name'] for r in rows}=={'cargo-c','cargo-c-vendor','cargo-c-published-source'}
        assert set(outer.namelist())=={r['filename'] for r in rows}|{'toddy-crates.json','toddy-sources.json','toddy-build.py','toddy-probe.py'}
        for row in rows:
            name=row['filename'];assert Path(name).name==name
            data=outer.read(name);assert hashlib.sha256(data).hexdigest()==row['sha256']
            path=Path('/mnt/lfs/sources')/name;part=path.with_name(name+'.part');assert not part.exists()
            if path.exists():assert digest(path)==row['sha256']
            else:
                with part.open('xb') as output:output.write(data);output.flush();os.fsync(output.fileno())
                part.replace(path)
        primary=next(r for r in rows if r['name']=='cargo-c')
        vendor=next(r for r in rows if r['name']=='cargo-c-vendor')
        published=next(r for r in rows if r['name']=='cargo-c-published-source')
        assert parent['primary_source_sha256']==primary['sha256'] and parent['artifact']['sha256']==vendor['sha256']
        source.mkdir()
        for row in [primary,vendor]:
            subprocess.run(['python3','/opt/toddy-build/scripts/build/source.py',row['filename']],cwd=source,check=True)
        project=source/'cargo-c-0.10.24';assert project.is_dir() and not project.is_symlink()
        project.rename(source/'project');project=source/'project'
        assert not (project/'Cargo.lock').exists()
        with tarfile.open(Path('/mnt/lfs/sources')/published['filename']) as release:
            locks=[m for m in release.getmembers() if len(Path(m.name).parts)==2 and m.name.endswith('/Cargo.lock')]
            assert len(locks)==1;body=release.extractfile(locks[0]).read()
        assert hashlib.sha256(body).hexdigest()==published['cargo_lock_sha256']==parent['cargo_lock_sha256']
        (project/'Cargo.lock').write_bytes(body)
        assert verify_vendor(source/'vendor',parent['packages'])==parent['packages']
        readability=readable_vendor(source/'vendor')
        assert verify_vendor(source/'vendor',parent['packages'])==parent['packages']
        for name in ['toddy-crates.json','toddy-sources.json','toddy-build.py','toddy-probe.py']:
            (source/name).write_bytes(outer.read(name))
    config_text='[source.crates-io]\nreplace-with="toddy-vendor"\n[source.toddy-vendor]\ndirectory="/src/vendor"\n[net]\noffline=true\n'
    (source/'toddy-cargo.toml').write_text(config_text)
    fs=os.statvfs('/mnt/lfs');assert fs.f_bavail*fs.f_frsize>=20*1024**3
    receipt={'scope':'Authenticated immutable cargo-c source/published same-commit lock/vendor input only, not compilation/install',
             'sources':rows,'cargo_lock_sha256':parent['cargo_lock_sha256'],'registry_crates':len(parent['packages']),
             'recipe_sha256':digest(source/'toddy-build.py'),'probe_sha256':digest(source/'toddy-probe.py'),
             'cargo_config_sha256':digest(source/'toddy-cargo.toml'),'public_vendor_readability':readability,'free_bytes_before_build':fs.f_bavail*fs.f_frsize}
    (source/'toddy-prepared.json').write_text(json.dumps(receipt,indent=2)+chr(10))
    work.mkdir();os.chown(work,101,101);print(json.dumps(receipt))


def main():
    root=phase2_vm.ROOT;config_path=root/'config/phase2/rust-crates.lock.json'
    config=json.loads(config_path.read_text());parent=next(p for p in config['parents'] if p['name']=='cargo-c')
    assert parent['vendor_exit']==0 and len(parent['packages'])==418
    frozen=json.loads((root/'config/phase2/sources.lock.json').read_text())['components']
    rows=[next(r for r in frozen if r['name']==name) for name in ['cargo-c','cargo-c-vendor','cargo-c-published-source']]
    payload=io.BytesIO()
    with zipfile.ZipFile(payload,'w',compression=zipfile.ZIP_STORED) as outer:
        for row in rows:
            path=root/'.local/sources'/row['filename'];assert digest(path)==row['sha256']
            outer.writestr(row['filename'],path.read_bytes())
        outer.writestr('toddy-crates.json',config_path.read_bytes());outer.writestr('toddy-sources.json',json.dumps(rows).encode())
        for name,filename in [('toddy-build.py','cargo_c_build.py'),('toddy-probe.py','cargo_c_probe.py')]:
            body=(root/'scripts/build/phase2'/filename).read_bytes();compile(body,filename,'exec');outer.writestr(name,body)
    remote='from pathlib import Path\nimport hashlib,json,tomllib,os,stat\n'+inspect.getsource(digest)+'\n'+inspect.getsource(verify_vendor)+'\n'+inspect.getsource(readable_vendor)+'\n'+inspect.getsource(prepare_remote)+'\nprepare_remote()\n'
    compile(remote,'cargo-c-source-preparation','exec')
    prefix=root/'.local/phase2/cargo-c-input'
    with prefix.with_suffix('.log').open('xb') as output:
        result=subprocess.run(phase2_vm.ssh_args()+['python3 -c '+shlex.quote(remote)],input=payload.getvalue(),stdout=output,stderr=subprocess.STDOUT)
    prefix.with_suffix('.exit').write_text(str(result.returncode)+'\n');raise SystemExit(result.returncode)


if __name__=='__main__':main()
