"""Native daemon version and installed-layout GI types, not a live account action."""
import json,subprocess,sys
from pathlib import Path
import gi
gi.require_version('AccountsService','1.0')
from gi.repository import AccountsService as Act
prefix=Path(sys.argv[1])
r=subprocess.run([str(prefix/'usr/libexec/accounts-daemon'),'--version'],capture_output=True,text=True,timeout=10,check=True)
assert r.stdout.strip()=='accounts-daemon 26.27.3'
assert Act.User.__gtype__.name=='ActUser' and Act.UserManager.__gtype__.name=='ActUserManager'
assert int(Act.UserPasswordMode.REGULAR)==0 and int(Act.UserAccountType.ADMINISTRATOR)==1
print(json.dumps({'version':'26.27.3','daemon_version_exit':0,'native_gi_types':['ActUser','ActUserManager'],'password_mode_enum':0,'administrator_enum':1,'scope':'CLI/GI link only; original private-bus fixtures separate, no real account/privilege/GDM claim'}))
