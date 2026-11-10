#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
PYTHONDONTWRITEBYTECODE=1 python3 - <<'PYTEST'
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

target = Path('/mnt/lfs')
root = Path('/opt/toddy-build')
sys.path.insert(0, str(root / 'scripts/build/phase2'))
from qualify_lvm2 import digest, qualify

entries = qualify(root)
chroot = ['chroot', str(target)]
env = {'PATH': '/usr/bin:/usr/sbin', 'LC_ALL': 'C.UTF-8',
       'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONNOUSERSITE': '1'}
status = subprocess.check_output(chroot + ['dpkg-query', '-W', '-f=${Status} ${Version}', 'lvm2'], text=True)
assert status == 'install ok installed 2.03.42-1+toddy1'
assert not subprocess.check_output(chroot + ['dpkg', '--audit'], text=True).strip()
subprocess.run(chroot + ['apt-get', 'check'], check=True)
for path, row in entries.items():
    if 'sha256' in row:
        assert digest(target / path) == row['sha256']
    elif 'symlink' in row:
        assert (target / path).readlink() == Path(row['symlink'])
docs = target / 'usr/share/doc/lvm2'
notices = json.loads((docs / 'source-notices/index.json').read_text())['sources'][0]['notices']
assert {'COPYING', 'COPYING.BSD', 'COPYING.LIB'} <= {Path(row['path']).name for row in notices}
assert all(digest(docs / 'source-notices' / row['sha256']) == row['sha256'] for row in notices)

config = {f'/{path}' for path, row in entries.items() if path.startswith('etc/lvm/') and 'sha256' in row}
registered = subprocess.check_output(chroot + ['dpkg-query', '-W', '-f=${Conffiles}', 'lvm2'], text=True)
assert len(config) == 10 and {line.split()[0] for line in registered.splitlines() if line.strip()} == config
units = ['blk-availability.service', 'lvm-devices-import.path', 'lvm-devices-import.service']
for unit in units:
    assert (target / 'usr/lib/systemd/system' / unit).is_file()
    assert not any(p.name == unit and p.is_symlink() for p in (target / 'etc/systemd/system').rglob('*'))

with tempfile.TemporaryDirectory(prefix='toddy-lvm2-', dir=target / 'tmp') as directory:
    tmp = Path(directory)
    os.chown(tmp, 101, 101)
    virtual = '/tmp/' + tmp.name
    env['HOME'] = virtual
    shutil.copyfile(root / 'scripts/build/phase2/lvm2-probe.c', tmp / 'probe.c')
    wrapper = '''
set -euo pipefail
mount --make-rprivate /
mount -t tmpfs -o size=1m,nosuid,nodev tmpfs /mnt/lfs/dev
for name in null zero random urandom; do
    touch "/mnt/lfs/dev/$name"
    mount --bind "/dev/$name" "/mnt/lfs/dev/$name"
done
mount -t proc -o nosuid,nodev,noexec proc /mnt/lfs/proc
exec chroot --userspec=101:101 /mnt/lfs "$@"
'''
    launch = '''
import ctypes, os, sys
assert os.geteuid() == os.getegid() == 101
assert ctypes.CDLL(None, use_errno=True).prctl(38, 1, 0, 0, 0) == 0
status = open('/proc/self/status').read()
assert 'CapEff:\\t0000000000000000' in status and 'NoNewPrivs:\\t1' in status
os.execv(sys.argv[1], sys.argv[1:])
'''
    base = ['unshare', '--mount', '--pid', '--fork', '--net', 'bash', '-c', wrapper,
            'toddy-lvm2', 'python3', '-c', launch]
    subprocess.run(base + ['/usr/bin/cc', '-Wall', '-Wextra', '-Werror',
                           virtual + '/probe.c', '-ldevmapper', '-o', virtual + '/probe'],
                   env=env, check=True, timeout=30)
    subprocess.run(base + [virtual + '/probe'], env=env, check=True, timeout=15)
    linkage = subprocess.check_output(base + ['/usr/bin/ldd', virtual + '/probe'],
                                      env=env, text=True, timeout=10)
    assert 'libdevmapper.so.1.02 =>' in linkage and 'not found' not in linkage

linkage = subprocess.check_output(chroot + ['ldd', '/usr/sbin/lvm'], env=env, text=True)
assert 'not found' not in linkage
assert all(lib + ' =>' in linkage for lib in ('libdevmapper.so.1.02', 'libaio.so.1', 'libnvme.so.1', 'libudev.so.1'))
assert subprocess.check_output(chroot + ['pkg-config', '--modversion', 'devmapper'], env=env, text=True).strip().startswith('1.02.')
space = os.statvfs(target)
assert space.f_bavail * space.f_frsize >= 16 * 1024**3
proof = {'C_consumer': 'Two Device Mapper name escape and pool lifecycles passed',
         'notices_verified': len(notices), 'conffiles': len(config), 'units_present_and_disabled': units,
         'scope': 'Installed Device Mapper SDK in private device and network namespaces under UID101 and NNP. No mapper device, volume or activation test.',
         'physical_machine_tested': False}
Path('/var/log/toddy/phase2/lvm2-installed-consumer.json').write_text(json.dumps(proof, indent=2) + '\n')
PYTEST
