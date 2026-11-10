#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import json,os,shutil,subprocess,sys,tempfile
T=Path('/mnt/lfs');prefix=['chroot',str(T)];env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','PYTHONDONTWRITEBYTECODE':'1'}
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','gexiv2'],text=True)=='install ok installed 0.16.2-1+toddy1'
assert subprocess.check_output(prefix+['pkg-config','--modversion','gexiv2-0.16'],text=True).strip()=='0.16.2'
assert not subprocess.check_output(prefix+['dpkg','--audit'],text=True).strip();subprocess.run(prefix+['apt-get','check'],check=True)
sys.path.insert(0,'/opt/toddy-build/scripts/build/phase2');from qualify_gexiv2 import qualify,digest
proof=qualify(Path('/opt/toddy-build'))
for relative,sha in proof['stage_sha256'].items():assert digest(T/relative)==sha
with tempfile.TemporaryDirectory(prefix='toddy-gexiv2-',dir=T/'tmp') as directory:
 p=Path(directory);os.chown(p,101,101);p.chmod(0o755);virtual='/tmp/'+p.name;env['HOME']=virtual
 shutil.copyfile('/opt/toddy-build/scripts/build/phase2/gexiv2-probe.py',p/'probe.py')
 wrapper='set -euo pipefail; mount --make-rprivate /; mount -t tmpfs -o size=1m,nosuid,nodev tmpfs /mnt/lfs/dev; for name in null zero random urandom; do touch /mnt/lfs/dev/$name; mount --bind /dev/$name /mnt/lfs/dev/$name; done; exec chroot --userspec=101:101 /mnt/lfs "$@"'
 command=['unshare','--mount','--pid','--fork','--net','bash','-c',wrapper,'toddy-gexiv2']
 actual=json.loads(subprocess.check_output(command+['python3',virtual+'/probe.py',virtual+'/consumer'],env=env,text=True,timeout=45));assert actual==proof['consumer']
 libs=subprocess.check_output(prefix+['ldd','/usr/lib/libgexiv2-0.16.so.4'],env=env,text=True);assert 'libexiv2.so.28 => /usr/lib/libexiv2.so.28' in libs and 'not found' not in libs
Path('/var/log/toddy/phase2/gexiv2-installed-consumer.json').write_text(json.dumps({'scope':'Actual installed UID101/private-devices/no-route GI PNG UTF8 write/read/reset/image retention/malformed JPEG refusal/two recoveries, unchanged stage bytes/pkg-config/shared ABI/APT0. No LocalSearch/Nautilus/GUI acceptance.','consumer':actual,'installed_stage_files_identical':len(proof['stage_sha256']),'shared_library_resolution':True},indent=2)+'\n')
PY
