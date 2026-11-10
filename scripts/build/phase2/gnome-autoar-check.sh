#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import hashlib,json,os,shutil,subprocess,tempfile,zipfile
T=Path('/mnt/lfs');prefix=['chroot',str(T)];env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':'/tmp','PYTHONDONTWRITEBYTECODE':'1'}
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','gnome-autoar'],text=True)=='install ok installed 0.4.5-1+toddy1'
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','libarchive'],text=True)=='install ok installed 3.8.11-1+toddy1'
for n in ['gnome-autoar-0','gnome-autoar-gtk-0']:assert subprocess.check_output(prefix+['pkg-config','--modversion',n],text=True).strip()=='0.4.5'
assert not subprocess.check_output(prefix+['dpkg','--audit'],text=True).strip();subprocess.run(prefix+['apt-get','check'],check=True)
r=json.loads((T/'sources/phase2/work/gnome-autoar-1/stage-results.json').read_text());assert not (T/'stage').exists()
with tempfile.TemporaryDirectory(prefix='toddy-gnome-autoar-',dir=T/'tmp') as directory:
 p=Path(directory);os.chown(p,101,101);p.chmod(0o755);source=T/'sources/phase2/work/gnome-autoar-1/probe-3/native-probe'
 if not source.exists():source=T/'sources/phase2/work/gnome-autoar-1/native-probe'
 shutil.copyfile(source,p/'native-probe');(p/'native-probe').chmod(0o755);virtual='/tmp/'+p.name
 with zipfile.ZipFile(p/'payload.zip','w',compression=zipfile.ZIP_DEFLATED) as z:z.writestr('documento-ã.txt','Olá Toddy\n')
 (p/'empty.zip').write_bytes(b'');original={n:hashlib.sha256((p/n).read_bytes()).hexdigest() for n in ['payload.zip','empty.zip']}
 wrapper='set -euo pipefail; mount --make-rprivate /; mount -t tmpfs -o size=1m,nosuid,nodev tmpfs /mnt/lfs/dev; for name in null zero random urandom; do touch /mnt/lfs/dev/$name; mount --bind /dev/$name /mnt/lfs/dev/$name; done; exec chroot --userspec=101:101 /mnt/lfs "$@"'
 command=['unshare','--mount','--pid','--fork','--net','bash','-c',wrapper,'toddy-autoar']
 actual=json.loads(subprocess.check_output(command+[virtual+'/native-probe',virtual],env=env,text=True,timeout=30));assert actual==r['consumer'];assert original=={n:hashlib.sha256((p/n).read_bytes()).hexdigest() for n in original}
 code="import gi,json;gi.require_version('GnomeAutoar','0.1');gi.require_version('GnomeAutoarGtk','0.1');from gi.repository import GnomeAutoar,GnomeAutoarGtk;assert GnomeAutoar.Extractor.__gtype__.name=='AutoarExtractor';print(json.dumps({'namespace':'GnomeAutoar0.1/GnomeAutoarGtk0.1','GI_type':'AutoarExtractor','widget_tested':False}))"
 gi=json.loads(subprocess.check_output(command+['python3','-c',code],env=env,text=True,timeout=15));assert gi==r['GI_consumer']
 libs=subprocess.check_output(prefix+['ldd',virtual+'/native-probe'],env=env,text=True);assert 'libgnome-autoar-0.so.0 => /usr/lib/libgnome-autoar-0.so.0' in libs and 'not found' not in libs
Path('/var/log/toddy/phase2/gnome-autoar-installed-consumer.json').write_text(json.dumps({'scope':'Actual installed UID101/private-device/no-route ZIP Unicode filename/content extraction/empty refusal/precancelled no-destination/two recovery cycles/source retained/C-GI/shared ABI/pkg-config/APT0. Existing owned libarchive3.8.11 reused, no downgrade/rebuild. Original22automated archive/security cases retained/private identical130entry fixtures; manual create/extract/UI programs compile-only, no GUI or mid-extraction Stop acceptance.','consumer':actual,'GI_consumer':gi,'shared_library_resolution':True,'reused_libarchive':'3.8.11-1+toddy1'},indent=2)+'\n')
PY
