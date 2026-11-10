#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
PYTHONDONTWRITEBYTECODE=1 python3 - <<'PYTEST'
import json
import os
import shlex
import shutil
from pathlib import Path
import subprocess
import sys
import tempfile

target = Path('/mnt/lfs')
root = Path('/opt/toddy-build')
sys.path.insert(0, str(root / 'scripts/build/phase2'))
from qualify_udisks2 import CONSUMER, GI_CONSUMER, digest, qualify

entries = qualify(root)
chroot = ['chroot', str(target)]
env = {'PATH': '/usr/bin:/usr/sbin', 'LC_ALL': 'C.UTF-8',
       'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONNOUSERSITE': '1'}
status = subprocess.check_output(chroot + ['dpkg-query', '-W', '-f=${Status} ${Version}', 'udisks2'], text=True)
assert status == 'install ok installed 2.11.2-1+toddy1'
assert not subprocess.check_output(chroot + ['dpkg', '--audit'], text=True).strip()
subprocess.run(chroot + ['apt-get', 'check'], check=True)
for path, row in entries.items():
    if 'sha256' in row:
        assert digest(target / path) == row['sha256']
    elif 'symlink' in row:
        assert (target / path).readlink() == Path(row['symlink'])
docs = target / 'usr/share/doc/udisks2'
notices = json.loads((docs / 'source-notices/index.json').read_text())['sources'][0]['notices']
assert any(Path(row['path']).name == 'COPYING' for row in notices)
assert all(digest(docs / 'source-notices' / row['sha256']) == row['sha256'] for row in notices)

config = '/etc/udisks2/udisks2.conf'
registered = subprocess.check_output(chroot + ['dpkg-query', '-W', '-f=${Conffiles}', 'udisks2'], text=True)
assert any(line.split()[0] == config for line in registered.splitlines() if line.strip())
with tempfile.TemporaryDirectory(prefix='toddy-udisks2-', dir=target / 'tmp') as directory:
    tmp = Path(directory)
    os.chown(tmp, 101, 101)
    virtual = '/tmp/' + tmp.name
    env['HOME'] = virtual
    shutil.copyfile(root / 'scripts/build/phase2/udisks2-probe.c', tmp / 'probe.c')
    flags = shlex.split(subprocess.check_output(chroot + ['pkg-config', '--cflags', '--libs', 'udisks2', 'gio-2.0'],
                                               env=env, text=True))
    wrapper = '''
set -euo pipefail
mount --make-rprivate /
mount -t tmpfs -o size=1m,nosuid,nodev tmpfs /mnt/lfs/run
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
            'toddy-udisks2', 'python3', '-c', launch]
    subprocess.run(base + ['/usr/bin/cc', '-Wall', '-Wextra', '-Werror', virtual + '/probe.c',
                           '-o', virtual + '/probe', *flags], env=env, check=True, timeout=30)
    actual = subprocess.check_output(base + [virtual + '/probe'], env=env, text=True, timeout=15)
    assert actual == CONSUMER
    probe = '''
import gi
gi.require_version('UDisks', '2.0')
from gi.repository import UDisks
assert gi.Repository.get_default().get_typelib_path('UDisks') == '/usr/lib/girepository-1.0/UDisks-2.0.typelib'
for cycle in range(2):
    manager = UDisks.ManagerSkeleton.new()
    manager.props.version = '2.11.2'
    assert manager.props.version == '2.11.2'
print('UDisks 2 GI metadata and two local manager objects passed')
'''
    actual_gi = subprocess.check_output(base + ['/usr/bin/python3', '-c', probe],
                                        env=env, text=True, timeout=15)
    assert actual_gi == GI_CONSUMER

linkage = subprocess.check_output(chroot + ['ldd', '/usr/libexec/udisks2/udisksd'], env=env, text=True)
assert 'not found' not in linkage
assert all(lib + ' =>' in linkage for lib in ('libblockdev.so.3', 'libudisks2.so.0', 'libpolkit-gobject-1.so.0'))
assert subprocess.check_output(chroot + ['pkg-config', '--modversion', 'udisks2'],
                               env=env, text=True).strip() == '2.11.2'
unit = 'udisks2.service'
assert not any(path.name == unit and path.is_symlink() for path in (target / 'etc/systemd/system').rglob('*'))
space = os.statvfs(target)
assert space.f_bavail * space.f_frsize >= 16 * 1024**3
proof = {'C_consumer': actual, 'GI_consumer': actual_gi, 'conffile': config,
         'notices_verified': len(notices), 'unit_enable_links_added': False,
         'scope': 'Installed local C/GI under UID101 and NNP with private runtime, devices and network. Daemon was not invoked.',
         'physical_machine_tested': False}
Path('/var/log/toddy/phase2/udisks2-installed-consumer.json').write_text(json.dumps(proof, indent=2) + '\n')
PYTEST
