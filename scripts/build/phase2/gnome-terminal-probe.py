"""Actual Terminal client and private DConf profiles across two session buses."""
from pathlib import Path
import json,os,shutil,subprocess,sys
prefix=Path(sys.argv[1]);work=Path(sys.argv[2]);assert not work.exists();work.mkdir(mode=0o700)
exe=prefix/'usr/bin/gnome-terminal'
r=subprocess.run([str(exe),'--version'],capture_output=True,text=True,timeout=15);assert r.returncode==0 and '3.60.0' in r.stdout
bad=subprocess.run([str(exe),'--toddy-invalid-option'],capture_output=True,text=True,timeout=15);assert bad.returncode!=0
schema=work/'schemas';schema.mkdir();shutil.copyfile(prefix/'usr/share/glib-2.0/schemas/org.gnome.Terminal.gschema.xml',schema/'org.gnome.Terminal.gschema.xml')
subprocess.run(['glib-compile-schemas','--strict',str(schema)],check=True)
services=work/'data/dbus-1/services';services.mkdir(parents=True)
(services/'ca.desrt.dconf.service').write_text('[D-BUS Service]\nName=ca.desrt.dconf\nExec=/usr/libexec/dconf-service\n')
config=work/'config';config.mkdir(mode=0o700);runtime=work/'runtime';runtime.mkdir(mode=0o700)
env=dict(os.environ,GSETTINGS_SCHEMA_DIR=str(schema),GSETTINGS_BACKEND='dconf',XDG_CONFIG_HOME=str(config),XDG_DATA_HOME=str(work/'data'),XDG_RUNTIME_DIR=str(runtime),PYTHONDONTWRITEBYTECODE='1')
code='''import gi,json,subprocess,sys
from gi.repository import Gio,GLib
mode=sys.argv[1];uuid='b02b02b0-0000-4000-8000-000000000001';path='/org/gnome/terminal/legacy/profiles:/:'+uuid+'/'
profile=Gio.Settings.new_with_path('org.gnome.Terminal.Legacy.Profile',path);profiles=Gio.Settings.new('org.gnome.Terminal.ProfilesList')
if mode=='write':
 assert profile.get_boolean('use-system-font')
 font=profile.get_string('font')
 assert profile.set_string('visible-name','Toddy ã') and profile.set_boolean('use-theme-colors',False)
 assert profile.set_string('background-color','#081b33') and profile.set_string('foreground-color','#f4f7fb')
 assert profiles.set_strv('list',[uuid]) and profiles.set_string('default',uuid)
 Gio.Settings.sync()
 bad=subprocess.run(['gsettings','set','org.gnome.Terminal.Legacy.Profile:'+path,'use-theme-colors','not-a-boolean'],capture_output=True,text=True,timeout=10)
 assert bad.returncode!=0 and not profile.get_boolean('use-theme-colors')
 assert profile.get_boolean('use-system-font') and profile.get_string('font')==font
 print(json.dumps({'typed_profile_written':True,'invalid_boolean_refused_state_preserved':True,'system_font_preserved':True}))
else:
 assert profiles.get_strv('list')==[uuid] and profiles.get_string('default')==uuid
 assert profile.get_string('visible-name')=='Toddy ã' and profile.get_string('background-color')=='#081b33' and profile.get_string('foreground-color')=='#f4f7fb'
 assert not profile.get_boolean('use-theme-colors') and profile.get_boolean('use-system-font')
 for key in ['visible-name','background-color','foreground-color','use-theme-colors']:profile.reset(key)
 profiles.reset('list');profiles.reset('default');Gio.Settings.sync()
 assert profile.get_string('visible-name')=='Unnamed' and profile.get_boolean('use-theme-colors') and profiles.get_strv('list')==profiles.get_default_value('list').unpack()
 print(json.dumps({'persisted_after_bus_restart':True,'reset_recovered_defaults':True,'system_font_preserved':True}))
'''
records=[]
for mode in ['write','read']:
 r=subprocess.run(['dbus-run-session','--','python3','-c',code,mode],env=env,capture_output=True,text=True,timeout=35)
 if r.returncode:sys.stderr.write(r.stderr)
 assert r.returncode==0;records.append(json.loads(r.stdout))
assert (config/'dconf/user').is_file()
print(json.dumps({'client_version':'3.60.0','invalid_CLI_option_refused':True,'profile_cycles':records,'private_DConf_file':True,'widget_or_display_tested':False}))
