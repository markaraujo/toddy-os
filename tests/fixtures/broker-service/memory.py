#!/usr/bin/env python3
"""Actual host private-bus memory/profile/FD smoke; no model or native acceptance."""
import fcntl
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
from gi.repository import Gio, GLib

ROOT=Path(__file__).resolve().parents[3]
BUS='io.github.markaraujo.Toddy.Service'; OBJECT='/io/github/markaraujo/Toddy/Service'; INTERFACE=BUS+'1'
if os.getuid()==0:raise SystemExit('unprivileged_source_probe_required')
connection=Gio.bus_get_sync(Gio.BusType.SESSION,None)


def call(method,values=(),signature='()'):
    value=connection.call_sync(BUS,OBJECT,INTERFACE,method,GLib.Variant(signature,values) if values else None,
        GLib.VariantType('(s)'),Gio.DBusCallFlags.NONE,5000,None).unpack()[0]
    return json.loads(value)


def rejected(method,values,signature):
    try:call(method,values,signature)
    except GLib.Error:return
    raise AssertionError('expected_memory_denial')


def mutate(operation,**values):
    page=call('GetMemory',('toddy-default',),'(s)')
    return call('MutateMemory',('toddy-default',page['profile_revision'],json.dumps({'version':1,
        'memory_generation':page['memory_generation'],'operation':operation,**values})),'(sss)')


with tempfile.TemporaryDirectory(prefix='toddy-memory-service-') as temporary:
    base=Path(temporary); process=None
    command=[sys.executable,str(ROOT/'runtime/broker/service.py'),'--data-dir',str(base/'data'),
        '--workspace',str(base/'workspace'),'--defaults',str(ROOT/'config/phase2')]
    def start():
        child=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        if not select.select([child.stdout],[],[],8)[0] or child.stdout.readline()!=b'READY\n':
            child.terminate();child.wait(timeout=5);raise AssertionError('memory_service_not_ready')
        return child
    started=time.monotonic()
    try:
        process=start()
        cap=call('GetCapabilities');assert 'owner-memory-v1' in cap['features']
        initial=call('GetMemory',('toddy-default',),'(s)');assert not initial['records']
        first=mutate('put',id='language',text='Portuguese explicit preference',expires=None)
        page=call('GetMemory',('toddy-default',),'(s)')
        assert page['records'][0]['text']=='Portuguese explicit preference'
        assert 'user_document' not in page
        response,fds=connection.call_with_unix_fd_list_sync(BUS,OBJECT,INTERFACE,'ExportMemory',
            GLib.Variant('(sst)',('toddy-default',page['profile_revision'],page['memory_generation'])),
            GLib.VariantType('(h)'),Gio.DBusCallFlags.NONE,5000,None,None)
        backup=fds.get(response.unpack()[0])
        try:
            seals=fcntl.F_SEAL_SEAL|fcntl.F_SEAL_WRITE|fcntl.F_SEAL_GROW|fcntl.F_SEAL_SHRINK
            assert fcntl.fcntl(backup,fcntl.F_GET_SEALS)&seals==seals
            deleted=mutate('delete',id='language')
            # An editor stage taken before memory mutation is stale, never wins.
            settings=call('GetProfileConfig',('toddy-default',),'(s)');config=settings['config']
            config['display_name']='Memory settings CAS'
            stage=call('ValidateProfile',('toddy-default',deleted['profile_revision'],json.dumps(config)),'(sss)')
            changed=mutate('put',id='another',text='Keep current',expires=None)
            rejected('ApplyProfile',('toddy-default',deleted['profile_revision'],stage['validated_revision']),'(sss)')
            incoming=Gio.UnixFDList.new();index=incoming.append(backup)
            result,_=connection.call_with_unix_fd_list_sync(BUS,OBJECT,INTERFACE,'RestoreMemory',
                GLib.Variant('(ssth)',('toddy-default',changed['profile_revision'],changed['memory_generation'],index)),
                GLib.VariantType('(s)'),Gio.DBusCallFlags.NONE,5000,incoming,None)
            assert json.loads(result.unpack()[0])['profile_id']=='toddy-default'
        finally:os.close(backup)
        page=call('GetMemory',('toddy-default',),'(s)');assert all(r['id']!='language' for r in page['records'])
        # Explicit backup restore replaces memory, unlike profile rollback.
        mutate('put',id='another',text='Keep current',expires=None)
        page=call('GetMemory',('toddy-default',),'(s)')
        # Profile rollback restores settings/persona while memory stays current.
        call('RestoreProfile',('toddy-default',page['profile_revision'],first['profile_revision']),'(sss)')
        page=call('GetMemory',('toddy-default',),'(s)');assert all(r['id']!='language' for r in page['records'])
        clone=call('CloneProfile',('toddy-default',page['profile_revision'],'work'),'(sss)')
        assert call('GetMemory',('work',),'(s)')['records']==[]
        listed=call('ListProfiles');call('SelectProfile',('work',listed['generation']),'(st)')
        assert call('GetMemory',('toddy-default',),'(s)')['records'][0]['id']=='another'
        process.terminate();process.wait(timeout=8);process.stdout.close();process.stderr.close()
        process=start()
        assert call('GetMemory',('toddy-default',),'(s)')['records'][0]['id']=='another'
        assert call('GetMemory',('work',),'(s)')['records']==[]
        print(json.dumps({'scope':'host private bus/source/canonical SQLite only; no provider or guest acceptance',
            'owner_memory_crud':True,'sealed_fd_backup_tombstones':True,'profile_stage_cas':True,
            'profile_restore_keeps_memory':True,'clone_selection_restart_isolation':True,
            'seconds':round(time.monotonic()-started,3)}))
    finally:
        if process is not None:
            if process.poll() is None:process.terminate();process.wait(timeout=8)
            process.stdout.close();process.stderr.close()
