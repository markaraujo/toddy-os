#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import hashlib,json,os,shutil,subprocess,tempfile
T=Path('/mnt/lfs');prefix=['chroot',str(T)];env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':'/tmp','PYTHONDONTWRITEBYTECODE':'1'}
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','vte'],text=True)=='install ok installed 0.84.1-1+toddy1'
assert subprocess.check_output(prefix+['pkg-config','--modversion','vte-2.91'],text=True).strip()=='0.84.1'
assert not subprocess.check_output(prefix+['dpkg','--audit'],text=True).strip();subprocess.run(prefix+['apt-get','check'],check=True)
expected=json.loads((T/'sources/phase2/work/vte-1/stage-results.json').read_text())['consumer']
source=T/'sources/phase2/work/vte-1/probe-3/native-probe'
if not source.exists():source=T/'sources/phase2/work/vte-1/native-probe'
assert not (T/'stage').exists()
with tempfile.TemporaryDirectory(prefix='toddy-vte-',dir=T/'tmp') as directory:
 p=Path(directory);os.chown(p,101,101);p.chmod(0o755);shutil.copyfile(source,p/'native-probe');(p/'native-probe').chmod(0o755)
 virtual='/tmp/'+p.name
 libs=subprocess.check_output(prefix+['ldd',virtual+'/native-probe'],env=env,text=True);assert 'libvte-2.91.so.0 => /usr/lib/libvte-2.91.so.0' in libs and 'not found' not in libs
 wrapper='''set -euo pipefail
mount --make-rprivate /
mount -t tmpfs -o size=1m,nosuid,nodev tmpfs /mnt/lfs/dev
mkdir /mnt/lfs/dev/pts
mount -t devpts -o newinstance,nosuid,noexec,mode=0620,ptmxmode=0666,gid=101 devpts /mnt/lfs/dev/pts
ln -s pts/ptmx /mnt/lfs/dev/ptmx
for name in null zero random urandom; do touch /mnt/lfs/dev/$name; mount --bind /dev/$name /mnt/lfs/dev/$name; done
exec chroot --userspec=101:101 /mnt/lfs /usr/bin/python3 -c "$1" "$2"
'''
 code="import os,json,subprocess,sys;assert os.getuid()==os.geteuid()==101;print(subprocess.check_output([sys.argv[1],'/etc/profile.d/vte.sh'],text=True),end='')"
 actual=json.loads(subprocess.check_output(['unshare','--mount','--pid','--fork','--net','bash','-c',wrapper,'toddy-vte',code,virtual+'/native-probe'],env=env,text=True,timeout=70));assert actual==expected
 gi=json.loads(subprocess.check_output(['unshare','--net','chroot','--userspec=101:101',str(T),'python3','-c',"import gi,json;gi.require_version('Vte','2.91');from gi.repository import Vte;assert (Vte.get_major_version(),Vte.get_minor_version(),Vte.get_micro_version())==(0,84,1);print(json.dumps({'namespace':'Vte2.91','runtime_version':'0.84.1','widget_or_display_tested':False}))"],env=env,text=True,timeout=15))
assert not (T/'dev/pts').exists() and not (T/'dev/ptmx').exists()
index=json.loads((T/'usr/share/doc/vte/source-notices/index.json').read_text());assert {r['filename'] for r in index['sources']}=={'vte-0.84.1.tar.gz','fmt-12.2.0.tar.gz','fast_float-8.2.10.tar.gz'}
conf=subprocess.check_output(prefix+['dpkg-query','-W','-f=${Conffiles}','vte'],text=True);assert '/etc/profile.d/vte.sh ' in conf and '/etc/profile.d/vte.csh ' in conf
Path('/var/log/toddy/phase2/vte-installed-consumer.json').write_text(json.dumps({'scope':'Actual installed UID101 shared VTE/regex/refusal/PTY/UTF8/managed-group Stop/recovery/interactive owner prompt/GI, private no-route/devpts namespace removed. All18originals retained, both shell conffiles and inlined dependency notices verified. No widget/GNOME Terminal/display/focus acceptance.','consumer':actual,'GI_consumer':gi,'shared_library_resolution':True,'shell_conffiles':True,'inlined_dependency_notices':True},indent=2)+'\n')
PY
