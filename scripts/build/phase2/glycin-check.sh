#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import hashlib,json,shlex,subprocess,tempfile
root=Path('/opt/toddy-build');target=Path('/mnt/lfs');prefix=['chroot',str(target)]
env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':'/root','PYTHONDONTWRITEBYTECODE':'1'}
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','glycin'],env=env,text=True)=='install ok installed 2.1.5-1+toddy1'
assert subprocess.check_output(prefix+['pkg-config','--modversion','glycin-2'],env=env,text=True).strip()=='2.1.0'
assert not subprocess.check_output(prefix+['dpkg','--audit'],env=env,text=True).strip()
subprocess.run(prefix+['apt-get','check'],env=env,check=True)
proof=json.loads(Path('/var/log/toddy/phase2/glycin-native-runtime-5.json').read_text())
for relative,sha in proof['stage_file_hashes'].items():
 with (target/relative).open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==sha
for relative in ['usr/lib/libglycin-2.so','usr/libexec/glycin-loaders/2+/glycin-image-rs','usr/libexec/glycin-loaders/2+/glycin-svg']:
 r=subprocess.run(prefix+['ldd','/'+relative],env=env,capture_output=True,text=True,check=True)
 assert 'not found' not in r.stdout+r.stderr
with tempfile.TemporaryDirectory(prefix='toddy-glycin-api-',dir='/mnt/lfs/tmp') as directory:
 p=Path(directory);native='/tmp/'+p.name;(p/'consumer.c').write_bytes((root/'scripts/build/phase2/glycin-probe.c').read_bytes())
 flags=shlex.split(subprocess.check_output(prefix+['pkg-config','--cflags','--libs','glycin-2'],env=env,text=True))
 subprocess.run(prefix+['cc','-std=c11','-Wall','-Wextra','-Werror',native+'/consumer.c',*flags,'-o',native+'/consumer'],env=env,check=True)
 subprocess.run(prefix+[native+'/consumer'],env=env,check=True)
body="import gi;gi.require_version('Gly','2');from gi.repository import Gly,GLib;l=Gly.Loader.new_for_bytes(GLib.Bytes.new(b'installed-type-probe'));assert l is not None;l.set_sandbox_selector(Gly.SandboxSelector.BWRAP)"
subprocess.run(prefix+['python3','-B','-c',body],env=env,check=True)
out={'scope':'Owned installed Glycin dependency closure/C+GI types and exact payload identity with actual native-tested stage; no Ubuntu namespace retry',
     'installed_payload_files_verified':len(proof['stage_file_hashes']),'native_consumer_exit':0,'gi_type_exit':0,
     'native_selected_upstream_cases':24,'installed_default_path_sandbox_image_test':'Pending subsequent native desktop boot gate',
     'original_failures_preserved':True}
Path('/var/log/toddy/phase2/glycin-installed-consumer.json').write_text(json.dumps(out,indent=2)+'\n')
PY
