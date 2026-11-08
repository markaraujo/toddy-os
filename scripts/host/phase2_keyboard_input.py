#!/usr/bin/env python3
"""Authenticate the frozen keyboard pair and exact book patch before compilation."""
import hashlib
import inspect
import io
import json
from pathlib import Path
import shlex
import subprocess
import zipfile
import phase2_vm


def prepare_remote():
    from pathlib import Path
    import fcntl,hashlib,io,json,os,subprocess,sys,zipfile
    subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
    lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
    source=Path('/mnt/lfs/sources/phase2/inputs/keyboard-13.1')
    work=Path('/mnt/lfs/sources/phase2/work/keyboard-1')
    assert not source.exists() and not work.exists(),'Reconcile existing input/work; no replay'
    with zipfile.ZipFile(io.BytesIO(sys.stdin.buffer.read())) as outer:
        config_bytes=outer.read('toddy-keyboard.json');config=json.loads(config_bytes)
        assert Path('/opt/toddy-build/config/phase2/keyboard.lock.json').read_bytes()==config_bytes
        assert len(config['packages'])==2
        rows=[{'filename':r['archive'],'sha256':r['source_sha256']} for r in config['packages']]
        rows.append(config['patch'])
        assert set(outer.namelist())=={r['filename'] for r in rows}|{'toddy-keyboard.json','toddy-build.sh','toddy-probe.c'}
        for row in rows:
            name=row['filename'];assert Path(name).name==name
            data=outer.read(name);assert hashlib.sha256(data).hexdigest()==row['sha256']
            path=Path('/mnt/lfs/sources')/name;part=path.with_name(name+'.part');assert not part.exists()
            if path.exists():assert hashlib.sha256(path.read_bytes()).hexdigest()==row['sha256']
            else:
                with part.open('xb') as output:output.write(data);output.flush();os.fsync(output.fileno())
                part.replace(path)
        stat=os.statvfs('/mnt/lfs');assert stat.f_bavail*stat.f_frsize>=18*1024**3
        source.mkdir()
        for row in config['packages']:
            subprocess.run(['python3','/opt/toddy-build/scripts/build/source.py',row['archive']],cwd=source,check=True)
            assert (source/row['source_root']).is_dir()
        patch=Path('/mnt/lfs/sources')/config['patch']['filename']
        subprocess.run(['python3','/opt/toddy-build/scripts/build/source.py',patch.name,'--verify-only'],check=True)
        library=source/'libxkbcommon-1.13.2';path=library/'tools/info.c'
        before=hashlib.sha256(path.read_bytes()).hexdigest()
        subprocess.run(['patch','--batch','--forward','--fuzz=0','-Np1','-i',str(patch)],cwd=library,check=True)
        source_patch={'path':'libxkbcommon-1.13.2/tools/info.c','before_sha256':before,
                      'after_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                      'patch_sha256':config['patch']['sha256']}
        for name in ['toddy-keyboard.json','toddy-build.sh','toddy-probe.c']:
            (source/name).write_bytes(outer.read(name))
    receipt={'scope':'Authenticated keyboard source pair and exact required patch only; native build/tests/install pending',
             'sources':config['packages'],'source_patch':source_patch,
             'config_sha256':hashlib.sha256(config_bytes).hexdigest(),
             'recipe_sha256':hashlib.sha256((source/'toddy-build.sh').read_bytes()).hexdigest(),
             'probe_sha256':hashlib.sha256((source/'toddy-probe.c').read_bytes()).hexdigest()}
    (source/'toddy-prepared.json').write_text(json.dumps(receipt,indent=2)+chr(10))
    work.mkdir();os.chown(work,101,101)
    print(json.dumps(receipt))


def main():
    root=phase2_vm.ROOT;config_path=root/'config/phase2/keyboard.lock.json'
    config=json.loads(config_path.read_text());payload=io.BytesIO()
    rows=[{'filename':r['archive'],'sha256':r['source_sha256']} for r in config['packages']]+[config['patch']]
    with zipfile.ZipFile(payload,'w',compression=zipfile.ZIP_STORED) as outer:
        for row in rows:
            data=(root/'.local/sources'/row['filename']).read_bytes()
            assert hashlib.sha256(data).hexdigest()==row['sha256'];outer.writestr(row['filename'],data)
        outer.writestr('toddy-keyboard.json',config_path.read_bytes())
        outer.writestr('toddy-build.sh',(root/'scripts/build/phase2/keyboard-build.sh').read_bytes())
        outer.writestr('toddy-probe.c',(root/'scripts/build/phase2/keyboard-probe.c').read_bytes())
    remote=inspect.getsource(prepare_remote)+'\nprepare_remote()\n';compile(remote,'keyboard-preparation','exec')
    prefix=root/'.local/phase2/keyboard-input'
    with prefix.with_suffix('.log').open('xb') as output:
        result=subprocess.run(phase2_vm.ssh_args()+['python3 -c '+shlex.quote(remote)],input=payload.getvalue(),stdout=output,stderr=subprocess.STDOUT)
    prefix.with_suffix('.exit').write_text(str(result.returncode)+'\n');raise SystemExit(result.returncode)


if __name__=='__main__':main()
