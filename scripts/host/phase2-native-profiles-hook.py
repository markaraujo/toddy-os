"""Trusted disposable B04/B05 source integration hook; called only by owner probe."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
import zlib

assert os.geteuid()==0 and os.uname().release=='7.1.8-toddy' and uid==12405
bundle=_native_broker_bundle;assert isinstance(bundle,dict) and len(bundle)<40
for name,text in bundle.items():
    target=Path(name)
    assert target.is_absolute() and '..' not in target.parts
    assert name.startswith(('/usr/lib/toddy/broker/','/usr/lib/toddy/tools/','/usr/lib/toddy/connections/','/usr/lib/toddy/local/','/usr/lib/toddy/shared/','/usr/lib/toddy/ui/','/usr/share/toddy/')) or name in [
        '/usr/lib/systemd/user/toddy-agent.service','/usr/share/dbus-1/services/io.github.markaraujo.Toddy.Service.service']
    assert not target.exists() and not target.is_symlink(),'Preserve existing native package files'
    target.parent.mkdir(parents=True,exist_ok=True);target.write_text(text);target.chmod(0o644)
env={'PATH':'/usr/bin:/usr/sbin','LANG':'C.UTF-8','HOME':'/home/'+username,'USER':username,'LOGNAME':username,
     'XDG_RUNTIME_DIR':'/run/user/'+str(uid),'DBUS_SESSION_BUS_ADDRESS':'unix:path=/run/user/'+str(uid)+'/bus'}
def user_command(argv,timeout=35,check=True):
    r=subprocess.run(argv,user=uid,group=uid,extra_groups=[],capture_output=True,text=True,env=env,timeout=timeout)
    assert not check or r.returncode==0,('native_broker_command_failed',argv[:3],r.returncode,r.stderr[-500:])
    return r
user_command(['/usr/bin/systemctl','--user','daemon-reload'])
user_command(['/usr/bin/systemctl','--user','start','toddy-agent.service'])
assert user_command(['/usr/bin/systemctl','--user','is-active','toddy-agent.service']).stdout.strip()=='active'
client=Path('/tmp/toddy-native-profiles-client.py')
client.write_text(r'''import gi,json,os,time
from pathlib import Path
from gi.repository import Gio,GLib
c=Gio.bus_get_sync(Gio.BusType.SESSION,None)
BUS='io.github.markaraujo.Toddy.Service';OBJ='/io/github/markaraujo/Toddy/Service';IFACE=BUS+'1'
def call(method,values=(),sig='()'):
 r=c.call_sync(BUS,OBJ,IFACE,method,GLib.Variant(sig,values) if values else None,GLib.VariantType('(s)'),Gio.DBusCallFlags.NONE,5000,None).unpack()[0]
 return r if method=='SubmitTask' else json.loads(r)
def until(fn):
 end=time.monotonic()+10
 while time.monotonic()<end:
  r=fn()
  if r:return r
  time.sleep(.02)
 raise AssertionError('native_profiles_deadline')
def denied(fn):
 try:fn()
 except GLib.Error:return
 raise AssertionError('expected_rejection')
cap=call('GetCapabilities');original=cap['profile_revision']
settings=call('GetProfileConfig',('toddy-default',),'(s)');config=settings['config']
bad={**config,'untrusted_grant':True}
denied(lambda:call('ValidateProfile',('toddy-default',original,json.dumps(bad)),'(sss)'))
assert call('GetCapabilities')['profile_revision']==original
config['tools']['enabled']=['system-info','file-write']
stage=call('ValidateProfile',('toddy-default',original,json.dumps(config)),'(sss)')
revision=call('ApplyProfile',('toddy-default',original,stage['validated_revision']),'(sss)')['profile_revision']
request=json.dumps({'version':1,'text':'Native captured profile effect','tool':{'kind':'file-write','arguments':{'path':'profile-proof.txt','text':'Captured original profile bytes.','expected_sha256':None}}})
task=call('SubmitTask',('native-profile-write','toddy-default',revision,request),'(ssss)')
call('CreateProfile',('work',),'(s)')
listing=call('ListProfiles');selected=call('SelectProfile',('work',listing['generation']),'(st)')
done=until(lambda:(lambda s:s if s['state']=='completed' else None)(call('GetTask',(task,),'(s)')))
assert done['profile_id']=='toddy-default' and done['profile_revision']==revision
assert call('SubmitTask',('native-profile-write','toddy-default',revision,request),'(ssss)')==task
assert call('LookupRequest',('toddy-default','native-profile-write'),'(ss)')['task']['task_id']==task
assert not call('LookupRequest',('work','native-profile-write'),'(ss)')['found']
metadata=call('ListTasks',('toddy-default',0),'(st)')
assert metadata['tasks'][0]['task_id']==task and 'Captured original profile bytes.' not in json.dumps(metadata)
old=call('GetProfileConfig',('toddy-default',),'(s)')
assert original in old['previous_revisions']
restored=call('RestoreProfile',('toddy-default',revision,original),'(sss)')
assert restored['restored'] and restored['profile_revision']==original
assert call('GetTask',(task,),'(s)')['profile_revision']==revision
cloned=call('CloneProfile',('toddy-default',original,'clone'),'(sss)')
clone=call('GetProfileConfig',('clone',),'(s)')['config']
assert clone['tools']['enabled']==['system-info'] and clone['provider']['mode']=='deferred'
work=call('GetProfileConfig',('work',),'(s)')['profile_revision']
reply,fds=c.call_with_unix_fd_list_sync(BUS,OBJ,IFACE,'ExportProfile',GLib.Variant('(ss)',('work',work)),GLib.VariantType('(h)'),Gio.DBusCallFlags.NONE,5000,None,None)
fd=fds.get(reply.unpack()[0])
try:
 raw=os.pread(fd,8*1024*1024+1,0);assert json.loads(raw)['routing']=='deferred-rebind-required'
 incoming=Gio.UnixFDList.new();index=incoming.append(fd)
 reply,_=c.call_with_unix_fd_list_sync(BUS,OBJ,IFACE,'ImportProfile',GLib.Variant('(sh)',('imported',index)),GLib.VariantType('(s)'),Gio.DBusCallFlags.NONE,5000,incoming,None)
 assert json.loads(reply.unpack()[0])['profile_id']=='imported'
finally:os.close(fd)
denied(lambda:call('SelectProfile',('imported',listing['generation']),'(st)'))
print(json.dumps({'task_id':task,'profile_revision':revision,'selected_profile':'work','native_uid':os.getuid(),'invalid_edit_preserved_working_revision':True,'rollback_keeps_task_pin':True,'sealed_fd_export_import':True,'clone_resets_authority':True,'lookup_without_replay':True}))
''');client.chmod(0o644)
proof=json.loads(user_command(['/usr/bin/python3',str(client)]).stdout)
assert proof['native_uid']==uid
workspace=Path('/home/'+username+'/Toddy/profile-proof.txt')
# The fixed service workspace default is inspected from the actual user path.
assert workspace.read_text()=='Captured original profile bytes.'
before=workspace.stat().st_mtime_ns
launcher="import sys;sys.path.insert(0,'/usr/lib');from toddy.ui.cli import main;raise SystemExit(main())"
cli=user_command(['/usr/bin/python3','-I','-c',launcher,'task',proof['task_id']])
assert 'completed' in cli.stdout
listed=json.loads(user_command(['/usr/bin/python3','-I','-c',launcher,'profiles']).stdout)
assert listed['active_profile_id']=='work'
user_command(['/usr/bin/systemctl','--user','restart','toddy-agent.service'])
looked=json.loads(user_command(['/usr/bin/python3','-I','-c',launcher,'lookup','toddy-default','native-profile-write']).stdout)
assert looked['found'] and looked['task']['profile_revision']==proof['profile_revision']
assert workspace.stat().st_mtime_ns==before
passed('native-named-profiles-task-pins-rollback-cli-and-restart-no-replay',**proof,cli_same_authenticated_service=True)
user_command(['/usr/bin/systemctl','--user','stop','toddy-agent.service'])
