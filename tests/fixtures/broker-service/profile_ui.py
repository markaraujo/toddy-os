#!/usr/bin/env python3
"""Actual host GTK/profile controls and broker/private files; no guest/model/root."""
import argparse
import json
import os
from pathlib import Path
import select
import subprocess
import sys
import tempfile
import time

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
os.environ.setdefault('GTK_USE_PORTAL','0');os.environ.setdefault('GIO_USE_VFS','local');os.environ.setdefault('GTK_A11Y','none')
import gi
gi.require_version('Gtk','4.0');gi.require_version('Adw','1')
from gi.repository import Gtk,Adw,Gio,GLib
from runtime.ui.app import ToddyApplication,SetupWindow
from runtime.ui.model import SetupModel

parser=argparse.ArgumentParser();parser.add_argument('--locale',default='en');args=parser.parse_args()
if os.getuid()==0:raise SystemExit('unprivileged_profile_UI_probe_required')
Gtk.init();Adw.init()
with tempfile.TemporaryDirectory(prefix='toddy-profile-UI-') as directory:
    base=Path(directory)
    process=subprocess.Popen([sys.executable,str(ROOT/'runtime/broker/service.py'),
        '--data-dir',str(base/'legacy'),'--workspace',str(base/'workspace'),
        '--defaults',str(ROOT/'config/phase2')],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    if not select.select([process.stdout],[],[],8)[0] or process.stdout.readline()!=b'READY\n':
        process.terminate();process.wait(timeout=5);raise AssertionError('broker_not_ready')
    model=SetupModel(ROOT,base/'setup',args.locale)
    app=ToddyApplication(model);app.register(None)
    window=SetupWindow(app,model);client=window.client
    loop=GLib.MainLoop();stage=0;outcome={};started=time.monotonic();counts={'SubmitTask':0,'LookupRequest':0}
    export=base/'private-profile.json'
    original_call=client._call
    lost={}
    def call(method,parameters,completed,failed=None):
        if method in counts:counts[method]+=1
        if method=='SubmitTask':
            lost['request']=dict(client.pending_request)
            def drop(data):
                lost['task_id']=data
                raise ValueError('intentional_lost_acceptance_reply')
            return original_call(method,parameters,drop,failed)
        return original_call(method,parameters,completed,failed)
    client._call=call
    def choose(profile_id):
        window.profile_picker.set_selected([row['id'] for row in window.registry_rows].index(profile_id))
    def ids():return {row['id'] for row in (client.profile_list or {}).get('profiles',[])}
    def poll():
        global stage
        try:
            if stage==0 and client.phase=='ready' and client.profile_list is not None:
                assert not window.entry.get_sensitive()
                stage=1;window.new_profile_id.set_text('work');window.profile_create.emit('clicked')
            elif stage==1 and 'work' in ids() and not client.profile_mutating:
                assert client.profile_list['active_profile_id']=='toddy-default'
                stage=2;choose('work');window.profile_use.emit('clicked')
            elif stage==2 and client.capabilities['profile_id']=='work' and client.profile_list['active_profile_id']=='work':
                stage=3;window.new_profile_id.set_text('clone');choose('work');window.profile_clone.emit('clicked')
            elif stage==3 and 'clone' in ids() and not client.profile_mutating:
                assert client.profile_list['active_profile_id']=='work'
                stage=4;chosen=next(row for row in client.profile_list['profiles'] if row['id']=='work')
                window._export_to(export,'work',chosen['revision'])
            elif stage==4 and export.is_file() and client.profile_action_status=='exported':
                assert export.stat().st_mode&0o777==0o600
                bundle=json.loads(export.read_bytes())
                assert bundle['routing']=='deferred-rebind-required'
                stage=5;window._import_from(export,'imported')
            elif stage==5 and 'imported' in ids() and not client.profile_mutating:
                assert client.profile_list['active_profile_id']=='work'
                stage=6;choose('imported');window.profile_use.emit('clicked')
            elif stage==6 and client.capabilities['profile_id']=='imported' and client.profile_list['active_profile_id']=='imported':
                stage=7;window.run_button.emit('clicked')
            elif stage==7 and client.state.acceptance_uncertain:
                assert counts['SubmitTask']==1
                stage=8;client.recheck()
            elif stage==8 and client.acceptance_lookup=='found' and client.state.snapshot and client.state.snapshot['state']=='completed':
                assert client.state.task_id==lost['task_id']
                assert client.task_profile_id=='imported'
                assert counts['SubmitTask']==1 and counts['LookupRequest']==1
                assert not client.state.acceptance_uncertain
                assert 'gi.repository.Secret' not in sys.modules
                outcome.update(status='passed',scope='actual-host-GTK-and-broker-private-bus-not-guest-model-root',
                    locale=args.locale,create_clone_select=True,sealed_FD_file_export_import=True,
                    lost_reply_readonly_lookup_no_resubmit=True,counts=counts,
                    seconds=round(time.monotonic()-started,3))
                loop.quit();return False
        except Exception as exc:
            outcome.update(status='failed',stage=stage,reason=type(exc).__name__,counts=counts)
            loop.quit();return False
        return True
    def timeout():
        outcome.update(status='failed',reason='deadline',stage=stage,phase=client.phase,counts=counts)
        loop.quit();return False
    GLib.timeout_add(10,poll);GLib.timeout_add(10000,timeout)
    try:loop.run()
    finally:
        window._close();window.destroy();model.close()
        if process.poll() is None:process.terminate();process.wait(timeout=8)
        process.stdout.close();process.stderr.close()
    print(json.dumps(outcome,sort_keys=True))
    raise SystemExit(0 if outcome.get('status')=='passed' else 1)
