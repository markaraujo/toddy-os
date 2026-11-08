"""Build three independently staged frozen desktop resource packages offline."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess


def main():
    assert os.getuid()==101 and not list(Path('/stage').iterdir())
    root=Path('/build/resources');root.mkdir()
    for name in ['compile','logs','icon-union','schema-union']:(root/name).mkdir()
    config=json.loads(Path('/src/toddy-resources.json').read_text());assert len(config['packages'])==3
    results=[]
    def run(name,phase,command,extra=None):
        log=root/'logs'/(name+'-'+phase+'.log')
        with log.open('xb') as out:
            r=subprocess.run(command,cwd=root,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',**(extra or {})),stdout=out,stderr=subprocess.STDOUT)
        log.with_suffix('.exit').write_text(str(r.returncode)+'\n');assert r.returncode==0,str(log)
        return {'phase':phase,'native_exit':r.returncode,'command':command,'log_sha256':hashlib.sha256(log.read_bytes()).hexdigest()}
    for package in config['packages']:
        name=package['name'];build=root/'compile'/name;stage=Path('/stage')/name
        commands=[]
        commands.append(run(name,'configure',['meson','setup',str(build),'/src/'+package['source_root'],
            '--prefix=/usr','--libdir=lib','--buildtype=release','--wrap-mode=nofallback',*package['options']]))
        commands.append(run(name,'build',['ninja','-C',str(build),'-j4']))
        tests=json.loads(subprocess.check_output(['meson','introspect','--tests',str(build)],text=True))
        if tests:
            commands.append(run(name,'upstream-tests',['meson','test','-C',str(build),'--print-errorlogs','--no-rebuild']))
        commands.append(run(name,'stage',['ninja','-C',str(build),'install'],{'DESTDIR':str(stage)}))
        results.append({'name':name,'version':package['version'],'commands':commands,'registered_upstream_tests':len(tests),
            'upstream_note':'No registered executable suite' if not tests else 'Actual registered native tests executed',
            'stage':str(stage)})
        print(json.dumps({'name':name,'native_build_stage_exit':0}),flush=True)
    # Generate caches from the actual complete stock input union, keeping each
    # foreign package's payload out of its cache owner's independent stage.
    installed_icons=Path('/usr/share/icons')
    if installed_icons.exists():shutil.copytree(installed_icons,root/'icon-union',dirs_exist_ok=True,symlinks=True)
    caches=[]
    for name,theme in [('hicolor-icon-theme','hicolor'),('adwaita-icon-theme','Adwaita')]:
        path=Path('/stage')/name/'usr/share/icons'/theme;union=root/'icon-union'/theme
        shutil.copytree(path,union,dirs_exist_ok=True,symlinks=True)
        run(name,'cache',['gtk4-update-icon-cache','-qtf',str(union)])
        run(name,'cache-validate',['gtk4-update-icon-cache','--validate',str(union)])
        data=(union/'icon-theme.cache').read_bytes();assert data and b'/build/' not in data and b'/stage/' not in data
        (path/'icon-theme.cache').write_bytes(data)
        caches.append({'package':name,'theme':theme,'sha256':hashlib.sha256(data).hexdigest(),
                       'source_scope':'Installed stock icons plus new theme stage, no user directories'})
    schemas=root/'schema-union'
    for directory in [Path('/usr/share/glib-2.0/schemas'),Path('/stage/gsettings-desktop-schemas/usr/share/glib-2.0/schemas')]:
        for p in directory.iterdir():
            if p.is_file() and p.name!='gschemas.compiled':
                destination=schemas/p.name
                if destination.exists():assert destination.read_bytes()==p.read_bytes()
                else:shutil.copy2(p,destination)
    run('gsettings-desktop-schemas','schema-cache',['glib-compile-schemas','--strict',str(schemas)])
    native_gi='/stage/gsettings-desktop-schemas/usr/lib/girepository-1.0'
    run('desktop-resources','consumer',['python3','/src/toddy-probe.py','/stage',str(schemas),str(root/'icon-union')],{'GI_TYPELIB_PATH':native_gi})
    cache=schemas/'gschemas.compiled';assert b'/build/' not in cache.read_bytes()
    source_manifest={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in schemas.iterdir() if p.is_file() and p.name!='gschemas.compiled'}
    result={'scope':'Native resource data/cache/API qualification only; no graphical GNOME/window acceptance',
            'packages':results,'icon_caches':caches,'schema_inputs':source_manifest,
            'combined_schema_cache_sha256':hashlib.sha256(cache.read_bytes()).hexdigest(),
            'consumer_exit':0,'consumer':json.loads((root/'logs/desktop-resources-consumer.log').read_text()),
            'schema_cache_scope':'Private combined schema proof; native cache requires same-owner controlled transaction'}
    Path('/build/test-results.json').write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':main()
