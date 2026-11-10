#!/usr/bin/env python3
"""Actual staged GI/source JavaScript and private schemas; no display claim."""
import hashlib,json,os,shutil,subprocess,sys
from pathlib import Path
import gi
source,stage,work=map(Path,sys.argv[1:])
for name in ['Shell','St']:gi.require_version(name,'18')
from gi.repository import Shell,St,Gio,GLib
assert Shell.util_get_week_start() in range(7)
assert St.Widget.__gtype__.name=='StWidget'
script=work/'params-consumer.js'
module=(source/'js/misc/params.js').as_uri()
script.write_text('import * as Params from '+json.dumps(module)+''';
const defaults = {foo: 'Toddy', count: 42, extra: null};
function check(v) { if (!v) throw new Error('params postcondition'); }
for (let cycle = 0; cycle < 2; cycle++) {
    let r = Params.parse(null, defaults);
    check(r.foo === 'Toddy' && r.count === 42 && r !== defaults);
    r = Params.parse({count: 7}, defaults);
    check(r.count === 7 && defaults.count === 42);
    let refused = false;
    try { Params.parse({unknown: true}, defaults); } catch (e) { refused = true; }
    check(refused);
    check(Params.parse({unknown: true}, defaults, true).unknown === true);
    check(Params.parse({}, defaults).count === 42);
}
print(JSON.stringify({cycles: 2, defaults: true, override: true,
    unknown_refused: true, explicit_extra: true, recovery: true}));
''')
r=json.loads(subprocess.check_output(['gjs','-m',str(script)],text=True,timeout=20))
union=work/'schema-union';union.mkdir();inputs={}
for base in [Path('/usr/share/glib-2.0/schemas'),stage/'usr/share/glib-2.0/schemas']:
    for p in sorted(base.iterdir()):
        if p.name=='gschemas.compiled':continue
        assert p.is_file() and not p.is_symlink()
        sha=hashlib.sha256(p.read_bytes()).hexdigest()
        assert p.name not in inputs or inputs[p.name]==sha
        inputs[p.name]=sha;shutil.copyfile(p,union/p.name)
subprocess.run(['glib-compile-schemas','--strict',str(union)],check=True)
ss=Gio.SettingsSchemaSource.new_from_directory(str(union),None,False)
schema=ss.lookup('org.gnome.shell',False);assert schema is not None
os.environ['GSETTINGS_BACKEND']='memory'
s=Gio.Settings.new_full(schema,None,None)
old=s.get_value('favorite-apps');bad=GLib.Variant('s','invalid-type')
assert not bad.is_of_type(schema.get_key('favorite-apps').get_value_type())
# range_check validates ranges; value type validation is a separate API.
for cycle in range(2):
    assert s.set_strv('favorite-apps',['org.gnome.Nautilus.desktop'])
    assert s.get_strv('favorite-apps')==['org.gnome.Nautilus.desktop']
    s.reset('favorite-apps');assert s.get_value('favorite-apps').equal(old)
print(json.dumps({'scope':'Real Shell/St GI type and weekday, unchanged source Params through native GJS, private schema/memory roundtrip/refusal/reset only; stock cache/desktop/input/login untested','GI_type':'StWidget','params':r,'params_source_sha256':hashlib.sha256((source/'js/misc/params.js').read_bytes()).hexdigest(),'schema_count':len(ss.list_schemas(False)[0]),'schema_inputs':inputs,'favorite_apps_cycles':2,'wrong_type_refused':True,'preferences_changed':False}))
