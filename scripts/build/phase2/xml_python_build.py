"""Enable only the native Python binding in the preserved libxml2 cache."""
import ast
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time


def main():
    assert os.getuid()==101
    root=Path('/build/python-binding-1');compile=Path('/build/compile');stage=root/'stage'
    def run(name,args,**kwargs):
        with (root/(name+'.log')).open('xb') as log:r=subprocess.run(args,stdout=log,stderr=subprocess.STDOUT,**kwargs)
        (root/(name+'.exit')).write_text(str(r.returncode)+'\n');assert r.returncode==0,(name,r.returncode)
    if root.exists():
        # Exact configure-only recovery: no repeat of a successful state change.
        assert (root/'configure.exit').read_text().strip()=='0'
        assert not (root/'binding-build.log').exists() and not list(stage.iterdir())
        binaries=json.loads((root/'core-before.json').read_text())
        for name,digest in binaries.items():
            with (compile/name).open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==digest
        options=json.loads((compile/'meson-info/intro-buildoptions.json').read_text())
        assert next(r['value'] for r in options if r['name']=='python')=='enabled'
    else:
        root.mkdir();stage.mkdir();binaries={}
        for p in compile.rglob('*'):
            if p.is_file() and not p.is_symlink():
                with p.open('rb') as f:
                    if f.read(4)==b'\x7fELF':
                        f.seek(0);binaries[str(p.relative_to(compile))]=hashlib.file_digest(f,'sha256').hexdigest()
        assert binaries;(root/'core-before.json').write_text(json.dumps(binaries,indent=2)+'\n')
        run('configure',['meson','setup','--reconfigure',str(compile),'/src','-Dpython=enabled'])
    targets=json.loads(subprocess.check_output(['meson','introspect','--targets',str(compile)]))
    target=next(t for t in targets if t['name'].startswith('libxml2mod.') and t['type']=='shared module');assert len(target['filename'])==1
    relative=str(Path(target['filename'][0]).relative_to(compile))
    run('binding-build',['ninja','-C',str(compile),'-j4',relative])
    # Run original scripts with original relative fixtures in a writable copy.
    fixtures=root/'python-source';shutil.copytree('/src',fixtures,symlinks=True)
    for p in fixtures.rglob('*'):
        if not p.is_symlink():p.chmod(p.stat().st_mode|0o200)
    text=Path('/src/python/meson.build').read_text()
    tests=ast.literal_eval(text.split('python_tests =',1)[1].split('foreach file',1)[0].strip())
    assert len(tests)==48 and len(set(tests))==48
    env=dict(os.environ,PYTHONPATH=str(compile/'python'));rows=[]
    (root/'python-tests').mkdir()
    for name in tests:
        assert (fixtures/'python/tests'/name).is_file()
        start=time.monotonic()
        with (root/'python-tests'/(name+'.log')).open('xb') as log:
            r=subprocess.run(['python3',name],cwd=fixtures/'python/tests',env=env,stdout=log,stderr=subprocess.STDOUT)
        rows.append({'name':name,'exit':r.returncode,'seconds':round(time.monotonic()-start,3)})
        (root/'python-tests/results.json').write_text(json.dumps(rows,indent=2)+'\n')
    assert all(r['exit']==0 for r in rows),'Preserve original failed scripts; do not stage on failure'
    # Meson install --no-rebuild installs into private scratch, never the OS.
    full=root/'python-full-stage'
    run('private-install',['meson','install','-C',str(compile),'--no-rebuild','--destdir',str(full)])
    files=[]
    for p in full.rglob('*'):
        if not p.is_file() or p.is_symlink():continue
        rel=p.relative_to(full)
        if '/site-packages/' in '/'+str(rel) and p.suffix in ('.py','.so'):
            dest=stage/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest);files.append(str(rel))
    assert len(files)==3 and any(Path(f).name=='libxml2.py' for f in files)
    for name,digest in binaries.items():
        with (compile/name).open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==digest
    result={'scope':'Optional native Python binding only; accepted core and C suite reused',
            'upstream_python_scripts':rows,'existing_core_elf_files_unchanged':len(binaries),'payload':sorted(files)}
    (root/'test-results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))


if __name__=='__main__':main()
