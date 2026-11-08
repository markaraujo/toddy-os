#!/usr/bin/env python3
"""Authenticate the frozen SVG renderer and offline crates before native build."""
import inspect
import io
import json
from pathlib import Path
import shlex
import subprocess
import sys
import zipfile

import phase2_vm
from phase2_rust_vendor import digest, verify_vendor
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'build/phase2'))
from public_vendor_readability import readable_vendor


def prepare_remote():
    import fcntl,hashlib,io,json,os,subprocess,sys,zipfile
    from pathlib import Path
    subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
    lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
    source=Path('/mnt/lfs/sources/phase2/inputs/librsvg-2.62.3')
    work=Path('/mnt/lfs/sources/phase2/work/librsvg-1')
    assert not source.exists() and not work.exists(),'Reconcile existing source/work; no replay'
    fs=os.statvfs('/mnt/lfs');assert fs.f_bavail*fs.f_frsize>=18*1024**3
    with zipfile.ZipFile(io.BytesIO(sys.stdin.buffer.read())) as outer:
        config_bytes=outer.read('toddy-crates.json');config=json.loads(config_bytes)
        assert Path('/opt/toddy-build/config/phase2/rust-crates.lock.json').read_bytes()==config_bytes
        parent=next(p for p in config['parents'] if p['name']=='librsvg')
        assert parent['version']=='2.62.3' and len(parent['packages'])==352
        rows=json.loads(outer.read('toddy-sources.json'))
        frozen=json.loads(Path('/opt/toddy-build/config/phase2/sources.lock.json').read_text())['components']
        assert len(rows)==2 and all(r in frozen for r in rows)
        assert {r['name'] for r in rows}=={'librsvg','librsvg-vendor'}
        assert set(outer.namelist())=={r['filename'] for r in rows}|{'toddy-crates.json','toddy-sources.json','toddy-build.py','toddy-probe.c'}
        for row in rows:
            name=row['filename'];assert Path(name).name==name
            data=outer.read(name);assert hashlib.sha256(data).hexdigest()==row['sha256']
            path=Path('/mnt/lfs/sources')/name;part=path.with_name(name+'.part');assert not part.exists()
            if path.exists():assert digest(path)==row['sha256']
            else:
                with part.open('xb') as output:output.write(data);output.flush();os.fsync(output.fileno())
                part.replace(path)
        source.mkdir()
        for row in rows:
            subprocess.run(['python3','/opt/toddy-build/scripts/build/source.py',row['filename']],cwd=source,check=True)
        (source/'librsvg-2.62.3').rename(source/'project')
        assert digest(source/'project/Cargo.lock')==parent['cargo_lock_sha256']
        assert verify_vendor(source/'vendor',parent['packages'])==parent['packages']
        readability=readable_vendor(source/'vendor')
        assert verify_vendor(source/'vendor',parent['packages'])==parent['packages']
        for name in ['toddy-crates.json','toddy-sources.json','toddy-build.py','toddy-probe.c']:
            (source/name).write_bytes(outer.read(name))
    text='[source.crates-io]\nreplace-with="toddy-vendor"\n[source.toddy-vendor]\ndirectory="/src/vendor"\n[net]\noffline=true\n'
    (source/'toddy-cargo.toml').write_text(text)
    fs=os.statvfs('/mnt/lfs');assert fs.f_bavail*fs.f_frsize>=18*1024**3
    receipt={'scope':'Frozen native SVG source/offline vendor input, no build acceptance','sources':rows,
             'cargo_lock_sha256':parent['cargo_lock_sha256'],'registry_crates':len(parent['packages']),
             'recipe_sha256':digest(source/'toddy-build.py'),'probe_sha256':digest(source/'toddy-probe.c'),
             'cargo_config_sha256':digest(source/'toddy-cargo.toml'),'public_vendor_readability':readability,
             'free_bytes_before_build':fs.f_bavail*fs.f_frsize}
    (source/'toddy-prepared.json').write_text(json.dumps(receipt,indent=2)+chr(10))
    work.mkdir();os.chown(work,101,101);print(json.dumps(receipt))


def main():
    root=phase2_vm.ROOT;contract=root/'config/phase2/rust-crates.lock.json'
    config=json.loads(contract.read_text());parent=next(p for p in config['parents'] if p['name']=='librsvg')
    assert parent['vendor_exit']==0 and len(parent['packages'])==352
    frozen=json.loads((root/'config/phase2/sources.lock.json').read_text())['components']
    rows=[next(r for r in frozen if r['name']==name) for name in ['librsvg','librsvg-vendor']]
    payload=io.BytesIO()
    with zipfile.ZipFile(payload,'w',compression=zipfile.ZIP_STORED) as outer:
        for row in rows:
            path=root/'.local/sources'/row['filename'];assert digest(path)==row['sha256']
            outer.writestr(row['filename'],path.read_bytes())
        outer.writestr('toddy-crates.json',contract.read_bytes());outer.writestr('toddy-sources.json',json.dumps(rows).encode())
        for name,filename in [('toddy-build.py','librsvg_build.py'),('toddy-probe.c','librsvg-probe.c')]:
            outer.writestr(name,(root/'scripts/build/phase2'/filename).read_bytes())
    remote='from pathlib import Path\nimport hashlib,json,tomllib,os,stat\n'+inspect.getsource(digest)+'\n'+inspect.getsource(verify_vendor)+'\n'+inspect.getsource(readable_vendor)+'\n'+inspect.getsource(prepare_remote)+'\nprepare_remote()\n'
    compile(remote,'librsvg-source-preparation','exec')
    prefix=root/'.local/phase2/librsvg-input'
    with prefix.with_suffix('.log').open('xb') as output:
        result=subprocess.run(phase2_vm.ssh_args()+['python3 -c '+shlex.quote(remote)],input=payload.getvalue(),stdout=output,stderr=subprocess.STDOUT)
    prefix.with_suffix('.exit').write_text(str(result.returncode)+'\n');raise SystemExit(result.returncode)


if __name__=='__main__':main()
