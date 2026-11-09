#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import hashlib,json,subprocess,tempfile,os
prefix=['chroot','/mnt/lfs'];env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':'/tmp'}
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Version}','systemd'],text=True)=='261.2-1+toddy2'
assert not subprocess.check_output(prefix+['dpkg','--audit'],text=True).strip();subprocess.run(prefix+['apt-get','check'],check=True)
receipt=json.loads(Path('/var/log/toddy/phase2/hwdb-cache-transaction.json').read_text());assert receipt['state']=='complete'
p=Path('/mnt/lfs/usr/lib/udev/hwdb.bin');assert hashlib.sha256(p.read_bytes()).hexdigest()==receipt['cache_sha256']
with tempfile.TemporaryDirectory(prefix='toddy-hwdb-',dir='/mnt/lfs/tmp') as directory:
 p=Path(directory);(p/'consumer.c').write_bytes(Path('/mnt/lfs/sources/phase2/work/hwdb-cache-1/probe-2/consumer.c').read_bytes());native='/tmp/'+p.name
 subprocess.run(prefix+['cc','-Wall','-Wextra','-Werror',native+'/consumer.c','-lsystemd','-o',native+'/consumer'],check=True)
 subprocess.run(prefix+[native+'/consumer','/usr/lib/udev/hwdb.bin'],check=True)
result=subprocess.check_output(prefix+['systemd-hwdb','query','acpi:GSM:'],text=True);assert 'ID_VENDOR_FROM_DATABASE=LG Electronics' in result
base='/sources/phase2/';code=['chroot','--userspec=101:101','/mnt/lfs',base+'work/colord-1/compile/lib/colord/colord-test-private','-p','/colord/edid']
env.update(TESTDATADIR=base+'inputs/colord-1.4.8/data/tests',LD_LIBRARY_PATH=base+'work/colord-1/compile/lib/colord')
with Path('/var/log/toddy/phase2/hwdb-colord-edid-2.log').open('xb') as out:r=subprocess.run(code,env=env,stdout=out,stderr=subprocess.STDOUT)
assert r.returncode==0
assert 'ok 1 /colord/edid' in Path('/var/log/toddy/phase2/hwdb-colord-edid-2.log').read_text()
Path('/var/log/toddy/phase2/hwdb-cache-installed-consumer.json').write_text(json.dumps({'scope':'Native owned hardware database vendor/refusal API/CLI and unchanged original Colord EDID fixture; no physical device test','native_consumer_exit':0,'original_colord_edid_case_exit':0,'old_nonlegal_regular_files_unchanged':receipt['old_nonlegal_regular_files_unchanged']},indent=2)+'\n')
PY
