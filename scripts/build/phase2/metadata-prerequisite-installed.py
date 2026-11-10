"""Test the actual owned small-library installation as private UID101 clients."""
from pathlib import Path
import json,os,shutil,subprocess,sys,tempfile
from qualify_metadata_prerequisites import qualify,digest
name,=sys.argv[1:];assert name in ['brotli','inih'];version='1.2.0' if name=='brotli' else '62'
T=Path('/mnt/lfs');prefix=['chroot',str(T)];env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':'/tmp','PYTHONDONTWRITEBYTECODE':'1'}
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}',name],text=True)=='install ok installed '+version+'-1+toddy1'
for module in (['libbrotlicommon','libbrotlidec','libbrotlienc'] if name=='brotli' else ['inih','INIReader']):assert subprocess.check_output(prefix+['pkg-config','--modversion',module],text=True).strip()==version
assert not subprocess.check_output(prefix+['dpkg','--audit'],text=True).strip();subprocess.run(prefix+['apt-get','check'],check=True)
r=qualify(Path('/opt/toddy-build'),name)
for relative,sha in r['stage_sha256'].items():assert digest(T/relative)==sha
with tempfile.TemporaryDirectory(prefix='toddy-'+name+'-',dir=T/'tmp') as directory:
 p=Path(directory);p.chmod(0o755);os.chown(p,101,101);virtual='/tmp/'+p.name
 wrapper='set -euo pipefail; mount --make-rprivate /; mount -t tmpfs -o size=1m,nosuid,nodev tmpfs /mnt/lfs/dev; for name in null zero random urandom; do touch /mnt/lfs/dev/$name; mount --bind /dev/$name /mnt/lfs/dev/$name; done; exec chroot --userspec=101:101 /mnt/lfs "$@"'
 command=['unshare','--mount','--pid','--fork','--net','bash','-c',wrapper,'toddy-small-metadata']
 if name=='brotli':
  shutil.copyfile('/opt/toddy-build/scripts/build/phase2/brotli-probe.py',p/'probe.py');args=['python3',virtual+'/probe.py','/usr/bin/brotli',virtual+'/consumer'];linkage='/usr/bin/brotli'
 else:
  shutil.copyfile(T/'sources/phase2/work/inih-1/native-probe',p/'native-probe');(p/'native-probe').chmod(0o755);args=[virtual+'/native-probe',virtual];linkage=virtual+'/native-probe'
 actual=json.loads(subprocess.check_output(command+args,env=env,text=True,timeout=30));assert actual==r['consumer']
 libs=subprocess.check_output(prefix+['ldd',linkage],env=env,text=True);assert 'not found' not in libs
 for stem in (['libbrotlienc.so.1','libbrotlidec.so.1','libbrotlicommon.so.1'] if name=='brotli' else ['libinih.so.0','libINIReader.so.0']):assert stem+' => /usr/lib/'+stem in libs
Path('/var/log/toddy/phase2/'+name+'-installed-consumer.json').write_text(json.dumps({'scope':'Owned installed UID101/private device/no-route actual local API/CLI UTF8/refusal/recovery/unchanged stage/pkg-config/shared ABI/APT0. New Exiv2 profile and desktop integration remain unqualified.','consumer':actual,'installed_stage_files_identical':len(r['stage_sha256']),'shared_library_resolution':True},indent=2)+'\n')
