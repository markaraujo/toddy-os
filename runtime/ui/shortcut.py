"""Explicit per-user GNOME shortcut registration; never runs during import/startup."""
import gi
gi.require_version('Gtk','4.0')
from gi.repository import Gio, Gtk

MEDIA='org.gnome.settings-daemon.plugins.media-keys'
CUSTOM=MEDIA+'.custom-keybinding'
PATH='/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/toddy/'
COMMAND='/usr/bin/toddy'
NAME='Toddy'

class ShortcutError(ValueError):
    pass


def canonical(binding):
    if not isinstance(binding,str) or len(binding)>128:
        raise ShortcutError('invalid')
    valid,key,modifiers=Gtk.accelerator_parse(binding)
    if not valid or not Gtk.accelerator_valid(key,modifiers) or not modifiers:
        raise ShortcutError('invalid')
    return Gtk.accelerator_name(key,modifiers)


class Shortcut:
    def __init__(self,source=None):
        self.source=source or Gio.SettingsSchemaSource.get_default()
        if self.source is None:raise ShortcutError('unavailable')
        self.media=self.settings(MEDIA)
        self.own=self.settings(CUSTOM,PATH)

    def settings(self,schema_id,path=None):
        schema=self.source.lookup(schema_id,True)
        if schema is None:raise ShortcutError('unavailable')
        return Gio.Settings.new_full(schema,None,path)

    def _owned(self):
        return self.own.get_string('command')==COMMAND and self.own.get_string('name')==NAME

    def current(self):
        return self.own.get_string('binding') if PATH in self.media.get_strv('custom-keybindings') and self._owned() else ''

    def conflicts(self,binding):
        wanted=canonical(binding);found=[]
        ordinary,relocatable=self.source.list_schemas(True)
        ids=sorted(set(ordinary))
        # GNOME built-ins store accelerators in keybindings schemas and media-keys.
        # Scan installed schemas rather than assuming a frozen list of key names.
        for schema_id in ids:
            if '.keybindings' not in schema_id and schema_id!=MEDIA:continue
            settings=self.settings(schema_id)
            schema=self.source.lookup(schema_id,True)
            for key in schema.list_keys():
                if key=='custom-keybindings':continue
                value=settings.get_value(key)
                if value.get_type_string()=='as':values=value.unpack()
                elif value.get_type_string()=='s':values=[value.unpack()]
                else:continue
                for candidate in values:
                    try:match=canonical(candidate)==wanted
                    except ShortcutError:continue
                    if match:found.append(schema_id+':'+key)
        for path in self.media.get_strv('custom-keybindings'):
            if not path.startswith('/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/') or not path.endswith('/'):
                raise ShortcutError('unavailable')
            custom=self.settings(CUSTOM,path)
            if path==PATH and self._owned():continue
            try:match=canonical(custom.get_string('binding'))==wanted
            except ShortcutError:continue
            if match:found.append(path)
        return found

    def register(self,binding):
        binding=canonical(binding)
        paths=self.media.get_strv('custom-keybindings')
        if (PATH in paths or any(self.own.get_user_value(k) is not None for k in ('name','command','binding'))) and not self._owned():
            raise ShortcutError('occupied')
        if self.conflicts(binding):raise ShortcutError('conflict')
        if not self.media.is_writable('custom-keybindings') or any(not self.own.is_writable(k) for k in ('name','command','binding')):
            raise ShortcutError('locked')
        if self.media.get_strv('custom-keybindings')!=paths:raise ShortcutError('changed')
        self.own.delay()
        for key,value in (('name',NAME),('command',COMMAND),('binding',binding)):
            if not self.own.set_string(key,value):
                self.own.revert();raise ShortcutError('locked')
        self.own.apply()
        if PATH not in paths and not self.media.set_strv('custom-keybindings',paths+[PATH]):
            raise ShortcutError('locked')
        Gio.Settings.sync()
        if self.current()!=binding:raise ShortcutError('changed')
        return binding

    def remove(self):
        paths=self.media.get_strv('custom-keybindings')
        if not self._owned():raise ShortcutError('occupied')
        if not self.media.is_writable('custom-keybindings') or any(not self.own.is_writable(k) for k in ('name','command','binding')):
            raise ShortcutError('locked')
        if not self.media.set_strv('custom-keybindings',[p for p in paths if p!=PATH]):raise ShortcutError('locked')
        self.own.delay()
        for key in ('name','command','binding'):self.own.reset(key)
        self.own.apply();Gio.Settings.sync()
