#!/usr/bin/env python3
"""Actual private service bus/worker, deliberately absent root standing endpoint."""
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
system=Gio.bus_get_sync(Gio.BusType.SYSTEM,None)
assert not system.call_sync('org.freedesktop.DBus','/org/freedesktop/DBus','org.freedesktop.DBus',
    'NameHasOwner',GLib.Variant('(s)',('io.github.markaraujo.Toddy.Executor',)),
    GLib.VariantType('(b)'),Gio.DBusCallFlags.NONE,3000,None).unpack()[0], 'probe requires absent host executor'


def call(method,values=(),signature='()'):
    value=connection.call_sync(BUS,OBJECT,INTERFACE,method,GLib.Variant(signature,values) if values else None,
        GLib.VariantType('(s)'),Gio.DBusCallFlags.NONE,5000,None).unpack()[0]
    return json.loads(value)


with tempfile.TemporaryDirectory(prefix='toddy-automation-service-') as temporary:
    base=Path(temporary);process=None
    command=[sys.executable,str(ROOT/'runtime/broker/service.py'),'--data-dir',str(base/'data'),
        '--workspace',str(base/'workspace'),'--defaults',str(ROOT/'config/phase2')]
    def start():
        child=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        if not select.select([child.stdout],[],[],8)[0] or child.stdout.readline()!=b'READY\n':
            child.terminate();child.wait(timeout=5);raise AssertionError('automation_service_not_ready')
        return child
    started=time.monotonic()
    try:
        process=start()
        cap=call('GetCapabilities');assert 'owner-automation-v1' in cap['features']
        before=call('GetAutomation',('toddy-default',),'(s)');assert not before['jobs']
        config=call('GetProfileConfig',('toddy-default',),'(s)')['config']
        config['automation']={'enabled':True,'workflow_ids':['disk-health']}
        stage=call('ValidateProfile',('toddy-default',cap['profile_revision'],json.dumps(config)),'(sss)')
        revision=call('ApplyProfile',('toddy-default',cap['profile_revision'],stage['validated_revision']),'(sss)')['profile_revision']
        configured=call('ConfigureAutomation',('toddy-default',revision,json.dumps({'version':1,
            'operation':'configure','job_id':'health','action':'disk-health','interval':60,
            'next_due':time.time(),'missed':'skip','catchup':0,'seconds':10,'max_runs':2})),'(sss)')
        assert configured['enabled'] is False and configured['standing_grant_created'] is False
        # An enabled profile plus known workflow still cannot manufacture grant.
        try:
            call('ConfigureAutomation',('toddy-default',revision,json.dumps({'version':1,'operation':'enable','job_id':'health'})),'(sss)')
        except GLib.Error:pass
        else:raise AssertionError('missing root endpoint must deny standing authorization')
        state=call('GetAutomation',('toddy-default',),'(s)')
        assert state['jobs'][0]['enabled']==0 and state['runs']==[]
        assert state['registered_workflows']==['disk-health','service-health']
        assert not list((base/'workspace').iterdir())
        process.terminate();process.wait(timeout=8);process.stdout.close();process.stderr.close()
        process=start()
        state=call('GetAutomation',('toddy-default',),'(s)')
        assert state['jobs'][0]['id']=='health' and state['runs']==[]
        call('CloneProfile',('toddy-default',revision,'work'),'(sss)')
        assert call('GetAutomation',('work',),'(s)')['jobs']==[]
        assert call('GetProfileConfig',('work',),'(s)')['config']['automation']['enabled'] is False
        print(json.dumps({'scope':'actual host service bus/configuration/worker lifecycle only; no native timer/notification acceptance',
            'profile_never_grants_standing':True,'missing_root_endpoint_denies_enable':True,
            'disabled_schedule_restart':True,'clone_excludes_schedules':True,
            'workspace_unchanged':True,'seconds':round(time.monotonic()-started,3)}))
    finally:
        if process is not None:
            if process.poll() is None:process.terminate();process.wait(timeout=8)
            process.stdout.close();process.stderr.close()
