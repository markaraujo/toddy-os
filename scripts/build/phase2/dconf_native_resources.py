"""Generate the first owned DConf GIO module cache inside the full-root transaction."""
import hashlib,json,subprocess
from pathlib import Path
subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
record=Path('/var/log/toddy/packages/dconf_0.49.0-1+toddy1_amd64.json');r=json.loads(record.read_text());assert r['installed']
modules=Path('/mnt/lfs/usr/lib/gio/modules');library=modules/'libdconfsettings.so';cache=modules/'giomodule.cache'
assert sorted(p.name for p in modules.glob('*.so'))==['libdconfsettings.so']
assert hashlib.sha256(library.read_bytes()).hexdigest()==r['payload']['/usr/lib/gio/modules/libdconfsettings.so']['sha256']
assert not cache.exists() and not cache.is_symlink(),'Reconcile generated cache before any repeat'
subprocess.run(['chroot','/mnt/lfs','gio-querymodules','/usr/lib/gio/modules'],check=True)
assert cache.read_text().strip()=='libdconfsettings.so: gsettings-backend'
r['generated_paths'].append('/usr/lib/gio/modules/giomodule.cache')
r['generated_resources']={'/usr/lib/gio/modules/giomodule.cache':{'generator':'/usr/bin/gio-querymodules','input_sha256':hashlib.sha256(library.read_bytes()).hexdigest(),'sha256':hashlib.sha256(cache.read_bytes()).hexdigest(),'scope':'Generated runtime cache, not archive payload; regenerate proportionally when qualified module inputs change'}}
part=record.with_suffix('.part');assert not part.exists();part.write_text(json.dumps(r,indent=2)+'\n');part.replace(record)
