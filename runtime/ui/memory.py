"""Bounded explicit-owner memory controls over authenticated Service1 only."""
import fcntl
import json
import os
from pathlib import Path
import re

import gi
gi.require_version('Gtk','4.0')
from gi.repository import Gio,GLib,Gtk
from .bridge import OBJECT,INTERFACE
from .model import open_profile_import,save_profile_export
from .task_state import body,REVISION


def sealed_local_backup(path):
    source=open_profile_import(path)
    target=os.memfd_create('toddy-owner-memory-restore',os.MFD_CLOEXEC|os.MFD_ALLOW_SEALING)
    try:
        os.fchmod(target,0o600)
        size=os.fstat(source).st_size
        data=os.pread(source,8*1024*1024+1,0)
        if len(data)!=size:raise ValueError('memory_backup_changed')
        view=memoryview(data)
        while view:view=view[os.write(target,view):]
        fcntl.fcntl(target,fcntl.F_ADD_SEALS,fcntl.F_SEAL_SEAL|fcntl.F_SEAL_WRITE|fcntl.F_SEAL_GROW|fcntl.F_SEAL_SHRINK)
        result=os.open('/proc/self/fd/'+str(target),os.O_RDONLY|os.O_CLOEXEC)
        return result
    finally:
        os.close(source);os.close(target)


def page(encoded,profile):
    value=body(encoded,49152)
    if value.get('profile_id')!=profile or not isinstance(value.get('profile_revision'),str) or not REVISION.fullmatch(value['profile_revision']) or \
            type(value.get('memory_generation')) is not int or not 0<=value['memory_generation']<2**53 or \
            not isinstance(value.get('records'),list) or len(value['records'])>32 or \
            type(value.get('complete')) is not bool or type(value.get('user_document_review_required')) is not bool or \
            not isinstance(value.get('next_cursor'),str) or len(value['next_cursor'])>128:
        raise ValueError('invalid_memory_page')
    seen=set()
    for row in value['records']:
        if not isinstance(row,dict) or not isinstance(row.get('id'),str) or not re.fullmatch(r'[a-z][a-z0-9-]{0,63}',row['id']) or \
                row['id'] in seen or not isinstance(row.get('text'),str) or len(row['text'].encode('utf-8'))>4096 or \
                row.get('kind') not in ('document','preference') or \
                any(not isinstance(row.get(key),str) or len(row[key])>512 for key in ('source_kind','source_ref','source_revision')):
            raise ValueError('invalid_memory_record')
        seen.add(row['id'])
    return value


