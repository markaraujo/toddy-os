"""Validate the existing private schema union without compiling or writing preferences."""
import hashlib
import json
import os
from pathlib import Path
import xml.etree.ElementTree as ET

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    assert os.getuid()==101
    import gi
    gi.require_version('Gio','2.0')
    from gi.repository import Gio
    w=Path('/build');proof=json.loads((w/'test-results.json').read_text());union=w/'schema-union';assert sha(union/'gschemas.compiled')==proof['schema_cache_sha256']
    native=Path('/usr/share/glib-2.0/schemas');stage=Path('/stage/usr/share/glib-2.0/schemas')
    old={p.name:sha(p) for p in native.iterdir() if p.name!='gschemas.compiled'}
    added={p.name:sha(p) for p in stage.iterdir() if p.name!='gschemas.compiled'}
    assert len(added)==2 and not set(old)&set(added)
    assert {**old,**added}==proof['schema_inputs']=={p.name:sha(p) for p in union.iterdir() if p.name!='gschemas.compiled'}
    keys=0
    source=Gio.SettingsSchemaSource.new_from_directory(str(union),None,False)
    base=Gio.SettingsSchemaSource.new_from_directory(str(native),None,False)
    fixed,rel=source.list_schemas(False);old_fixed,old_rel=base.list_schemas(False)
    baseline_ids=set(old_fixed)|set(old_rel);all_xml={};staged_ids=set()
    for folder in [native,stage]:
        for p in folder.glob('*.gschema.xml'):
            for schema in ET.fromstring(p.read_bytes()).findall('schema'):
                name=schema.get('id');assert name not in all_xml
                all_xml[name]=schema.get('path')
                if folder==stage:staged_ids.add(name)
    assert set(fixed)|set(rel)==set(all_xml)
    expected={name:path for name,path in all_xml.items() if name not in baseline_ids}
    stock_pending=set(expected)-staged_ids
    assert stock_pending=={'org.freedesktop.ColorHelper'} and len(staged_ids)==4
    for name,path in expected.items():
        schema=source.lookup(name,False);assert schema is not None and schema.get_path()==path
        for keyname in schema.list_keys():
            key=schema.get_key(keyname);value=key.get_default_value();assert value.is_of_type(key.get_value_type()) and key.range_check(value);keys+=1
    result={'scope':'Private exact current GTK4-owned schema union with staged Mutter XML, default types/ranges only; no user preference or global cache writes','baseline_cache_sha256':sha(native/'gschemas.compiled'),'union_cache_sha256':sha(union/'gschemas.compiled'),'baseline_inputs':old,'added_inputs':added,'schema_inputs':proof['schema_inputs'],'new_schemas':expected,'pending_stock_schemas':sorted(stock_pending),'staged_mutter_schemas':sorted(staged_ids),'new_default_values_checked':keys,'baseline_fixed':len(old_fixed),'baseline_relocatable':len(old_rel),'union_fixed':len(fixed),'union_relocatable':len(rel),'native_exit':0}
    (w/'schema-qualification.json').write_text(json.dumps(result,indent=2)+'\n')
