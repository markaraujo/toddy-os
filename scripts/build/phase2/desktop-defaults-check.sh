#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import json,os,subprocess,tempfile
T=Path('/mnt/lfs')
assert subprocess.check_output(['chroot',str(T),'dpkg-query','-W','-f=${Status} ${Version}','toddy-desktop-defaults'],text=True)=='install ok installed 0.2.0-1+toddy1'
code='''import json,sys
from gi.repository import Gio
assert Gio.SettingsBackend.get_default().__gtype__.name=='DConfSettingsBackend'
b=Gio.Settings.new('org.gnome.desktop.background');i=Gio.Settings.new('org.gnome.desktop.interface')
p=Gio.Settings.new_with_path('org.gnome.Terminal.Legacy.Profile','/org/gnome/terminal/legacy/profiles:/:b1dcc9dd-5262-4d8d-a863-c897e6d979b9/')
assert b.is_writable('primary-color') and p.is_writable('background-color')
if sys.argv[1]=='write':
 assert b.get_string('primary-color')=='#081b33' and b.get_string('picture-uri')==''
 assert i.get_string('color-scheme')=='prefer-dark'
 assert p.get_string('background-color')=='#081b33' and p.get_string('foreground-color')=='#f4f7fb' and not p.get_boolean('use-theme-colors')
 assert p.get_boolean('use-system-font')
 assert Gio.Settings.new('org.gnome.shell').get_strv('favorite-apps')==['org.gnome.Nautilus.desktop','firefox.desktop','org.gnome.Terminal.desktop','org.gnome.TextEditor.desktop','org.gnome.Settings.desktop']
 assert b.set_string('primary-color','#123456') and p.set_string('background-color','#654321');Gio.Settings.sync()
else:
 assert b.get_string('primary-color')=='#123456' and p.get_string('background-color')=='#654321'
 b.reset('primary-color');p.reset('background-color');Gio.Settings.sync()
 assert b.get_string('primary-color')=='#081b33' and p.get_string('background-color')=='#081b33'
print(json.dumps({'cycle':sys.argv[1],'defaults_or_persisted_user_override_verified':True,'writable_without_locks':True,'system_font_preserved':True}))
'''
rows=[]
with tempfile.TemporaryDirectory(prefix='toddy-desktop-defaults-',dir=T/'var/tmp') as directory:
 home=Path(directory);os.chown(home,101,101);virtual='/var/tmp/'+home.name
 for n in ['config','runtime']:(home/n).mkdir(mode=0o700);os.chown(home/n,101,101)
 env={'HOME':virtual,'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','XDG_CONFIG_HOME':virtual+'/config','XDG_RUNTIME_DIR':virtual+'/runtime','GSETTINGS_BACKEND':'dconf','DCONF_PROFILE':'user','PYTHONDONTWRITEBYTECODE':'1'}
 for mode in ['write','read']:
  r=subprocess.run(['setpriv','--no-new-privs','chroot','--userspec=101:101','--groups=101',str(T),'dbus-run-session','--','python3','-c',code,mode],env=env,capture_output=True,text=True,timeout=30)
  assert r.returncode==0,(mode,r.stdout,r.stderr);rows.append(json.loads(r.stdout))
subprocess.run(['chroot',str(T),'apt-get','check'],check=True)
assert not subprocess.check_output(['chroot',str(T),'dpkg','--audit'],text=True).strip()
Path('/var/log/toddy/phase2/desktop-defaults-consumer.json').write_text(json.dumps({'scope':'Actual installed dconf UID101/NNP typed settings/default values, writable preference override across two buses/reset. Native graphical rendering still pending.','cycles':rows},indent=2)+'\n')
PY
