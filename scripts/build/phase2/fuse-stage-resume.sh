#!/bin/bash
# No compiler replay: complete staging of existing85 successful build targets.
set -euo pipefail
[[ $(id -u) == 101 && -f /build/compile/build.ninja && -z $(ls -A /stage) ]]
[[ $(sha256sum /src/toddy-build.sh | cut -d' ' -f1) == a918260c35b26b8f1e0232129417dd93f3ddcc5932dff3b7818df1779d46abf5 ]]
export PYTHONDONTWRITEBYTECODE=1
python3 - <<'PY'
from pathlib import Path
import json,subprocess
p=Path('/build');rows=[]
# The Meson "wrong_command" target deliberately fails, telling users to invoke
# pytest. These real upstream C drivers do not need a kernel/device mount.
for name in ['test_abi','test_want_conversion']:
 r=subprocess.run([str(p/'compile/test'/name)],capture_output=True,text=True,timeout=30)
 rows.append({'name':name,'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr})
 assert r.returncode==0,(name,r.stdout,r.stderr)
(p/'isolated-unit-results-2.json').write_text(json.dumps(rows,indent=2)+'\n')
PY
meson install -C /build/compile --destdir /stage --no-rebuild
python3 - <<'PY'
from pathlib import Path
import hashlib,json,os,subprocess
w=Path('/build');s=Path('/stage');helper=s/'usr/bin/fusermount3'
r=subprocess.run([str(helper),'--version'],capture_output=True,text=True,timeout=15);assert r.returncode==0 and '3.18.2' in r.stdout
bad=subprocess.run([str(helper),'--toddy-invalid-option'],capture_output=True,text=True,timeout=15);assert bad.returncode!=0
assert not helper.stat().st_mode&0o6000,'Unprivileged stage must not set root helper privilege'
assert os.statvfs(w).f_bavail*os.statvfs(w).f_frsize>=16*1024**3
result={'scope':'Isolated UID101/NNP Fuse3.18.2 compile/stage, two actual upstream non-mount C drivers and helper version/invalid option. Kernel mount/custom-IO and privileged-helper permission/refusal/recovery tests remain pending. No root helper permission installed by compiler.',
 'compile_exit':0,'stage_exit':0,'native_signals_test':'Pending actual FUSE device/mount; original isolated failure retained',
 'original_units':json.loads((w/'isolated-unit-results-2.json').read_text()),'helper_version':r.stdout.strip(),'invalid_option_exit':bad.returncode,
 'stage_sha256':{str(p.relative_to(s)):hashlib.sha256(p.read_bytes()).hexdigest() for p in s.rglob('*') if p.is_file() and not p.is_symlink()},
 'artifacts':{str(p.relative_to(w/'compile')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (w/'compile').rglob('*') if p.is_file() and not p.is_symlink() and p.open('rb').read(4)==b'\x7fELF'}}
(w/'stage-results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['stage_sha256','artifacts']}))
PY
