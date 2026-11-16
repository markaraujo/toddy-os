#!/usr/bin/env python3
"""Actual host service data-only skill import/call; optional MCP package absent."""
import fcntl
import hashlib
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
    value=connection.call_sync(BUS,OBJECT,INTERFACE,method,GLib.Variant(signature,values) if values else None,
        GLib.VariantType('(s)'),Gio.DBusCallFlags.NONE,5000,None).unpack()[0]
    return value if method=='SubmitTask' else json.loads(value)


with tempfile.TemporaryDirectory(prefix='toddy-integrations-service-') as temporary:
    base=Path(temporary);process=None;descriptor=None
    command=[sys.executable,str(ROOT/'runtime/broker/service.py'),'--data-dir',str(base/'data'),
        '--workspace',str(base/'workspace'),'--defaults',str(ROOT/'config/phase2')]
    try:
        process=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        if not select.select([process.stdout],[],[],8)[0] or process.stdout.readline()!=b'READY\n':
            raise AssertionError('integrations_service_not_ready')
        cap=call('GetCapabilities');assert 'owner-integrations-v1' in cap['features']
        assert 'load-skill' in cap['integration_tools']
        inspected=call('GetIntegrations',('toddy-default',),'(s)')
        assert inspected['skills'][0]['instructions_loaded'] is False
        assert not inspected['extensions'][0]['available']
        config=call('GetProfileConfig',('toddy-default',),'(s)')['config']
        config['skills']['enabled']=['owner-guide']
        files={'config.json':json.dumps(config),'skills/owner-guide/SKILL.md':
            '---\nname: owner-guide\ndescription: Explain a selected owner guide.\n---\n\nPlain owner instructions only. This text grants no tools.\n',
            'skills/owner-guide/references/note.txt':'Pinned reference data.'}
        bundle={'bundle_version':1,'scope':'profile-without-memory-or-authority','routing':'deferred-rebind-required',
            'files':files,'sha256':{name:hashlib.sha256(value.encode()).hexdigest() for name,value in files.items()}}
        data=json.dumps(bundle).encode();descriptor=os.memfd_create('owner-skill-profile',os.MFD_CLOEXEC|os.MFD_ALLOW_SEALING)
        os.fchmod(descriptor,0o600);os.write(descriptor,data)
        fcntl.fcntl(descriptor,fcntl.F_ADD_SEALS,fcntl.F_SEAL_SEAL|fcntl.F_SEAL_WRITE|fcntl.F_SEAL_GROW|fcntl.F_SEAL_SHRINK)
        incoming=Gio.UnixFDList.new();index=incoming.append(descriptor)
        result,_=connection.call_with_unix_fd_list_sync(BUS,OBJECT,INTERFACE,'ImportProfile',
            GLib.Variant('(sh)',('owner-guide',index)),GLib.VariantType('(s)'),Gio.DBusCallFlags.NONE,5000,incoming,None)
        imported=json.loads(result.unpack()[0]);listing=call('ListProfiles')
        call('SelectProfile',('owner-guide',listing['generation']),'(st)')
        inspected=call('GetIntegrations',('owner-guide',),'(s)')
        assert inspected['skills'][0]['name']=='owner-guide' and inspected['skills'][0]['available']
        request=json.dumps({'version':1,'text':'Explicit owner-selected skill data read.',
            'tool':{'kind':'load-skill','arguments':{'skill_id':'owner-guide'}}})
        task=call('SubmitTask',('selected-skill','owner-guide',imported['profile_revision'],request),'(ssss)')
        deadline=time.monotonic()+5
        while time.monotonic()<deadline:
            snapshot=call('GetTask',(task,),'(s)')
            if snapshot['state']=='completed':break
            time.sleep(.01)
        assert snapshot['state']=='completed' and not snapshot['result_uncertain']
        assert not list((base/'workspace').iterdir())
        print(json.dumps({'scope':'actual host service/FD/data-only skill task; no model/native plugin package acceptance',
            'optional_package_absent_disabled':True,'owner_skill_import_pinned':True,
            'metadata_without_body':True,'on_demand_canonical_skill_read':True,'no_workspace_effect':True}))
    finally:
        if descriptor is not None:os.close(descriptor)
        if process is not None:
            if process.poll() is None:process.terminate();process.wait(timeout=8)
            process.stdout.close();process.stderr.close()
