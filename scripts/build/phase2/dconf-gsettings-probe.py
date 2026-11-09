"""Real GSettings DConf module persistence with a private schema and user database."""
import hashlib,json,os,shutil,subprocess,sys
from pathlib import Path
prefix=Path(sys.argv[1]);work=Path(sys.argv[2]);mode=sys.argv[3]
assert mode in ['stage','installed'] and not work.exists();work.mkdir(mode=0o700)
service=str(prefix/'usr/libexec/dconf-service');assert Path(service).is_file()
share=work/'data';services=share/'dbus-1/services';services.mkdir(parents=True)
(services/'ca.desrt.dconf.service').write_text('[D-BUS Service]\nName=ca.desrt.dconf\nExec='+service+'\n')
for name in ['config','runtime','schemas']:(work/name).mkdir(mode=0o700)
schemas=work/'schemas';(schemas/'org.toddy.DConfProbe.gschema.xml').write_text('''<schemalist><schema id="org.toddy.DConfProbe" path="/org/toddy/dconf-probe/"><key name="value" type="s"><default>'base'</default></key></schema></schemalist>''')
subprocess.run(['glib-compile-schemas','--strict',str(schemas)],check=True)
env=dict(os.environ,XDG_DATA_HOME=str(share),XDG_CONFIG_HOME=str(work/'config'),XDG_RUNTIME_DIR=str(work/'runtime'),GSETTINGS_SCHEMA_DIR=str(schemas),GSETTINGS_BACKEND='dconf',PYTHONDONTWRITEBYTECODE='1')
for name in ['GIO_EXTRA_MODULES','GIO_MODULE_DIR','DCONF_PROFILE']:env.pop(name,None)
if mode=='stage':
    modules=work/'modules';modules.mkdir();original=prefix/'usr/lib/gio/modules/libdconfsettings.so';target=modules/original.name;shutil.copy2(original,target)
    assert hashlib.sha256(original.read_bytes()).digest()==hashlib.sha256(target.read_bytes()).digest()
    subprocess.run(['gio-querymodules',str(modules)],check=True)
    env.update(GIO_EXTRA_MODULES=str(modules),LD_LIBRARY_PATH=str(prefix/'usr/lib'))
else:env.pop('LD_LIBRARY_PATH',None)
code='''import json,sys
from gi.repository import Gio
backend=Gio.SettingsBackend.get_default();assert backend.__gtype__.name=='DConfSettingsBackend'
s=Gio.Settings.new('org.toddy.DConfProbe')
if sys.argv[1]=='write':
 assert s.get_string('value')=='base'
 assert s.set_string('value','navy');Gio.Settings.sync()
 assert s.get_string('value')=='navy'
 print(json.dumps({'backend':backend.__gtype__.name,'write':True,'sync':True}))
else:
 assert s.get_string('value')=='navy'
 s.reset('value');Gio.Settings.sync();assert s.get_string('value')=='base'
 print(json.dumps({'backend':backend.__gtype__.name,'persisted_after_new_bus':True,'reset':True}))
'''
records=[]
for cycle in ['write','read']:
 r=subprocess.run(['dbus-run-session','--','python3','-c',code,cycle],env=env,capture_output=True,text=True,timeout=30,check=True);records.append(json.loads(r.stdout))
assert (work/'config/dconf/user').is_file()
print(json.dumps({'scope':'Actual GSettings DConf backend/private schema/private user database, no user settings changed','mode':mode,'cycles':records,'unrelated_configuration_changed':False}))
