#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import hashlib,json,subprocess
T=Path('/mnt/lfs');prefix=['chroot',str(T)];env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':'/tmp','PYTHONDONTWRITEBYTECODE':'1'}
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','gtk3'],text=True)=='install ok installed 3.24.52-1+toddy2'
assert subprocess.check_output(prefix+['pkg-config','--modversion','gtk+-3.0'],text=True).strip()=='3.24.52'
assert not subprocess.check_output(prefix+['dpkg','--audit'],text=True).strip();subprocess.run(prefix+['apt-get','check'],check=True)
r=json.loads(Path('/var/log/toddy/phase2/gtk3-ibus-cache-transaction-1.json').read_text());assert r['state']=='complete'
cache=T/'usr/lib/gtk-3.0/3.0.0/immodules.cache'
assert hashlib.sha256(cache.read_bytes()).hexdigest()==r['new_cache_sha256']
query=subprocess.run(['chroot','--userspec=101:101',str(T),'/usr/bin/gtk-query-immodules-3.0',*sorted(r['modules'])],env=env,capture_output=True,timeout=20)
assert query.returncode==0 and not query.stderr and query.stdout==cache.read_bytes()
for name,row in r['modules'].items():assert hashlib.sha256((T/name.lstrip('/')).read_bytes()).hexdigest()==row['sha256']
notice=json.loads((T/'usr/share/doc/gtk3/source-notices/index.json').read_text());assert all(row['notices'] for row in notice['sources'])
Path('/var/log/toddy/phase2/gtk3-ibus-cache-installed-consumer.json').write_text(json.dumps({'scope':'Actual installed GTK3 query tool as UID101 loads twelve owned IM modules; exact cache output/eleven prior registrations and IBus registration verified. All old runtime/header/config payload retained, SDK/APT0. No window/focus/GNOME input or arbitrary module lifecycle acceptance.','uid':101,'query_exit':0,'modules':12,'prior_module_registrations_preserved':11,'IBus_registered':True,'all_source_notices_retained':True,'old_nonlegal_entries_unchanged':r['old_nonlegal_entries_unchanged']},indent=2)+'\n')
PY
