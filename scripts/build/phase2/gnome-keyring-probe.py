"""Native daemon version and PAM loader ABI only; no real login/credential claim."""
from pathlib import Path
import ctypes,json,os,subprocess,sys
p=Path(sys.argv[1]);daemon=p/'usr/bin/gnome-keyring-daemon'
r=subprocess.run([str(daemon),'--version'],capture_output=True,text=True,timeout=10,check=True)
assert 'gnome-keyring-daemon: 50.0' in r.stdout and 'testing: disabled' in r.stdout
module=p/'usr/lib/security/pam_gnome_keyring.so';assert module.is_file()
library=ctypes.CDLL(str(module),mode=os.RTLD_NOW|os.RTLD_LOCAL)
symbols=['pam_sm_authenticate','pam_sm_setcred','pam_sm_open_session','pam_sm_close_session','pam_sm_chauthtok']
for name in symbols:assert getattr(library,name)
assert not (p/'usr/lib/gnome-keyring/gnome-keyring-ssh').exists()
print(json.dumps({'version':'50.0','daemon_version_exit':0,'production_test_hooks_disabled':True,'PAM_loaded_exports':symbols,'scope':'CLI/PAM load only; actual backend/PAM login/graphical acceptance pending, no policy enabled or real credentials used'}))
