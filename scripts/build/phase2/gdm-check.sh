#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import configparser,hashlib,json,shutil,stat,subprocess,tempfile
T=Path('/mnt/lfs');prefix=['chroot',str(T)];env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':'/tmp','PYTHONDONTWRITEBYTECODE':'1'}
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','gdm'],text=True)=='install ok installed 50.2-1+toddy1'
assert subprocess.check_output(prefix+['pkg-config','--modversion','gdm'],text=True).strip()=='50.2'
assert not subprocess.check_output(prefix+['dpkg','--audit'],text=True).strip();subprocess.run(prefix+['apt-get','check'],check=True)
w=T/'sources/phase2/work/gdm-1';expected=json.loads((w/'stage-results.json').read_text())['consumer'];assert not (T/'stage').exists()
with tempfile.TemporaryDirectory(prefix='toddy-GDM-',dir=T/'tmp') as directory:
 p=Path(directory);p.chmod(0o755);shutil.copyfile(w/'native-probe',p/'probe');(p/'probe').chmod(0o755)
 assert hashlib.sha256((p/'probe').read_bytes()).digest()==hashlib.sha256((w/'native-probe').read_bytes()).digest()
 native='/tmp/'+p.name+'/probe';libs=subprocess.check_output(prefix+['ldd',native],text=True,env=env);assert 'libgdm.so.1 => /usr/lib/libgdm.so.1' in libs
 actual=json.loads(subprocess.check_output(['chroot','--userspec=101:101',str(T),native],env=env,text=True,timeout=20));assert actual==expected
assert subprocess.check_output(prefix+['gdm','--version'],env=env,text=True).strip()=='GDM 50.2'
code="""import gi,json
gi.require_version('Gdm','1.0')
from gi.repository import Gdm
c=Gdm.Client.new();expected=['org.gnome.DisplayManager.UserVerifier.ChoiceList','org.gnome.DisplayManager.UserVerifier.CustomJSON']
c.set_enabled_extensions(expected);assert c.get_enabled_extensions()==expected
print(json.dumps({'namespace':'Gdm1.0','actual_client_extensions':True}))
"""
gi=json.loads(subprocess.check_output(prefix+['python3','-c',code],env=env,text=True,timeout=20))
g=next(s.split(':') for s in (T/'etc/group').read_text().splitlines() if s.startswith('gdm:'));assert g[2]=='21'
assert not any(s.startswith('gdm:') for s in (T/'etc/passwd').read_text().splitlines())
assert (T/'usr/lib/sysusers.d/gdm.conf').read_text()=='g gdm 21\n'
st=(T/'var/lib/gdm').stat();assert (st.st_uid,st.st_gid,stat.S_IMODE(st.st_mode))==(0,0,0o755)
conf=configparser.ConfigParser();conf.optionxform=str;conf.read(T/'etc/gdm/custom.conf')
for n in ['AutomaticLoginEnable','TimedLoginEnable','InitialSetupEnable']:assert not conf.getboolean('daemon',n)
assert not (T/'etc/systemd/system/display-manager.service').exists(),'No display manager activation before native GUI gate'
for name in ['system-auth','system-account','system-password','system-session']:assert (T/'etc/pam.d'/name).read_bytes()==(Path('/opt/toddy-build/config/phase2/pam')/name).read_bytes()
Path('/var/log/toddy/phase2/gdm-installed-consumer.json').write_text(json.dumps({'scope':'Owned full Wayland/Systemd/PAM GDM daemon/libgdm/pam_gdm/GI, actual UID101 client/extensions/precancel/refusal/recovery/CLI/SDK0; dedicated group21/root0755state/dynamic userdb enabled. No greeter/login/keyring/permission/GNOME/physical acceptance or service activation. Stock schema cache pending.','consumer':actual,'GI':gi,'dedicated_gid':21,'obsolete_static_user_created':False,'factory_autologin':False,'daemon_enabled_or_started':False},indent=2)+'\n')
PY
