"""Prepare a new readonly independent test input, preserving parked native fixtures."""
from pathlib import Path
import fcntl,hashlib,json,os,shutil,subprocess
root=Path('/opt/toddy-build');base=Path('/mnt/lfs/sources/phase2');logs=Path('/var/log/toddy/phase2')
subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
source=base/'inputs/localsearch-bus-address-1';work=base/'work/localsearch-bus-address-1';receipt=logs/'localsearch-bus-address-prepared-1.json';assert not any(p.exists() for p in [source,work,receipt]);s=os.statvfs('/mnt/lfs');assert s.f_bavail*s.f_frsize>16*1024**3+4*1024**2
original=base/'inputs/localsearch-3.11.1/utils/trackertestutils';config=base/'work/localsearch-1/compile/tests/test-bus.conf';assert '<listen>unix:tmpdir=./</listen>' in config.read_text()
source.mkdir();(source/'utils').mkdir();shutil.copytree(original,source/'utils/trackertestutils');shutil.copyfile(config,source/'test-bus.conf');shutil.copyfile(root/'scripts/build/phase2/localsearch_bus_address_probe.py',source/'probe.py');(source/'bin').mkdir()
(source/'bin/dbus-daemon').write_text('#!/bin/bash\nset -euo pipefail\n[[ $(id -u) == 101 && $XDG_RUNTIME_DIR == /build/run ]]\nexec /usr/bin/dbus-daemon "$@" --address=unix:tmpdir=/build/run\n')
(source/'toddy-build.sh').write_text('#!/bin/bash\nset -euo pipefail\nexport PYTHONDONTWRITEBYTECODE=1\ncd /src\nexec python3 /src/probe.py\n')
def manifest(directory):return {str(p.relative_to(directory)):hashlib.sha256(p.read_bytes()).hexdigest() for p in directory.rglob('*') if p.is_file() and not p.is_symlink()}
assert manifest(original)==manifest(source/'utils/trackertestutils')
proof={'scope':'Independent D-Bus --address override only; original LocalSearch3.11.1 helper/config bytes copied unchanged, no parked native execution/retry. Original shutil.which selects declared wrapper through private PATH; global daemon/config/permissions unchanged.','source':str(source),'work':str(work),'inputs':manifest(source),'original_helper_files':len(manifest(original)),'original_config_sha256':hashlib.sha256(config.read_bytes()).hexdigest(),'references':['LocalSearch3.11.1 utils/trackertestutils/dbusdaemon.py _dbus_daemon_path/start','D-Bus1.16.2 bus/main.c --address parser']}
for p in source.rglob('*'):p.chmod(0o555 if p.is_dir() else 0o444)
(source/'bin/dbus-daemon').chmod(0o555);source.chmod(0o555);work.mkdir();os.chown(work,101,101);receipt.write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps({'prepared':True,'helper_files':proof['original_helper_files']}))
