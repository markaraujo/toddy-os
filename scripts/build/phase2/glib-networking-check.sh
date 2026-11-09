#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import hashlib,json,shutil,subprocess,tempfile
prefix=['chroot','/mnt/lfs'];env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':'/tmp','PYTHONDONTWRITEBYTECODE':'1'}
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','glib-networking'],text=True)=='install ok installed 2.80.1-1+toddy1'
assert not subprocess.check_output(prefix+['dpkg','--audit'],text=True).strip();subprocess.run(prefix+['apt-get','check'],check=True)
resources=json.loads(Path('/var/log/toddy/phase2/gio-network-resources-1.json').read_text());assert resources['state']=='complete'
assert hashlib.sha256(Path('/mnt/lfs/usr/lib/gio/modules/giomodule.cache').read_bytes()).hexdigest()==resources['new_cache_sha256']
work=Path('/mnt/lfs/sources/phase2/work/glib-networking-1');expected=json.loads((work/'stage-results.json').read_text())['consumer']
with tempfile.TemporaryDirectory(prefix='toddy-gio-network-',dir='/mnt/lfs/tmp') as directory:
    p=Path(directory);shutil.copyfile(work/'native-probe-3',p/'probe');(p/'probe').chmod(0o755)
    native='/tmp/'+p.name
    # No GIO module/TLS override: actual installed shared cache selects backend.
    consumer=json.loads(subprocess.check_output(prefix+[native+'/probe'],env=env,text=True,timeout=30));assert consumer==expected
    script=Path('/opt/toddy-build/scripts/build/phase2/dconf-gsettings-probe.py');shutil.copyfile(script,p/script.name)
    settings=json.loads(subprocess.check_output(prefix+['python3','-B',native+'/'+script.name,'/',native+'/settings','installed'],env=env,text=True,timeout=70))
    assert settings['mode']=='installed' and all(r['backend']=='DConfSettingsBackend' for r in settings['cycles'])
Path('/var/log/toddy/phase2/glib-networking-installed-consumer.json').write_text(json.dumps({'scope':'Owned actual default GIO/GnuTLS factory trust/malformed certificate refusal/recovery and changed shared-cache DConf GSettings persistence/new-bus/reset. Original local TLS/proxy fixtures reused; remote network/native GNOME/DTLS pending.','consumer':consumer,'GSettings_changed_cache_consumer':settings,'shared_cache_modules':4,'module_override_used':False},indent=2)+'\n')
PY
