"""Compile strict owned schema union and compare all existing key contracts."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,xml.etree.ElementTree as ET
import gi
gi.require_version('Gio','2.0')
from gi.repository import Gio
p=Path('/build');source=Path('/src');proof=json.loads((source/'toddy-schema-union.json').read_text())
assert os.geteuid()==101 and not (p/'test-results.json').exists() and not (p/'schema-union').exists()
def digest(f):
    with f.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
for name,sha in proof['inputs'].items():assert digest(source/'schemas'/name)==sha
assert digest(source/'baseline-gschemas.compiled')==proof['old_cache_sha256']
union=p/'schema-union';shutil.copytree(source/'schemas',union)
for f in union.iterdir():f.chmod(0o644)
union.chmod(0o755)
with (p/'compile-schemas.log').open('x') as log:
    r=subprocess.run(['glib-compile-schemas','--strict',str(union)],stdout=log,stderr=subprocess.STDOUT)
(p/'compile-schemas.exit').write_text(str(r.returncode)+'\n');assert r.returncode==0
baseline=p/'baseline';baseline.mkdir();shutil.copyfile(source/'baseline-gschemas.compiled',baseline/'gschemas.compiled')
def describe(directory):
    schema_source=Gio.SettingsSchemaSource.new_from_directory(str(directory),None,False)
    fixed,relocatable=schema_source.list_schemas(False);result={}
    for identifier in sorted(fixed+relocatable):
        schema=schema_source.lookup(identifier,False);keys={}
        for name in schema.list_keys():
            key=schema.get_key(name);keys[name]={'type':key.get_value_type().dup_string(),'default':key.get_default_value().print_(True),'range':key.get_range().print_(True)}
        result[identifier]={'path':schema.get_path(),'keys':keys}
    return result
old=describe(baseline);new=describe(union)
assert all(new.get(identifier)==row for identifier,row in old.items()),'Existing schema contract/default changed; inspect before native promotion'
expected={s.get('id') for f in union.glob('*.xml') for s in ET.parse(f).findall('.//schema')}
assert None not in expected and set(new)==expected
required=['org.gnome.SessionManager','org.gnome.crypto.pgp','org.gnome.evolution-data-server','org.gnome.evolution-data-server.calendar','org.gnome.evolution-data-server.addressbook','org.gnome.Evolution.DefaultSources']
assert all(identifier in new for identifier in required)
cache=union/'gschemas.compiled';assert b'/build/' not in cache.read_bytes()
result={'scope':'Strict complete installed stock schema union and actual Gio schema/key/default/range lookup only; no user preferences written or native GUI acceptance', 'compile_exit':0,'native_consumer_exit':0,'inputs':proof['inputs'],'cache_sha256':digest(cache),'baseline_cache_sha256':proof['old_cache_sha256'],'baseline_schemas_preserved':len(old),'baseline_keys_preserved':sum(len(v['keys']) for v in old.values()),'total_schemas':len(new),'total_keys':sum(len(v['keys']) for v in new.values()),'added_schemas':sorted(set(new)-set(old)),'required_schema_lookup':required,'descriptions':new}
(p/'test-results.json').write_text(json.dumps(result,indent=2)+'\n')
