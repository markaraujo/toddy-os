"""Prove real-cache sandbox denials before changing a kernel configuration."""
from pathlib import Path
import errno,hashlib,json,os
assert os.getuid()==os.getgid()==101
status=Path('/proc/self/status').read_text();assert 'NoNewPrivs:\t1' in status and 'CapEff:\t0000000000000000' in status
source=Path('/src/cache/init/main.c');original=hashlib.sha256(source.read_bytes()).hexdigest();assert original==hashlib.sha256(Path('/build/merged/init/main.c').read_bytes()).hexdigest()
denied=[]
for p in [source,Path('/build/merged/init/main.c'),Path('/usr/.toddy-kernel-denial')]:
 try:
  fd=os.open(p,os.O_WRONLY|os.O_APPEND|os.O_CREAT,0o600)
 except OSError as e:assert e.errno in (errno.EACCES,errno.EROFS);denied.append(str(p))
 else:os.close(fd);raise AssertionError('Unexpected source/system write access')
try:list(Path('/build/private-overlay').iterdir())
except PermissionError:pass
else:raise AssertionError('Private overlay internals exposed')
assert not Path('/var/lib/dpkg').exists()
p=Path('/build/merged/.toddy-private-isolation-probe');assert not p.exists()
with p.open('x') as f:f.write('private-cache-only\n')
assert p.read_text()=='private-cache-only\n';p.unlink()
assert hashlib.sha256(source.read_bytes()).hexdigest()==original
r={'uid':101,'gid':101,'no_new_privileges':True,'effective_capabilities':0,'write_denials':denied,'overlay_internals_denied':True,'package_database_absent':True,'private_cache_write_read_remove':True,'source_unchanged':True,'source_sha256':original}
Path('/build/worker-isolation.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
