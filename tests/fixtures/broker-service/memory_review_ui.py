#!/usr/bin/env python3
"""Actual host GTK/profile controls and broker/private files; no guest/model/root."""
import argparse
import json
import os
from pathlib import Path
import select
import shutil
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
    defaults=base/'defaults';shutil.copytree(ROOT/'config/phase2',defaults)
    raw='Private manual notes <b>literal</b>\nPrefer Portuguese, only after owner review.\n'
    (defaults/'profile/USER.md').write_text(raw)
    process=subprocess.Popen([sys.executable,str(ROOT/'runtime/broker/service.py'),
        '--data-dir',str(base/'legacy'),'--workspace',str(base/'workspace'),
        '--defaults',str(defaults)],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    if not select.select([process.stdout],[],[],8)[0] or process.stdout.readline()!=b'READY\n':
        process.terminate();process.wait(timeout=5);raise AssertionError('broker_not_ready')
    model=SetupModel(ROOT,base/'setup',args.locale)
    app=ToddyApplication(model);app.register(None)
    window=SetupWindow(app,model);client=window.client
    panel=window.memory
    loop=GLib.MainLoop();stage=0;outcome={};started=time.monotonic();writes=[]
    original=client._call
    def counted(method,parameters,completed,failed=None):
        if method=='MutateMemory':writes.append(parameters.unpack())
        return original(method,parameters,completed,failed)
    client._call=counted
    def poll():
        global stage
        try:
            if stage==0 and client.phase=='ready' and client.profile_list is not None:
                stage=1;panel.inspect.emit('clicked')
            elif stage==1 and panel.snapshot and not panel.busy:
                assert panel.snapshot['user_document_review_required'] and not panel.rows
                assert not panel.review_apply.get_sensitive() and not writes
                stage=2;panel.document_read.emit('clicked')
            elif stage==2 and panel.reviewed is not None and not panel.busy:
                assert panel.document_buffer.get_text(panel.document_buffer.get_start_iter(),panel.document_buffer.get_end_iter(),True)==raw
                assert not panel.review_consent.get_active() and not panel.review_apply.get_sensitive() and not writes
                panel.preferences_buffer.set_text('invalid JSON');panel.review_consent.set_active(True)
                panel.review_apply.emit('clicked');assert not writes
                panel.preferences_buffer.set_text('{"language":"Português escolhido pelo dono"}')
                stage=3;panel.review_apply.emit('clicked')
            elif stage==3 and panel.snapshot and panel.rows and not panel.busy:
                assert len(writes)==1
                sent=json.loads(writes[0][2])
                assert sent['operation']=='review-user-document' and sent['reviewed_user_sha256']
                assert panel.rows[0]['text']=='Português escolhido pelo dono' and panel.rows[0]['source_kind']=='user-md'
                assert not panel.snapshot['user_document_review_required'] and panel.reviewed is None
                assert not panel.review_consent.get_active() and not panel.document_buffer.get_char_count()
                stage=4;window.new_profile_id.set_text('review-other');window.profile_create.emit('clicked')
            elif stage==4 and any(row['id']=='review-other' for row in (client.profile_list or {}).get('profiles',[])) and not client.profile_mutating:
                window.profile_picker.set_selected([row['id'] for row in window.registry_rows].index('review-other'))
                stage=5;window.profile_use.emit('clicked')
            elif stage==5 and client.capabilities and client.capabilities['profile_id']=='review-other':
                assert panel.snapshot is None and panel.reviewed is None and not panel.document_buffer.get_char_count()
                assert len(writes)==1 and 'gi.repository.Secret' not in sys.modules
                outcome.update(status='passed',locale=args.locale,scope='actual-host-GTK-broker-private-bus-not-guest-model-root',
                               manual_notes_shown_plain_readonly=True,no_read_conversion=True,invalid_json_no_write=True,
                               explicit_hash_revision_generation_bound_conversion=True,profile_switch_clears_private_review=True,
                               seconds=round(time.monotonic()-started,3))
                loop.quit();return False
            if time.monotonic()-started>12:raise AssertionError('review_UI_timeout_stage_'+str(stage)+'_'+panel.status.get_text())
        except BaseException as error:
            outcome.update(status='failed',stage=stage,error=repr(error));loop.quit();return False
        return True
    GLib.timeout_add(10,poll)
    try:loop.run()
    finally:
        window._close();window.destroy();process.terminate();process.wait(timeout=5)
    print(json.dumps(outcome,sort_keys=True))
    if outcome.get('status')!='passed':raise SystemExit(1)