class MemoryPanel(Gtk.Box):
    def __init__(self,window):
        super().__init__(orientation=Gtk.Orientation.VERTICAL,spacing=12)
        self.window=window;self.text=window.model.text;self.identity=None;self.snapshot=None
        self.busy=False;self.rows=[];self.serial=0;self.rendering=False;self.reload_pending=False
        self.append(window._label(self.text('memory.notice')))
        self.status=window._label(self.text('memory.unavailable'));self.append(self.status)
        self.inspect=Gtk.Button(label=self.text('memory.inspect'));self.inspect.connect('clicked',lambda *_:self.load());self.append(self.inspect)
        self.picker=Gtk.DropDown.new_from_strings([]);self.picker.connect('notify::selected',self.choose);self.append(self.picker)
        self.provenance=window._label('');self.append(self.provenance)
        self.record_id=Gtk.Entry(placeholder_text=self.text('memory.record_id'),max_length=128);self.append(self.record_id)
        self.editor=Gtk.TextView(wrap_mode=Gtk.WrapMode.WORD_CHAR)
        self.buffer=self.editor.get_buffer()
        scroll=Gtk.ScrolledWindow(min_content_height=120,max_content_height=240);scroll.set_child(self.editor);self.append(scroll)
        self.controls={}
        actions=(('put',lambda *_:self.mutate('put')),('delete',lambda *_:self.mutate('delete')),
                 ('next',lambda *_:self.load(next_page=True)),('export',lambda *_:self.file_action(False)),
                 ('restore',lambda *_:self.file_action(True)))
        for name,callback in actions:
            button=Gtk.Button(label=self.text('memory.'+name));button.connect('clicked',callback)
            self.controls[name]=button;self.append(button)
        self.restore_consent=Gtk.CheckButton(label=self.text('memory.restore_consent'));self.append(self.restore_consent)
        self.restore_consent.connect('toggled',lambda *_:self.sensitivity())
        self.sensitivity()

    def sync(self):
        client=self.window.client
        identity=(client.generation,(client.capabilities or {}).get('profile_id'))
        if identity!=self.identity:
            self.identity=identity;self.serial+=1;self.snapshot=None;self.rows=[];self.busy=False;self.reload_pending=False
            self.picker.set_model(Gtk.StringList.new([]));self.buffer.set_text('');self.record_id.set_text('');self.provenance.set_text('')
            self.restore_consent.set_active(False);self.status.set_text(self.text('memory.unavailable'))
        self.sensitivity()
        if self.reload_pending and self.available() and not self.busy:
            self.reload_pending=False
            GLib.idle_add(lambda:(self.load(),False)[1])

    def available(self):
        client=getattr(self.window,'client',None)
        return client is not None and client.phase=='ready' and 'owner-memory-v1' in (client.capabilities or {}).get('features',[])

    def sensitivity(self):
        ready=self.available() and not self.busy
        self.inspect.set_sensitive(ready)
        if not hasattr(self,'controls'):return
        loaded=ready and self.snapshot is not None
        self.picker.set_sensitive(loaded);self.record_id.set_sensitive(loaded);self.editor.set_editable(loaded)
        for name,button in self.controls.items():button.set_sensitive(loaded)
        self.controls['next'].set_sensitive(loaded and not self.snapshot['complete'])
        self.controls['restore'].set_sensitive(loaded and self.restore_consent.get_active())

    def choose(self,*_):
        index=self.picker.get_selected()
        if self.rendering or index>=len(self.rows):return
        row=self.rows[index];self.record_id.set_text(row['id']);self.buffer.set_text(row['text'])
        self.provenance.set_text(self.text('memory.provenance').format(kind=row['source_kind'],source=row['source_ref']))

    def failed(self,_code=None):
        self.busy=False;self.snapshot=None;self.status.set_text(self.text('memory.failed'));self.sensitivity()

    def load(self,next_page=False):
        self.sync()
        if not self.available() or self.busy:return
        client=self.window.client;profile=client.capabilities['profile_id'];serial=self.serial
        cursor=self.snapshot['next_cursor'] if next_page and self.snapshot else ''
        previous=self.snapshot
        self.busy=True;self.status.set_text(self.text('memory.loading'));self.sensitivity()
        def received(data):
            if serial!=self.serial:return
            value=page(data,profile)
            if cursor and previous and (value['profile_revision'],value['memory_generation'])!=(previous['profile_revision'],previous['memory_generation']):
                raise ValueError('memory_page_changed')
            self.snapshot=value;self.rows=value['records'];self.busy=False
            self.rendering=True;self.picker.set_model(Gtk.StringList.new([row['id'] for row in self.rows]));self.rendering=False
            self.buffer.set_text('');self.record_id.set_text('');self.provenance.set_text('')
            if self.rows:self.picker.set_selected(0);self.choose()
            self.status.set_text(self.text('memory.review_required' if value['user_document_review_required'] else 'memory.loaded'))
            self.sensitivity()
        client._call('ListMemory',GLib.Variant('(ssu)',(profile,cursor,16)),received,
                     lambda code:self.failed(code) if serial==self.serial else None)

    def mutate(self,operation):
        if not self.available() or self.busy or self.snapshot is None:return
        snapshot=self.snapshot;serial=self.serial
        value={'version':1,'memory_generation':snapshot['memory_generation'],'operation':operation,'id':self.record_id.get_text()}
        if operation=='put':
            value.update(text=self.buffer.get_text(self.buffer.get_start_iter(),self.buffer.get_end_iter(),True),expires=None)
            if len(value['text'].encode('utf-8'))>4096:self.failed();return
        self.busy=True;self.status.set_text(self.text('memory.loading'));self.sensitivity()
        def received(data):
            if serial!=self.serial:return
            result=body(data,49152)
            if result.get('profile_id')!=snapshot['profile_id']:raise ValueError('memory_profile_mismatch')
            self.busy=False;self.snapshot=None;self.reload_pending=True;self.window.client.recheck()
        self.window.client._call('MutateMemory',GLib.Variant('(sss)',(snapshot['profile_id'],snapshot['profile_revision'],json.dumps(value))),
                                received,lambda code:self.failed(code) if serial==self.serial else None)

    def transfer(self,path,restore=False,expected=None):
        if not self.available() or self.busy or self.snapshot is None:return
        snapshot=self.snapshot
        if expected is not None and expected!=snapshot:raise ValueError('memory_selection_changed')
        client=self.window.client;serial=self.serial;generation=client.generation
        incoming=None;descriptor=None
        if restore:
            if not self.restore_consent.get_active():raise ValueError('memory_restore_consent')
            descriptor=sealed_local_backup(path)
            incoming=Gio.UnixFDList.new();index=incoming.append(descriptor);os.close(descriptor)
            parameters=GLib.Variant('(ssth)',(snapshot['profile_id'],snapshot['profile_revision'],snapshot['memory_generation'],index))
            method='RestoreMemory';reply='(s)'
        else:
            parameters=GLib.Variant('(sst)',(snapshot['profile_id'],snapshot['profile_revision'],snapshot['memory_generation']))
            method='ExportMemory';reply='(h)'
        self.busy=True;self.status.set_text(self.text('memory.loading'));self.sensitivity()
        cancel=Gio.Cancellable();client.pending.add(cancel)
        def finished(conn,result,*_):
            client.pending.discard(cancel)
            try:
                value,descriptors=conn.call_with_unix_fd_list_finish(result)
                if serial!=self.serial or generation!=client.generation:return
                if restore:
                    returned=body(value.unpack()[0],49152)
                    if returned.get('profile_id')!=snapshot['profile_id']:raise ValueError('memory_profile_mismatch')
                    self.restore_consent.set_active(False);self.busy=False;self.snapshot=None;self.reload_pending=True;client.recheck()
                else:
                    if descriptors is None or descriptors.get_length()!=1:raise ValueError('memory_export_fd')
                    descriptor=descriptors.get(value.unpack()[0])
                    try:save_profile_export(descriptor,path)
                    finally:os.close(descriptor)
                    self.busy=False;self.status.set_text(self.text('memory.exported'));self.sensitivity()
            except (GLib.Error,ValueError,TypeError,OSError):
                if serial==self.serial:self.failed()
        try:
            client.connection.call_with_unix_fd_list(client.owner,OBJECT,INTERFACE,method,parameters,
                GLib.VariantType(reply),Gio.DBusCallFlags.NO_AUTO_START,5000,incoming,cancel,finished,None)
        except (GLib.Error,ValueError,TypeError,OSError):
            client.pending.discard(cancel);self.failed()

    def file_action(self,restore):
        if self.snapshot is None:return
        expected=dict(self.snapshot);key='memory.restore' if restore else 'memory.export'
        chooser=Gtk.FileChooserNative.new(self.text(key),self.window,Gtk.FileChooserAction.OPEN if restore else Gtk.FileChooserAction.SAVE,
                                         self.text(key),self.text('profile.file_cancel'))
        if not restore:chooser.set_current_name(expected['profile_id']+'.toddy-memory.json')
        def selected(dialog,response):
            try:
                if response==Gtk.ResponseType.ACCEPT:
                    path=dialog.get_file().get_path()
                    if path is None:raise ValueError('local_file_required')
                    self.transfer(Path(path),restore,expected)
            except (ValueError,OSError):self.failed()
            finally:dialog.destroy()
        chooser.connect('response',selected);chooser.show()
