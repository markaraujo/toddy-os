#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'CHECK'
from pathlib import Path
import hashlib,json,subprocess,stat
root=Path('/mnt/lfs');binary=root/'usr/bin/bwrap'
proof=json.loads((root/'sources/phase2/work/bubblewrap-1/test-results.json').read_text())['qualification']
assert stat.S_IMODE(binary.stat().st_mode)==0o755 and binary.stat().st_uid==0
assert hashlib.sha256(binary.read_bytes()).hexdigest()==proof['binary_sha256']
assert subprocess.check_output(['chroot',str(root),'dpkg-query','-W','-f=${Status} ${Version}','bubblewrap'],text=True)=='install ok installed 0.11.2-1+toddy1'
assert subprocess.check_output(['chroot',str(root),'/usr/bin/bwrap','--version'],text=True).strip()=='bubblewrap 0.11.2'
assert not subprocess.check_output(['chroot',str(root),'dpkg','--audit'],text=True).strip()
subprocess.run(['chroot',str(root),'apt-get','check'],check=True)
Path('/var/log/toddy/phase2/bubblewrap-installed-consumer.json').write_text(json.dumps({'scope':'Installed root-owned0755 executable byte-identical to actual native7.1.8 namespace-tested binary; version/loader0, no unsupported Ubuntu namespace replay or graphical acceptance',
'native_tested_binary_sha256':proof['binary_sha256'],'installed_binary_identical':True,'native_namespace_consumer_exit':0,
'installed_version_exit':0,'setuid_or_setgid':False,'native_runtime_report_sha256':proof['native_report_sha256']},indent=2)+'\n')
CHECK
