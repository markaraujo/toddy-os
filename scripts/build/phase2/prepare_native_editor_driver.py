"""Prepare one private readonly test-driver input, never install it in the OS."""
from pathlib import Path
import fcntl,hashlib,json,os,subprocess,sys
root=Path('/opt/toddy-build');base=Path('/mnt/lfs/sources/phase2');log=Path('/var/log/toddy/phase2')
subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
for step in ['b02-gnome-text-editor-install','b02-editor-schema-union-install']:
 r=json.loads(Path('/var/log/toddy/build',step+'.success.json').read_text());assert r['recipe_exit']==r['postcheck_exit']==0
generation=sys.argv[1] if len(sys.argv)==2 else '1';assert generation in ['1','2','3']
source=base/'inputs'/('editor-native-driver-'+generation);work=base/'work'/('editor-native-driver-'+generation);receipt=log/('editor-native-driver-prepared-'+generation+'.json')
assert not any(p.exists() for p in [source,work,receipt]);s=os.statvfs('/mnt/lfs');assert s.f_bavail*s.f_frsize>=16*1024**3+4*1024**2
source.mkdir();work.mkdir();os.chown(work,101,101)
for name in ['native-editor-driver.c','native_editor_session.py']:(source/name).write_bytes((root/'scripts/build/phase2'/name).read_bytes())
recipe='''#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/native-editor-driver.so ]]
cc -O2 -fPIC -shared -Werror=implicit-function-declaration /src/native-editor-driver.c $(pkg-config --cflags --libs gtk4) -Wl,-z,relro,-z,now -o /build/native-editor-driver.so
python3 - <<'RESULT'
from pathlib import Path
import hashlib,json
p=Path('/build/native-editor-driver.so');assert p.read_bytes().startswith(b'\\x7fELF')
Path('/build/driver-result.json').write_text(json.dumps({'compile_exit':0,'test_only':True,'installed_to_system':False,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()},indent=2)+'\\n')
RESULT
'''
(source/'toddy-build.sh').write_text(recipe)
proof={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in source.iterdir()}
for p in source.iterdir():p.chmod(0o444)
source.chmod(0o555);receipt.write_text(json.dumps({'scope':'Own test instrumentation and driver only; actual product source/binary unchanged. No fixture success or GUI acceptance from compilation.','source':str(source),'work':str(work),'inputs':proof},indent=2)+'\n')
print(json.dumps({'prepared':True,'inputs':proof}))
