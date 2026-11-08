"""Build frozen Python test backends as independent offline staged packages."""
import email.parser
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import zipfile


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def wheel_identity(path, name, version):
    with zipfile.ZipFile(path) as wheel:
        files=[p for p in wheel.namelist() if p.endswith('.dist-info/METADATA')]
        assert len(files)==1, 'Missing/ambiguous wheel metadata'
        metadata=email.parser.BytesParser().parsebytes(wheel.read(files[0]))
    normalize=lambda value:re.sub(r'[-_.]+','-',value).lower()
    assert normalize(metadata['Name'])==normalize(name), 'Wrong wheel package'
    assert metadata['Version']==version, 'Frozen wheel version drift'
    return {'name':metadata['Name'],'version':metadata['Version'],
            'requires_dist':metadata.get_all('Requires-Dist',[])}


def stage_entries(root):
    rows={}
    for path in sorted(root.rglob('*')):
        relative=str(path.relative_to(root))
        if path.is_symlink():rows[relative]={'symlink':os.readlink(path)}
        elif path.is_file():rows[relative]={'sha256':digest(path),'size':path.stat().st_size}
    return rows


def main():
    assert os.getuid()==101
    config=json.loads(Path('/src/toddy-tools.json').read_text())
    root=Path('/build/python-tools')
    assert not root.exists() and not list(Path('/stage').iterdir()), 'Reconcile existing build; no replay'
    stat=os.statvfs('/build');assert stat.f_bavail*stat.f_frsize>=18*1024**3
    root.mkdir();(root/'wheels').mkdir();(root/'bootstrap').mkdir();(root/'source').mkdir();(root/'logs').mkdir()
    env=dict(os.environ,PIP_NO_INDEX='1',PIP_CONFIG_FILE='/dev/null',
             PIP_DISABLE_PIP_VERSION_CHECK='1',PYTHONDONTWRITEBYTECODE='1',
             PYTHONNOUSERSITE='1',PYTHONPATH=str(root/'bootstrap'))
    results=[]
    for package in config['packages']:
        name=package['name'];version=package['version']
        assert re.fullmatch('[a-z][a-z0-9-]+',name)
        source=Path('/src')/package['source_root']
        destination=root/'source'/name
        assert source.is_dir() and source.is_relative_to('/src')
        shutil.copytree(source,destination,symlinks=True)
        env['SOURCE_DATE_EPOCH']=str(package['source_date_epoch'])
        log=root/'logs'/(name+'.log')
        before=set((root/'wheels').iterdir())
        commands=[['pip3','wheel','--no-index','--no-cache-dir','--no-build-isolation',
                   '--no-deps','--wheel-dir',str(root/'wheels'),'.']]
        with log.open('xb') as output:
            result=subprocess.run(commands[0],cwd=destination,env=env,stdout=output,stderr=subprocess.STDOUT)
            (root/'logs'/(name+'.build.exit')).write_text(str(result.returncode)+'\n')
            assert result.returncode==0, name+' wheel build failed; preserve prior packages'
            new=set((root/'wheels').iterdir())-before
            assert len(new)==1
            wheel=new.pop();identity=wheel_identity(wheel,name,version)
            stage=Path('/stage')/name
            assert not stage.exists()
            commands+=[['pip3','install','--ignore-installed','--no-index','--no-deps','--no-compile',
                         '--target',str(root/'bootstrap'),str(wheel)],
                        ['pip3','install','--ignore-installed','--no-index','--no-deps','--no-compile',
                         '--root',str(stage),'--prefix','/usr',str(wheel)]]
            for index,command in enumerate(commands[1:],1):
                result=subprocess.run(command,cwd=destination,env=env,stdout=output,stderr=subprocess.STDOUT)
                (root/'logs'/(name+'.install'+str(index)+'.exit')).write_text(str(result.returncode)+'\n')
                assert result.returncode==0, name+' private install failed'
        entries=stage_entries(stage)
        assert entries and all(p.startswith('usr/') for p in entries)
        results.append({'name':name,'version':version,'source_sha256':package['source_sha256'],
                        'source_date_epoch':package['source_date_epoch'],'commands':commands,
                        'wheel':str(wheel),'wheel_sha256':digest(wheel),'identity':identity,
                        'log_sha256':digest(log),'entries':entries})
        (root/'results.partial.json').write_text(json.dumps(results,indent=2)+'\n')
        print(json.dumps({'package':name,'version':version,'wheel_and_private_stage_exit':0}),flush=True)
    # Probe only staged distributions, excluding the private bootstrap copy.
    env['PYTHONPATH']=':'.join(str(Path('/stage')/p['name']/'usr/lib/python3.14/site-packages')
                               for p in config['packages'])
    with (root/'probe.log').open('xb') as output:
        result=subprocess.run(['python3','/src/toddy-probe.py','/src/toddy-tools.json',
                               '/build/python-tools-consumer'],env=env,stdout=output,stderr=subprocess.STDOUT)
    (root/'probe.exit').write_text(str(result.returncode)+'\n')
    assert result.returncode==0, 'Staged native test-tool consumers failed'
    assert all(stage_entries(Path('/stage')/row['name'])==row['entries'] for row in results)
    stat=os.statvfs('/build')
    proof={'scope':'Independent source-authenticated Python test/backend wheels and stages, no native owned install',
           'packages':results,'probe_exit':result.returncode,'probe_log_sha256':digest(root/'probe.log'),
           'consumer':json.loads(Path('/build/python-tools-consumer/results.json').read_text()),
           'config_sha256':digest(Path('/src/toddy-tools.json')),
           'free_bytes_after_build':stat.f_bavail*stat.f_frsize}
    (root/'qualified.json').write_text(json.dumps(proof,indent=2)+'\n')
    assert proof['free_bytes_after_build']>=16*1024**3


if __name__=='__main__':main()
