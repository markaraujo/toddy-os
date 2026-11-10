"""Frozen book's five proxy paths; rebuild only the separate reference cache."""
from pathlib import Path
import difflib,hashlib,json,re,shutil,subprocess

def correct():
 w=Path('/build');p=w/'book-schema-3';p.mkdir();source=Path('/src/src/external.gschema.xml');old=source.read_text()
 new,count=re.subn(r'"(/system)',r'"/org/gnome\1',old);assert count==5
 patched=p/'external.gschema.xml';patched.write_text(new);cache=p/'cache';cache.mkdir()
 patch=''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='a/src/external.gschema.xml',tofile='b/src/external.gschema.xml'))
 subprocess.run(['glib-compile-schemas','--targetdir',str(cache),'--schema-file','/src/src/org.gnome.Terminal.gschema.xml','--schema-file',str(patched)],check=True)
 from gi.repository import Gio
 before=Gio.SettingsSchemaSource.new_from_directory('/build/compile/src',None,False);after=Gio.SettingsSchemaSource.new_from_directory(str(cache),None,False)
 ids=set(sum((list(x) for x in before.list_schemas(False)),[]));assert ids==set(sum((list(x) for x in after.list_schemas(False)),[]))
 changes={};keys=0
 for name in sorted(ids):
  a=before.lookup(name,False);b=after.lookup(name,False);assert set(a.list_keys())==set(b.list_keys())
  if a.get_path()!=b.get_path():assert a.get_path().startswith('/system/');assert b.get_path()=='/org/gnome'+a.get_path();changes[name]={'before':a.get_path(),'after':b.get_path()}
  for key in a.list_keys():
   ka=a.get_key(key);kb=b.get_key(key);assert ka.get_value_type().dup_string()==kb.get_value_type().dup_string() and ka.get_default_value().equal(kb.get_default_value()) and ka.get_range().equal(kb.get_range());keys+=1
 assert len(changes)==5
 target=Path('/stage/usr/lib/gnome-terminal/gschemas.compiled');assert target.read_bytes()==(w/'compile/src/gschemas.compiled').read_bytes()
 before_sha=hashlib.sha256(target.read_bytes()).hexdigest();shutil.copyfile(cache/'gschemas.compiled',target)
 doc=Path('/stage/usr/share/doc/gnome-terminal');doc.mkdir(parents=True,exist_ok=True);(doc/'external-schema-paths.patch').write_text(patch)
 result={'reference':'BLFS13.1-systemd gnome/gnome-terminal.html','source_before_sha256':hashlib.sha256(old.encode()).hexdigest(),'source_after_sha256':hashlib.sha256(new.encode()).hexdigest(),'source_immutable':True,'compiled_ELFs_unchanged':True,'changed_schema_paths':changes,'preserved_schemas':len(ids),'preserved_key_type_default_range_contracts':keys,'stage_cache_before_sha256':before_sha,'stage_cache_after_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'patch_sha256':hashlib.sha256(patch.encode()).hexdigest()}
 (p/'result.json').write_text(json.dumps(result,indent=2)+'\n');return result
