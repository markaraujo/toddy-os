"""Native session binaries and private schema only, never a graphical session claim."""
from pathlib import Path
import json,subprocess,sys
from gi.repository import Gio
p=Path(sys.argv[1]);schemas=Path(sys.argv[2]);runs=[]
assert (p/'usr/libexec/gnome-session-init-worker').is_file() # Positional worker, no --help API; actual session gate later
for name in ['usr/bin/gnome-session','usr/bin/gnome-session-inhibit','usr/bin/gnome-session-quit','usr/libexec/gnome-session-ctl','usr/libexec/gnome-session-service']:
 r=subprocess.run([str(p/name),'--help'],capture_output=True,text=True,timeout=10,check=True);assert 'Usage:' in r.stdout
 runs.append({'name':name,'help_exit':0})
r=subprocess.run([str(p/'usr/bin/gnome-session'),'--version'],capture_output=True,text=True,timeout=10,check=True);assert r.stdout.strip().endswith(' 50.1')
r=subprocess.run([str(p/'usr/bin/gnome-session'),'--toddy-invalid-option'],capture_output=True,text=True,timeout=10);assert r.returncode!=0 and 'Unknown option' in r.stderr
schema=Gio.SettingsSchemaSource.new_from_directory(str(schemas),None,False).lookup('org.gnome.SessionManager',False);assert schema is not None
assert set(schema.list_keys())=={'logout-prompt','show-fallback-warning'} and all(schema.get_key(k).get_default_value().unpack() is True for k in schema.list_keys())
assert (p/'usr/lib/systemd/user/gnome-session@.target').is_file()
assert (p/'usr/share/wayland-sessions/gnome.desktop').is_file()
print(json.dumps({'version':'50.1','help_runs':runs,'invalid_option_refused':True,'private_schema_default_true_keys':sorted(schema.list_keys()),'wayland_session_and_systemd_target':True,'scope':'CLI/private schema/layout only; no actual SessionManager/login/desktop acceptance'}))
