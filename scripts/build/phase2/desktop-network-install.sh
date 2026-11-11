#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import hashlib,json,shutil,subprocess,sys
root=Path('/opt/toddy-build');target=Path('/mnt/lfs')
sys.path.insert(0,str(root/'scripts/build/phase2'))
from desktop_network import stage
destination=target/'sources/stage/phase2-toddy-desktop-network'
assert not destination.exists()
assert shutil.disk_usage(target).free>=16*1024**3+2*1024**2
for name in ['networkmanager','systemd','toddy-base-config']:
    assert subprocess.check_output(['chroot',str(target),'dpkg-query','-W','-f=${Status}',name],text=True)=='install ok installed'
assert (target/'etc/resolv.conf').is_symlink()
assert (target/'etc/resolv.conf').readlink()==Path('/run/systemd/resolve/stub-resolv.conf')
conffiles=stage(destination,root)
for p in destination.rglob('*'):
    if p.is_dir() and not p.is_symlink():continue
    actual=target/p.relative_to(destination)
    assert not actual.exists() and not actual.is_symlink(), 'Preserve existing owner configuration: '+str(actual)
command=['python3',str(root/'scripts/build/stage_package.py'),'toddy-desktop-network','0.2.0-1+toddy1',str(destination),
    '--architecture','all','--recipe','scripts/build/phase2/desktop-network-install.sh',
    '--depends','networkmanager (= 1.58.1-1+toddy1), systemd (>= 261.2-1+toddy3), toddy-base-config']
for name in conffiles:command+=['--conffile',name]
subprocess.run(command+['--install'],cwd=root,check=True)
Path('/var/log/toddy/phase2/desktop-network-policy-source.json').write_text(json.dumps({'scope':'Owned desktop network startup selection only; no chroot service activation or native runtime acceptance','conffiles':conffiles,'generator_sha256':hashlib.sha256((root/'scripts/build/phase2/desktop_network.py').read_bytes()).hexdigest(),'recovery':'README in native package; inverse marker conditions retain networkd recovery'},indent=2)+'\n')
PY
