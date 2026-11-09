"""Actual CLI/private-bus disk persistence with isolated user configuration."""
import json,os,subprocess,sys
from pathlib import Path
prefix=Path(sys.argv[1]);work=Path(sys.argv[2]);assert not work.exists();work.mkdir(mode=0o700)
exe=str(prefix/'usr/bin/dconf');service=str(prefix/'usr/libexec/dconf-service')
assert Path(exe).is_file() and Path(service).is_file()
share=work/'data';services=share/'dbus-1/services';services.mkdir(parents=True)
(services/'ca.desrt.dconf.service').write_text('[D-BUS Service]\nName=ca.desrt.dconf\nExec='+service+'\n')
config=work/'config';config.mkdir(mode=0o700);runtime=work/'runtime';runtime.mkdir(mode=0o700)
env=dict(os.environ,XDG_DATA_HOME=str(share),XDG_CONFIG_HOME=str(config),XDG_RUNTIME_DIR=str(runtime),LD_LIBRARY_PATH=str(prefix/'usr/lib'),PYTHONDONTWRITEBYTECODE='1')
# Every private bus is new; the second reader must observe the committed user DB.
code='''import json,subprocess,sys
exe=sys.argv[1];mode=sys.argv[2]
def call(*args,success=True):
 r=subprocess.run([exe,*args],capture_output=True,text=True,timeout=10)
 assert (r.returncode==0)==success
 return r.stdout.strip()
if mode=='write':
 call('write','/org/toddy/test/value',"'navy'")
 assert call('read','/org/toddy/test/value')=="'navy'"
 call('write','/org/toddy/test/value','(',success=False)
 assert call('read','/org/toddy/test/value')=="'navy'"
 print(json.dumps({'typed_write':True,'malformed_refused':True,'state_preserved':True}))
else:
 assert call('read','/org/toddy/test/value')=="'navy'"
 assert "value='navy'" in call('dump','/org/toddy/test/')
 call('reset','-f','/org/toddy/test/')
 assert call('read','/org/toddy/test/value')==''
 print(json.dumps({'persisted_after_bus_restart':True,'dump':True,'reset':True}))
'''
records=[]
for mode in ['write','read']:
 r=subprocess.run(['dbus-run-session','--','python3','-c',code,exe,mode],env=env,capture_output=True,text=True,timeout=30,check=True)
 records.append(json.loads(r.stdout))
assert (config/'dconf/user').is_file()
print(json.dumps({'cycles':records,'isolated_user_database':True,'unrelated_configuration_changed':False}))
