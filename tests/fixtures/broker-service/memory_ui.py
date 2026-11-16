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
    panel=window.memory
    loop=GLib.MainLoop();stage=0;outcome={};started=time.monotonic()
    backup=base/'private-memory.json'
    def poll():
        global stage
        try:
            if stage==0 and client.phase=='ready' and client.profile_list is not None:
                assert 'owner-memory-v1' in client.capabilities['features']
                stage=1;panel.inspect.emit('clicked')
            elif stage==1 and panel.snapshot is not None and not panel.busy:
                assert panel.snapshot['profile_id']=='toddy-default' and not panel.rows
                panel.record_id.set_text('language');panel.buffer.set_text('Português literal <b>plain</b>')
                stage=2;panel.controls['put'].emit('clicked')
            elif stage==2 and panel.snapshot and not panel.busy and panel.rows:
                assert panel.rows[0]['text']=='Português literal <b>plain</b>'
                stage=3;panel.transfer(backup)
            elif stage==3 and backup.is_file() and not panel.busy:
                assert backup.stat().st_mode&0o777==0o600
                stage=4;panel.controls['delete'].emit('clicked')
            elif stage==4 and panel.snapshot and not panel.rows and not panel.busy:
                assert not panel.controls['restore'].get_sensitive()
                panel.restore_consent.set_active(True)
                stage=5;panel.transfer(backup,True)
            elif stage==5 and panel.snapshot and not panel.busy and not panel.restore_consent.get_active():
                assert not panel.rows, 'old-backup-resurrected-deleted-preference'
                stage=6;window.new_profile_id.set_text('memory-other');window.profile_create.emit('clicked')
            elif stage==6 and any(row['id']=='memory-other' for row in (client.profile_list or {}).get('profiles',[])) and not client.profile_mutating:
                window.profile_picker.set_selected([row['id'] for row in window.registry_rows].index('memory-other'))
                stage=7;window.profile_use.emit('clicked')
            elif stage==7 and client.capabilities and client.capabilities['profile_id']=='memory-other':
                assert panel.snapshot is None and not panel.record_id.get_text()
                stage=8;panel.inspect.emit('clicked')
            elif stage==8 and panel.snapshot and panel.snapshot['profile_id']=='memory-other' and not panel.busy:
                assert not panel.rows
                assert 'gi.repository.Secret' not in sys.modules
                outcome.update(status='passed',locale=args.locale,scope='actual-host-GTK-broker-private-bus-not-guest-model-root',
                               inspect_put_delete=True,sealed_private_export_explicit_restore=True,deletion_survives_old_backup=True,
                               selected_profile_isolation=True,seconds=round(time.monotonic()-started,3))
                loop.quit();return False
            if time.monotonic()-started>12:raise AssertionError('memory_UI_timeout_stage_'+str(stage)+'_'+panel.status.get_text()+' busy='+str(panel.busy)+' snapshot='+str(panel.snapshot is not None)+' phase='+client.phase+' rows='+str(len(panel.rows)))
        except BaseException as error:
            outcome.update(status='failed',stage=stage,error=repr(error));loop.quit();return False
        return True
    GLib.timeout_add(10,poll)
    try:loop.run()
    finally:
        window._close();window.destroy();process.terminate();process.wait(timeout=5)
    print(json.dumps(outcome,sort_keys=True))
    if outcome.get('status')!='passed':raise SystemExit(1)
