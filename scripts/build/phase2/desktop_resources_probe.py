"""Native desktop schemas, actual icon lookup/SVG decode and cursor data."""
import json
from pathlib import Path
import sys
import gi

gi.require_version('Gtk','4.0');gi.require_version('GdkPixbuf','2.0');gi.require_version('GDesktopEnums','3.0')
from gi.repository import Gtk,Gio,GdkPixbuf,GDesktopEnums

root=Path(sys.argv[1]);schemas=Path(sys.argv[2]);icons=Path(sys.argv[3])
source=Gio.SettingsSchemaSource.new_from_directory(str(schemas),None,False)
ids=source.list_schemas(False)[0]
for name in ['org.gnome.desktop.interface','org.gnome.desktop.background','org.gnome.desktop.input-sources','org.gtk.gtk4.Settings.FileChooser']:
    assert source.lookup(name,False),name
interface=source.lookup('org.gnome.desktop.interface',False)
font=interface.get_key('font-name').get_default_value().unpack()
mono=interface.get_key('monospace-font-name').get_default_value().unpack()
assert font=='Adwaita Sans 11' and mono=='Adwaita Mono 11'
assert int(GDesktopEnums.BackgroundStyle.ZOOM)==5  # Frozen gdesktop-enums.h plain C enum.
theme=Gtk.IconTheme.new();theme.set_search_path([str(icons)]);theme.set_theme_name('Adwaita')
assert theme.has_icon('folder-symbolic') and theme.has_icon('document-open-symbolic')
folder=icons/'Adwaita/scalable/places/folder.svg'
image=GdkPixbuf.Pixbuf.new_from_file_at_scale(str(folder),32,32,True)
assert image.get_width()==image.get_height()==32
ok,png=image.save_to_bufferv('png',[],[]);assert ok and bytes(png).startswith(b'\x89PNG')
cursor=icons/'Adwaita/cursors/default';assert cursor.read_bytes()[:4]==b'Xcur'
result={'scope':'Native schema/default-font/GI enum/icon lookup/SVG pixels/cursor data; no window/session/pointer interaction acceptance',
        'schemas':len(ids),'font_default':font,'monospace_default':mono,'enum_zoom':int(GDesktopEnums.BackgroundStyle.ZOOM),
        'icon_names':['folder-symbolic','document-open-symbolic'],'svg_size':[32,32],'png_bytes':len(png),'cursor_magic':'Xcur'}
print(json.dumps(result))
