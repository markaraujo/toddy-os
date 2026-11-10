"""Actual private compiled schema contracts, never display or power operations."""
from pathlib import Path
import json,os,sys
import gi
gi.require_version('Gio','2.0')
from gi.repository import Gio,GLib
assert os.environ.get('GSETTINGS_BACKEND')=='memory'
source=Gio.SettingsSchemaSource.new_from_directory(sys.argv[1],Gio.SettingsSchemaSource.get_default(),False)
color=source.lookup('org.gnome.settings-daemon.plugins.color',False);power=source.lookup('org.gnome.settings-daemon.plugins.power',False);assert color and power
assert color.get_key('night-light-enabled').get_value_type().dup_string()=='b'
assert color.get_key('night-light-temperature').get_value_type().dup_string()=='u'
action=power.get_key('sleep-inactive-ac-type');assert action.range_check(action.get_default_value()) and not action.range_check(GLib.Variant('s','toddy-invalid-action'))
s=Gio.Settings.new_full(color,None,None);default=color.get_key('night-light-enabled').get_default_value().unpack();temp=color.get_key('night-light-temperature').get_default_value().unpack()
for cycle in [1,2]:
 assert s.set_boolean('night-light-enabled',not default) and s.get_boolean('night-light-enabled')!=default
 assert s.set_uint('night-light-temperature',5500) and s.get_uint('night-light-temperature')==5500
 s.reset('night-light-enabled');s.reset('night-light-temperature')
 assert s.get_boolean('night-light-enabled')==default and s.get_uint('night-light-temperature')==temp
schemas=source.list_schemas(False)
print(json.dumps({'private_schema_count':len(schemas[0])+len(schemas[1]),'typed_color_boolean_uint':True,'invalid_power_enum_refused':True,'memory_settings_reset_recovery_cycles':2,'stock_schema_cache_or_actual_services_display_audio_power_tested':False}))
