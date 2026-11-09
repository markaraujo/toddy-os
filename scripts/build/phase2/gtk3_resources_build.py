"""Qualify shared schemas and GTK3 input-module data without system writes."""
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    assert os.getuid()==101
    src=Path('/src');work=Path('/build');union=work/'schema-union';union.mkdir()
    recipe=json.loads((src/'toddy-resources.json').read_text())
    for directory in [src/'stock',src/'gtk3-stage/usr/share/glib-2.0/schemas']:
        for p in directory.iterdir():
            if p.name=='gschemas.compiled':continue
            assert p.is_file() and not p.is_symlink()
            output=union/p.name
            if output.exists():assert output.read_bytes()==p.read_bytes()
            else:shutil.copy2(p,output)
    with (work/'schema.log').open('xb') as log:
        subprocess.run(['glib-compile-schemas','--strict',str(union)],stdout=log,stderr=subprocess.STDOUT,check=True)
    import gi
    gi.require_version('Gio','2.0')
    from gi.repository import Gio
    baseline=Gio.SettingsSchemaSource.new_from_directory(str(src/'stock'),None,False)
    revised=Gio.SettingsSchemaSource.new_from_directory(str(union),None,False)
    def ids(source):
        fixed,relocatable=source.list_schemas(True)
        return sorted(set(fixed+relocatable))
    old=ids(baseline);new=ids(revised)
    old_fixed,old_relocatable=baseline.list_schemas(True)
    new_fixed,new_relocatable=revised.list_schemas(True)
    assert len(old_fixed)==52 and len(old_relocatable)==6 and set(old)<=set(new)
    assert len(new_fixed)==56 and len(new_relocatable)==6
    assert set(new)-set(old)=={'org.gtk.Settings.FileChooser','org.gtk.Settings.ColorChooser',
                               'org.gtk.Settings.Debug','org.gtk.Settings.EmojiChooser'}
    keys=0
    for name in new:
        schema=revised.lookup(name,True);assert schema
        for key in schema.list_keys():
            entry=schema.get_key(key);default=entry.get_default_value()
            assert default.is_of_type(entry.get_value_type())
            keys+=1
    stage=src/'gtk3-stage';modules=sorted(stage.glob('usr/lib/gtk-3.0/*/immodules/*.so'))
    assert len(modules)==11
    env=dict(os.environ,LD_LIBRARY_PATH=str(stage/'usr/lib'))
    result=subprocess.run([str(stage/'usr/bin/gtk-query-immodules-3.0'),*[str(p) for p in modules]],
                          env=env,text=True,capture_output=True,timeout=60,check=True)
    (work/'immodules-original.cache').write_text(result.stdout)
    (work/'immodules.stderr').write_text(result.stderr)
    assert not result.stderr.strip(), 'Inspect unexpected input-module loader diagnostics'
    lines=[line for line in result.stdout.splitlines() if line.startswith('"'+str(stage)+'/')]
    assert {shlex.split(line)[0] for line in lines}=={str(p) for p in modules}
    assert all(len(shlex.split(line))==1 for line in lines)
    canonical=result.stdout.replace(str(stage),'')
    assert '/src/' not in canonical
    cache=work/'immodules.cache';cache.write_text(canonical)
    assert len([line for line in canonical.splitlines() if line.startswith('"/usr/')])==11
    proof={'scope':'Native shared schema defaults/types and GTK3 input-module metadata loading only; no widget/display/IME text-entry/GDM/GNOME acceptance',
           'schema_exit':0,'baseline_schemas':len(old),'union_schemas':len(new),'schema_keys_checked':keys,
           'baseline_fixed':len(old_fixed),'baseline_relocatable':len(old_relocatable),
           'union_fixed':len(new_fixed),'union_relocatable':len(new_relocatable),
           'schema_ids':new,'new_ids':sorted(set(new)-set(old)),
           'schema_cache_sha256':sha(union/'gschemas.compiled'),
           'schema_inputs':{p.name:sha(p) for p in union.iterdir() if p.name!='gschemas.compiled'},
           'immodules_query_exit':0,'immodules':{str(p.relative_to(stage)):sha(p) for p in modules},
           'immodules_cache_sha256':sha(cache),'frozen_input_sha256':sha(src/'toddy-resources.json'),
           'old_owned_gtk_version':recipe['old_gtk_version']}
    (work/'test-results.json').write_text(json.dumps(proof,indent=2)+'\n')
    print(json.dumps({k:proof[k] for k in ['baseline_schemas','union_schemas','schema_keys_checked','schema_cache_sha256','immodules_query_exit']}))


if __name__=='__main__':main()
