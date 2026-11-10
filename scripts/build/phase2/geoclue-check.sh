#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import configparser,hashlib,json,shutil,subprocess,tempfile
prefix=['chroot','/mnt/lfs'];env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':'/tmp','PYTHONDONTWRITEBYTECODE':'1'}
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','geoclue'],text=True)=='install ok installed 2.8.2-1+toddy1'
assert subprocess.check_output(prefix+['pkg-config','--modversion','libgeoclue-2.0'],text=True).strip()=='2.8.2'
assert not subprocess.check_output(prefix+['dpkg','--audit'],text=True).strip();subprocess.run(prefix+['apt-get','check'],check=True)
w=Path('/mnt/lfs/sources/phase2/work/geoclue-1');expected=json.loads((w/'stage-results.json').read_text())['consumer'];assert not Path('/mnt/lfs/stage').exists()
with tempfile.TemporaryDirectory(prefix='toddy-geoclue-',dir='/mnt/lfs/tmp') as directory:
 p=Path(directory);shutil.copyfile(w/'native-probe',p/'probe');(p/'probe').chmod(0o755)
 assert hashlib.sha256((p/'probe').read_bytes()).digest()==hashlib.sha256((w/'native-probe').read_bytes()).digest()
 native='/tmp/'+p.name+'/probe';libs=subprocess.check_output(prefix+['ldd',native],text=True,env=env);assert 'libgeoclue-2.so.0 => /usr/lib/libgeoclue-2.so.0' in libs
 actual=json.loads(subprocess.check_output(prefix+[native],env=env,text=True,timeout=20));assert actual==expected
assert subprocess.check_output(prefix+['/usr/libexec/geoclue','--version'],text=True,env=env).strip()=='2.8.2'
code="""import gi,json
gi.require_version('Geoclue','2.0')
from gi.repository import Geoclue
p=Geoclue.LocationSkeleton.new();p.props.latitude=-23.433333;p.props.description='Posição sintética · Toddy'
assert abs(p.props.latitude+23.433333)<1e-9 and p.props.description=='Posição sintética · Toddy'
print(json.dumps({'namespace':'Geoclue2.0','typed_UTF8_properties':True}))
"""
gi=json.loads(subprocess.check_output(prefix+['python3','-c',code],env=env,text=True,timeout=20))
user=next(s.split(':') for s in Path('/mnt/lfs/etc/passwd').read_text().splitlines() if s.startswith('geoclue:'));assert user[2:4]==['30','30'] and user[5:]==['/var/lib/geoclue','/bin/false']
shadow=next(s.split(':') for s in Path('/mnt/lfs/etc/shadow').read_text().splitlines() if s.startswith('geoclue:'));assert shadow[1].startswith('!');del shadow
assert Path('/mnt/lfs/usr/lib/sysusers.d/geoclue-sysusers.conf').read_text()=='u geoclue 30 - /var/lib/geoclue /bin/false\n'
conf=configparser.ConfigParser(interpolation=None);text=Path('/mnt/lfs/etc/geoclue/geoclue.conf').read_text();conf.read_string(text)
assert not conf.getboolean('wifi','submit-data') and not Path('/mnt/lfs/etc/geoclue/conf.d/90-lfs-google.conf').exists()
assert not Path('/mnt/lfs/etc/xdg/autostart/geoclue-demo-agent.desktop').exists()
Path('/var/log/toddy/phase2/geoclue-installed-consumer.json').write_text(json.dumps({'scope':'Owned full backend/locked nonroot account/C/GI2.0 typed skeleton/refusal/recovery/SDK/APT and inactive service configuration only; actual D-Bus authorization/Stop/reconnect/location-source and native GNOME permission UI remain pending.','consumer':actual,'GI':gi,'service_uid':30,'service_gid':30,'service_account_locked':True,'telemetry_submission_default':False,'book_provider_key_override_used':False,'loaded_owned_library':True},indent=2)+'\n')
PY
