#!/usr/bin/env python3
"""Prepare one immutable, fully pinned Python test-backend input in the guest."""
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
    import fcntl,hashlib,io,json,os,stat,subprocess,sys,zipfile
    subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
    lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
    source=Path('/mnt/lfs/sources/phase2/inputs/python-test-tools-13.1')
    work=Path('/mnt/lfs/sources/phase2/work/python-test-tools-1')
    assert not source.exists() and not work.exists(),'Reconcile prior preparation; no replay'
    data=sys.stdin.buffer.read();assert len(data)<100*1024**2
    with zipfile.ZipFile(io.BytesIO(data)) as outer:
        config_bytes=outer.read('toddy-tools.json');config=json.loads(config_bytes)
        assert len(config['packages'])==12
        names={row['archive'] for row in config['packages']}
        assert len(names)==12 and set(outer.namelist())==names|{'toddy-tools.json','toddy-build.py','toddy-probe.py'}
        canonical=Path('/opt/toddy-build/config/phase2/python-test-tools.lock.json')
        assert canonical.read_bytes()==config_bytes
        for row in config['packages']:
            name=row['archive'];assert Path(name).name==name and '/' not in name
            payload=outer.read(name);assert hashlib.sha256(payload).hexdigest()==row['source_sha256']
            path=Path('/mnt/lfs/sources')/name;part=path.with_name(name+'.part')
            assert not part.exists(),'Reconcile incomplete archive transfer'
            if path.exists():assert hashlib.sha256(path.read_bytes()).hexdigest()==row['source_sha256']
            else:
                with part.open('xb') as output:output.write(payload);output.flush();os.fsync(output.fileno())
                part.replace(path)
        statfs=os.statvfs('/mnt/lfs');assert statfs.f_bavail*statfs.f_frsize>=18*1024**3
        source.mkdir()
        for row in config['packages']:
            subprocess.run(['python3','/opt/toddy-build/scripts/build/source.py',row['archive']],cwd=source,check=True)
            path=source/row['source_root']
            assert path.is_dir() and path.resolve().is_relative_to(source)
            # Do not discover a private archive mode by failing midway through
            # a compiler source copy. Preserve unexpected metadata for diagnosis.
            unreadable=[str(p.relative_to(source)) for p in path.rglob('*')
                        if p.is_file() and not p.is_symlink() and not p.stat().st_mode & stat.S_IROTH]
            assert not unreadable,unreadable
        for name in ['toddy-tools.json','toddy-build.py','toddy-probe.py']:
            (source/name).write_bytes(outer.read(name))
    receipt={'scope':'Authenticated source/backend preparation only, no native execution/install',
             'config_sha256':hashlib.sha256(config_bytes).hexdigest(),
             'recipe_sha256':hashlib.sha256((source/'toddy-build.py').read_bytes()).hexdigest(),
             'probe_sha256':hashlib.sha256((source/'toddy-probe.py').read_bytes()).hexdigest(),
             'sources':config['packages']}
    (source/'toddy-prepared.json').write_text(json.dumps(receipt,indent=2)+chr(10))
    work.mkdir();os.chown(work,101,101)
    print(json.dumps(receipt))


def main():
    root=phase2_vm.ROOT
    config_path=root/'config/phase2/python-test-tools.lock.json'
    config=json.loads(config_path.read_text())
    lock=json.loads((root/'config/phase2/sources.lock.json').read_text())['components']
    payload=io.BytesIO()
    with zipfile.ZipFile(payload,'w',compression=zipfile.ZIP_STORED) as outer:
        for row in config['packages']:
            matches=[r for r in lock if r['name']==row['name']]
            assert len(matches)==1 and matches[0]['version']==row['version']
            assert matches[0]['sha256']==row['source_sha256']
            path=root/'.local/sources'/row['archive'];data=path.read_bytes()
            assert hashlib.sha256(data).hexdigest()==row['source_sha256']
            outer.writestr(row['archive'],data)
        outer.writestr('toddy-tools.json',config_path.read_bytes())
        for name,filename in [('toddy-build.py','python_tools_build.py'),('toddy-probe.py','python_tools_probe.py')]:
            body=(root/'scripts/build/phase2'/filename).read_bytes();compile(body,filename,'exec')
            outer.writestr(name,body)
    remote=inspect.getsource(prepare_remote)+'\nprepare_remote()\n'
    compile(remote,'prepared-remote-python-tools','exec')
    prefix=root/'.local/phase2/python-test-tools-input'
    with prefix.with_suffix('.log').open('xb') as output:
        result=subprocess.run(phase2_vm.ssh_args()+['python3 -c '+shlex.quote(remote)],
                              input=payload.getvalue(),stdout=output,stderr=subprocess.STDOUT)
    prefix.with_suffix('.exit').write_text(str(result.returncode)+'\n')
    raise SystemExit(result.returncode)


if __name__=='__main__':main()
