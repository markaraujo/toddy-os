#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import hashlib,json,shutil,subprocess,tempfile
prefix=['chroot','/mnt/lfs'];env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':'/tmp','PYTHONDONTWRITEBYTECODE':'1'}
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','ibus'],text=True)=='install ok installed 1.5.34~rc2-1+toddy1'
assert subprocess.check_output(prefix+['pkg-config','--modversion','ibus-1.0'],text=True).strip()=='1.5.34-rc2'
assert not subprocess.check_output(prefix+['dpkg','--audit'],text=True).strip();subprocess.run(prefix+['apt-get','check'],check=True)
work=Path('/mnt/lfs/sources/phase2/work/ibus-1');expected=json.loads((work/'stage-results.json').read_text())['consumer']
assert not Path('/mnt/lfs/stage').exists()
with tempfile.TemporaryDirectory(prefix='toddy-ibus-',dir='/mnt/lfs/tmp') as directory:
    p=Path(directory);shutil.copyfile(work/'native-probe',p/'probe');(p/'probe').chmod(0o755)
    assert hashlib.sha256((p/'probe').read_bytes()).digest()==hashlib.sha256((work/'native-probe').read_bytes()).digest()
    native='/tmp/'+p.name+'/probe';libs=subprocess.check_output(prefix+['ldd',native],text=True,env=env)
    assert 'libibus-1.0.so.5 => /usr/lib/libibus-1.0.so.5' in libs
    consumer=json.loads(subprocess.check_output(prefix+[native],env=env,text=True,timeout=20));assert consumer==expected
version=subprocess.check_output(prefix+['ibus','version'],env=env,text=True,timeout=10).strip();assert '1.5.34-rc2' in version
for rel in ['usr/lib/gtk-3.0/3.0.0/immodules/im-ibus.so','usr/lib/gtk-4.0/4.0.0/immodules/libim-ibus.so','usr/lib/girepository-1.0/IBus-1.0.typelib']:
    assert Path('/mnt/lfs',rel).is_file()
notice=json.loads(Path('/mnt/lfs/usr/share/doc/ibus/source-notices/index.json').read_text())
assert {r['filename'] for r in notice['sources']}=={'ibus-1.5.34.tar.gz','UCD-17.0.0.zip','Unicode-License-3.0.txt'}
assert all(r['notices'] for r in notice['sources'])
Path('/var/log/toddy/phase2/ibus-installed-consumer.json').write_text(json.dumps({'scope':'Owned IBus public UTF8 serialization/key parser refusal/two-cycle recovery and SDK/modules only. Actual service/bus, shared IM/schema caches and graphical keyboard/desktop pending.','consumer':consumer,'loaded_owned_library':True,'source_tag':'1.5.34','embedded_version':version,'package_version':'1.5.34~rc2-1+toddy1','complete_source_and_Unicode_notices':True},indent=2)+'\n')
PY
