#!/usr/bin/env python3
"""Actual named-profile broker IPC/private files; no root/model/guest acceptance."""
import json
import os
from pathlib import Path
import select
import subprocess
import sys
import tempfile
import time

import gi
gi.require_version('Gio','2.0')
from gi.repository import Gio,GLib

ROOT=Path(__file__).resolve().parents[3]
BUS='io.github.markaraujo.Toddy.Service';OBJECT='/io/github/markaraujo/Toddy/Service';INTERFACE=BUS+'1'
if os.getuid()==0:raise SystemExit('unprivileged_source_probe_required')
connection=Gio.bus_get_sync(Gio.BusType.SESSION,None)


def call(method,values=(),signature='()'):
    result=connection.call_sync(BUS,OBJECT,INTERFACE,method,GLib.Variant(signature,values) if values else None,
        GLib.VariantType('(s)'),Gio.DBusCallFlags.NONE,5000,None).unpack()[0]
    return result if method=='SubmitTask' else json.loads(result)


def until(function):
    end=time.monotonic()+8
    while time.monotonic()<end:
        value=function()
        if value:return value
        time.sleep(.01)
    raise AssertionError('profile_probe_deadline')


def rejected(function):
    try:function()
    except GLib.Error:return
    raise AssertionError('expected_profile_denial')


def body(kind,args):return json.dumps({'version':1,'text':'Named profile source probe','tool':{'kind':kind,'arguments':args}})


with tempfile.TemporaryDirectory(prefix='toddy-profile-service-') as directory:
    base=Path(directory);data=base/'legacy-data';workspace=base/'workspace';process=None
    command=[sys.executable,str(ROOT/'runtime/broker/service.py'),'--data-dir',str(data),
             '--workspace',str(workspace),'--defaults',str(ROOT/'config/phase2')]
    def start():
        child=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        if not select.select([child.stdout],[],[],8)[0] or child.stdout.readline()!=b'READY\n':
            child.terminate();child.wait(timeout=5)
            raise AssertionError('profile_service_not_ready')
        return child
    started=time.monotonic()
    try:
        process=start()
        cap=call('GetCapabilities');assert 'named-profiles-v1' in cap['features']
        listing=call('ListProfiles');assert listing['active_profile_id']=='toddy-default'
        assert listing['profiles'][0]['id']=='toddy-default'
        settings=call('GetProfileConfig',('toddy-default',),'(s)')
        config=settings['config'];config['tools']['enabled']=['system-info','file-write','admin-command','shell']
        validated=call('ValidateProfile',('toddy-default',cap['profile_revision'],json.dumps(config)),'(sss)')
        revision=call('ApplyProfile',('toddy-default',cap['profile_revision'],validated['validated_revision']),'(sss)')['profile_revision']
        request=body('file-write',{'path':'owner.txt','text':'Original profile effect.','expected_sha256':None})
        task=call('SubmitTask',('profile-write','toddy-default',revision,request),'(ssss)')
        until(lambda:call('GetTask',(task,),'(s)')['state']=='completed')
        created=call('CreateProfile',('work',),'(s)');assert not created['selected']
        cloned=call('CloneProfile',('toddy-default',revision,'clone'),'(sss)');assert not cloned['selected']
        clone=call('GetProfileConfig',('clone',),'(s)')['config']
        assert clone['tools']['enabled']==['system-info'] and clone['provider']['mode']=='deferred'
        listed=call('ListProfiles');generation=listed['generation']
        selection=call('SelectProfile',('work',generation),'(st)')
        assert selection['generation']==generation+1
        assert call('GetTask',(task,),'(s)')['profile_id']=='toddy-default'
        assert call('SubmitTask',('profile-write','toddy-default',revision,request),'(ssss)')==task
        lookup=call('LookupRequest',('toddy-default','profile-write'),'(ss)')
        assert lookup['found'] and lookup['task']['task_id']==task
        assert not call('LookupRequest',('work','profile-write'),'(ss)')['found']
        metadata=call('ListTasks',('toddy-default',0),'(st)')
        assert metadata['tasks'][0]['request_id']=='profile-write'
        assert 'Original profile effect.' not in json.dumps(metadata)
        assert 'input_hash' not in json.dumps(metadata)
        work_revision=call('GetProfileConfig',('work',),'(s)')['profile_revision']
        rejected(lambda:call('SubmitTask',('disabled-admin','work',work_revision,
            body('admin-command',{'argv':['/usr/bin/true'],'timeout_seconds':1,
                                 'acknowledge_unrestricted_root':True})),'(ssss)'))
        # Export returns actual sealed readonly FD; import never chooses a path.
        response,fds=connection.call_with_unix_fd_list_sync(BUS,OBJECT,INTERFACE,'ExportProfile',
            GLib.Variant('(ss)',('work',work_revision)),GLib.VariantType('(h)'),Gio.DBusCallFlags.NONE,5000,None,None)
        descriptor=fds.get(response.unpack()[0])
        try:
            exported=os.pread(descriptor,8*1024*1024+1,0)
            assert json.loads(exported)['routing']=='deferred-rebind-required'
            incoming=Gio.UnixFDList.new();index=incoming.append(descriptor)
            result,_=connection.call_with_unix_fd_list_sync(BUS,OBJECT,INTERFACE,'ImportProfile',
                GLib.Variant('(sh)',('imported',index)),GLib.VariantType('(s)'),Gio.DBusCallFlags.NONE,5000,incoming,None)
            assert json.loads(result.unpack()[0])['profile_id']=='imported'
        finally:os.close(descriptor)
        assert call('ListProfiles')['active_profile_id']=='work'
        rejected(lambda:call('SelectProfile',('imported',generation),'(st)'))
        call('SelectProfile',('imported',selection['generation']),'(st)')
        process.terminate();process.wait(timeout=8);process.stdout.close();process.stderr.close()
        process=start()
        assert call('ListProfiles')['active_profile_id']=='imported'
        assert call('GetTask',(task,),'(s)')['state']=='completed'
        assert call('LookupRequest',('toddy-default','profile-write'),'(ss)')['task']['task_id']==task
        assert (workspace/'owner.txt').read_text()=='Original profile effect.'
        assert (data/'state.sqlite').is_file()  # Legacy leaf was not moved/copied.
        print(json.dumps({'scope':'actual-host-broker-private-bus-files-not-guest-model-or-root',
            'named_create_clone_select':True,'safe_import_tool_reset':True,'sealed_fd_export_import':True,
            'old_task_routes_after_selection_restart':True,'lookup_without_replay':True,
            'metadata_excludes_prompt_output':True,'legacy_db_path_preserved':True,
            'seconds':round(time.monotonic()-started,3)},sort_keys=True))
    finally:
        if process is not None:
            if process.poll() is None:process.terminate();process.wait(timeout=8)
            process.stdout.close();process.stderr.close()
