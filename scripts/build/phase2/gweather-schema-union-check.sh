#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import hashlib,json,subprocess
prefix=['chroot','/mnt/lfs'];env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':'/tmp','PYTHONDONTWRITEBYTECODE':'1'}
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','gtk'],text=True)=='install ok installed 4.22.4-1+toddy7'
assert subprocess.check_output(prefix+['pkg-config','--modversion','gtk4'],text=True).strip()=='4.22.4'
assert not subprocess.check_output(prefix+['dpkg','--audit'],text=True).strip();subprocess.run(prefix+['apt-get','check'],check=True)
receipt=json.loads(Path('/var/log/toddy/phase2/gweather-schema-union-transaction-1.json').read_text());assert receipt['state']=='complete'
assert hashlib.sha256(Path('/mnt/lfs/usr/share/glib-2.0/schemas/gschemas.compiled').read_bytes()).hexdigest()==receipt['new_cache_sha256']
proof=json.loads(Path('/mnt/lfs/sources/phase2/work/gweather-schema-union-1/test-results.json').read_text())
code="""import gi,json
gi.require_version('Gio','2.0')
from gi.repository import Gio
source=Gio.SettingsSchemaSource.get_default();fixed,reloc=source.list_schemas(True);result={}
for identifier in sorted(fixed+reloc):
 schema=source.lookup(identifier,True);keys={}
 for name in schema.list_keys():
  key=schema.get_key(name);keys[name]={'type':key.get_value_type().dup_string(),'default':key.get_default_value().print_(True),'range':key.get_range().print_(True)}
 result[identifier]={'path':schema.get_path(),'keys':keys}
print(json.dumps(result))
"""
actual=json.loads(subprocess.check_output(prefix+['python3','-c',code],env=env,text=True,timeout=30))
assert actual==proof['descriptions']
Path('/var/log/toddy/phase2/gweather-schema-union-installed-consumer.json').write_text(json.dumps({'scope':'Owned GTK same-version shared schema cache: actual installed default-source lookup and all623key/type/default/range contracts; no user values changed. Native GWeather Info separately verified below; forecasts/owner position/GNOME graphical acceptance pending.', 'schemas':len(actual),'keys':sum(len(v['keys']) for v in actual.values()),'baseline_schemas_preserved':81,'baseline_keys_preserved':618,'new_schemas':proof['added_schemas'],'module_or_schema_override_used':False,'GTK_runtime_entries_unchanged':receipt['old_nonlegal_entries_unchanged']},indent=2)+'\n')
info_code="""import gi,json
from gi.repository import Gio,GLib
gi.require_version('GWeather','4.0')
from gi.repository import GWeather
assert 'GSETTINGS_SCHEMA_DIR' not in __import__('os').environ
source=Gio.SettingsSchemaSource.get_default();schema=source.lookup('org.gnome.GWeather4',True)
assert schema and len(schema.list_keys())==5
world=GWeather.Location.get_world();station=world.find_by_station_code('SBGR');assert station
cycles=[]
for cycle in range(2):
 info=GWeather.Info.new(station)
 info.set_application_id('org.toddy.NativeGWeatherProbe')
 info.set_contact_info('https://github.com/markaraujo/toddy-os')
 info.set_enabled_providers(GWeather.Provider.NONE)
 info.update();info.abort()
 while GLib.MainContext.default().pending():GLib.MainContext.default().iteration(False)
 assert info.get_location().get_code()=='SBGR'
 cycles.append({'cycle':cycle,'Info_created_updated_aborted':True,'location_preserved':True})
print(json.dumps({'stock_schema_lookup':True,'schema_keys':5,'GI':'GWeather4.0','providers_disabled_for_test':True,'cycles':cycles,'forecasts_or_owner_location_qualified':False}))
"""
info=json.loads(subprocess.check_output(['unshare','--net','chroot','--userspec=101:101','/mnt/lfs','python3','-c',info_code],env={**env,'GSETTINGS_BACKEND':'memory'},text=True,timeout=30))
Path('/var/log/toddy/phase2/gweather-stock-info-consumer.json').write_text(json.dumps({'scope':'Actual installed default stock schema and GWeather Info update/abort/recovery asUID101 in private no-route network namespace, providers disabled/memory settings only. No schema/module override, owner preferences, real provider/position or GNOME graphical acceptance.','consumer':info},indent=2)+'\n')
PY
