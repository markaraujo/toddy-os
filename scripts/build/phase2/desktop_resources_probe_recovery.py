from pathlib import Path
import hashlib,json,os,subprocess
assert os.getuid()==101
root=Path('/build/resources');output=root/'recovery-2';output.mkdir()
def stages():
 result={}
 for p in Path('/stage').rglob('*'):
  if p.is_symlink():result[str(p.relative_to('/stage'))]={'link':os.readlink(p)}
  elif p.is_file():
   with p.open('rb') as f:result[str(p.relative_to('/stage'))]={'sha256':hashlib.file_digest(f,'sha256').hexdigest()}
 return result
before=stages();assert before
(output/'stage-before.json').write_text(json.dumps(before,indent=2)+'\n')
assert 'has no attribute' in (root/'logs/desktop-resources-consumer.log').read_text()
probe='"""Native desktop schemas, actual icon lookup/SVG decode and cursor data."""\nimport json\nfrom pathlib import Path\nimport sys\nimport gi\n\ngi.require_version(\'Gtk\',\'4.0\');gi.require_version(\'GdkPixbuf\',\'2.0\');gi.require_version(\'GDesktopEnums\',\'3.0\')\nfrom gi.repository import Gtk,Gio,GdkPixbuf,GDesktopEnums\n\nroot=Path(sys.argv[1]);schemas=Path(sys.argv[2]);icons=Path(sys.argv[3])\nsource=Gio.SettingsSchemaSource.new_from_directory(str(schemas),None,False)\nids=source.list_schemas(False)[0]\nfor name in [\'org.gnome.desktop.interface\',\'org.gnome.desktop.background\',\'org.gnome.desktop.input-sources\',\'org.gtk.gtk4.Settings.FileChooser\']:\n    assert source.lookup(name,False),name\ninterface=source.lookup(\'org.gnome.desktop.interface\',False)\nfont=interface.get_key(\'font-name\').get_default_value().unpack()\nmono=interface.get_key(\'monospace-font-name\').get_default_value().unpack()\nassert font==\'Adwaita Sans 11\' and mono==\'Adwaita Mono 11\'\nassert int(GDesktopEnums.BackgroundStyle.ZOOM)==5  # Frozen gdesktop-enums.h plain C enum.\ntheme=Gtk.IconTheme.new();theme.set_search_path([str(icons)]);theme.set_theme_name(\'Adwaita\')\nassert theme.has_icon(\'folder-symbolic\') and theme.has_icon(\'document-open-symbolic\')\nfolder=icons/\'Adwaita/scalable/places/folder.svg\'\nimage=GdkPixbuf.Pixbuf.new_from_file_at_scale(str(folder),32,32,True)\nassert image.get_width()==image.get_height()==32\nok,png=image.save_to_bufferv(\'png\',[],[]);assert ok and bytes(png).startswith(b\'\\x89PNG\')\ncursor=icons/\'Adwaita/cursors/default\';assert cursor.read_bytes()[:4]==b\'Xcur\'\nresult={\'scope\':\'Native schema/default-font/GI enum/icon lookup/SVG pixels/cursor data; no window/session/pointer interaction acceptance\',\n        \'schemas\':len(ids),\'font_default\':font,\'monospace_default\':mono,\'enum_zoom\':int(GDesktopEnums.BackgroundStyle.ZOOM),\n        \'icon_names\':[\'folder-symbolic\',\'document-open-symbolic\'],\'svg_size\':[32,32],\'png_bytes\':len(png),\'cursor_magic\':\'Xcur\'}\nprint(json.dumps(result))\n'

with (output/'consumer.log').open('xb') as log:
 r=subprocess.run(['python3','-c',probe,'/stage',str(root/'schema-union'),str(root/'icon-union')],env=dict(os.environ,GI_TYPELIB_PATH='/stage/gsettings-desktop-schemas/usr/lib/girepository-1.0'),stdout=log,stderr=subprocess.STDOUT)
(output/'consumer.exit').write_text(str(r.returncode)+'\n');assert r.returncode==0
assert stages()==before
(output/'qualified.json').write_text(json.dumps({'scope':'Probe-only plain C enum invocation correction; original three package stages/caches retained','native_exit':0,'stage_files_unchanged':len(before),'consumer':json.loads((output/'consumer.log').read_text())},indent=2)+'\n')
