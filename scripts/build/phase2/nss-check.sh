#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
unshare --mount --propagation private python3 - <<'PY'
from pathlib import Path
import hashlib,json,shutil,subprocess,tempfile
# A bare packaging chroot has no devtmpfs. Supply only standard character
# devices in this private mount namespace, never the builder's disk devices.
subprocess.run(['mount','-t','tmpfs','-o','nosuid,size=1m,mode=755','tmpfs','/mnt/lfs/dev'],check=True)
for name in ['null','zero','random','urandom']:
 p=Path('/mnt/lfs/dev')/name;p.touch();subprocess.run(['mount','--bind','/dev/'+name,str(p)],check=True)
env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':'/root'};prefix=['chroot','/mnt/lfs']
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','nss'],text=True,env=env)=='install ok installed 3.126-1+toddy1'
assert subprocess.check_output(prefix+['pkg-config','--modversion','nss'],text=True,env=env).strip()=='3.126.0'
assert subprocess.check_output(prefix+['nss-config','--version'],text=True,env=env).strip()=='3.126.0'
assert not subprocess.check_output(prefix+['dpkg','--audit'],text=True,env=env).strip();subprocess.run(prefix+['apt-get','check'],env=env,check=True)
work=Path('/mnt/lfs/sources/phase2/work/nss-1');expected=json.loads((work/'stage-results.json').read_text())['consumer']
for name in ['libpkcs11testmodule.so','libnssckbi-testlib.so']:assert not Path('/mnt/lfs/usr/lib',name).exists()
with tempfile.TemporaryDirectory(prefix='toddy-nss-',dir='/mnt/lfs/tmp') as directory:
 p=Path(directory);shutil.copyfile(work/'native-probe',p/'probe');(p/'probe').chmod(0o755)
 assert hashlib.sha256((p/'probe').read_bytes()).digest()==hashlib.sha256((work/'native-probe').read_bytes()).digest() and not Path('/mnt/lfs/stage').exists()
 virtual='/tmp/'+p.name;r=subprocess.run(prefix+[virtual+'/probe'],env=env,capture_output=True,text=True,timeout=30,check=True);consumer=json.loads(r.stdout);assert consumer==expected
 db=p/'db';db.mkdir(mode=0o700);args=['certutil','-d','sql:'+virtual+'/db']
 subprocess.run(prefix+args+['-N','--empty-password'],env=env,capture_output=True,timeout=30,check=True)
 first=subprocess.run(prefix+args+['-L'],env=env,capture_output=True,timeout=15,check=True)
 invalid=p/'invalid.der';invalid.write_bytes(bytes([0x30,0x82,0xff]))
 bad=subprocess.run(prefix+args+['-A','-n','Toddy-invalid-public-fixture','-t',',,','-i',virtual+'/invalid.der'],env=env,capture_output=True,timeout=15);assert bad.returncode!=0
 second=subprocess.run(prefix+args+['-L'],env=env,capture_output=True,timeout=15,check=True);assert first.stdout==second.stdout and b'Toddy-invalid-public-fixture' not in second.stdout
 assert (db/'cert9.db').is_file() and (db/'key4.db').is_file() and db.stat().st_mode&0o777==0o700
assert not Path(directory).exists()
Path('/var/log/toddy/phase2/nss-installed-consumer.json').write_text(json.dumps({'scope':'Installed SHA256/random/AES-GCM/tamper/refusal/recovery/SQL DB invalid-cert refusal/SDK/audit; TLS/trust-store/remote network/GNOME pending','consumer':consumer,'private_SQL_database_created':True,'malformed_DER_certificate_refused':True,'certificate_listing_preserved_after_refusal':True,'temporary_SQL_data_removed':True,'test_modules_not_shipped':True,'root_provider':'Upstream bundled roots; qualified p11-kit/make-ca switch pending'},indent=2)+'\n')
PY
