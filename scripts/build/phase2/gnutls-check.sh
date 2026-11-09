#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import hashlib,json,shutil,subprocess,tempfile
prefix=['chroot','/mnt/lfs'];env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':'/tmp'}
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','gnutls'],text=True)=='install ok installed 3.8.13-1+toddy1'
assert subprocess.check_output(prefix+['pkg-config','--modversion','gnutls'],text=True).strip()=='3.8.13'
assert not subprocess.check_output(prefix+['dpkg','--audit'],text=True).strip()
subprocess.run(prefix+['apt-get','check'],check=True)
work=Path('/mnt/lfs/sources/phase2/work/gnutls-1');expected=json.loads((work/'stage-results.json').read_text())['consumer']
assert not Path('/mnt/lfs/stage').exists() and not Path('/mnt/lfs/build').exists()
with tempfile.TemporaryDirectory(prefix='toddy-gnutls-',dir='/mnt/lfs/tmp') as directory:
    p=Path(directory);shutil.copyfile(work/'native-probe',p/'probe');(p/'probe').chmod(0o755)
    assert hashlib.sha256((p/'probe').read_bytes()).digest()==hashlib.sha256((work/'native-probe').read_bytes()).digest()
    native='/tmp/'+p.name+'/probe'
    libs=subprocess.check_output(prefix+['ldd',native],env=env,text=True)
    assert 'libgnutls.so.30 => /usr/lib/libgnutls.so.30' in libs and '/stage/' not in libs
    consumer=json.loads(subprocess.check_output(prefix+[native],env=env,text=True,timeout=30));assert consumer==expected
# Revalidate only the directly affected original against OWNED installed GnuTLS
# and real system trust, no private library/trust environment or path aliases.
r=subprocess.run(['chroot','--userspec=101:101','/mnt/lfs','/sources/phase2/inputs/make-ca-data-2/trust-store'],env=env,text=True,capture_output=True,timeout=30)
Path('/var/log/toddy/phase2/gnutls-installed-original-trust.log').write_text(r.stdout+r.stderr);assert r.returncode==0
Path('/var/log/toddy/phase2/gnutls-installed-consumer.json').write_text(json.dumps({'scope':'Owned installed crypto/default UTF8/IDNA/priority/refusal/recovery/SDK, unchanged original default system trust. Public DNS, remote TLS, native GNOME and local-trust update/recovery remain pending.','consumer':consumer,'original_default_trust_exit':0,'loaded_owned_library':True,'SDK_version':'3.8.13'},indent=2)+'\n')
PY
