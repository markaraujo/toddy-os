#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
PYTHONDONTWRITEBYTECODE=1 python3 - <<'PYTEST'
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

target = Path('/mnt/lfs')
root = Path('/opt/toddy-build')
sys.path.insert(0, str(root / 'scripts/build/phase2'))
from qualify_libblockdev import CONSUMER, digest, qualify

entries = qualify(root)
chroot = ['chroot', str(target)]
env = {'PATH': '/usr/bin:/usr/sbin', 'LC_ALL': 'C.UTF-8',
       'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONNOUSERSITE': '1'}
status = subprocess.check_output(chroot + ['dpkg-query', '-W', '-f=${Status} ${Version}', 'libblockdev'], text=True)
assert status == 'install ok installed 3.5.0-1+toddy1'
assert not subprocess.check_output(chroot + ['dpkg', '--audit'], text=True).strip()
subprocess.run(chroot + ['apt-get', 'check'], check=True)
for path, row in entries.items():
    if 'sha256' in row:
        assert digest(target / path) == row['sha256']
    elif 'symlink' in row:
        assert (target / path).readlink() == Path(row['symlink'])
docs = target / 'usr/share/doc/libblockdev'
notices = json.loads((docs / 'source-notices/index.json').read_text())['sources'][0]['notices']
assert any(Path(row['path']).name == 'LICENSE' for row in notices)
assert all(digest(docs / 'source-notices' / row['sha256']) == row['sha256'] for row in notices)

config = '/etc/libblockdev/3/conf.d/00-default.cfg'
registered = subprocess.check_output(chroot + ['dpkg-query', '-W', '-f=${Conffiles}', 'libblockdev'], text=True)
assert any(line.split()[0] == config for line in registered.splitlines() if line.strip())
with tempfile.TemporaryDirectory(prefix='toddy-libblockdev-', dir=target / 'tmp') as directory:
    tmp = Path(directory)
    os.chown(tmp, 101, 101)
    env['HOME'] = '/tmp/' + tmp.name
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
            'toddy-libblockdev', 'python3', '-c', launch]
    probe = '''
from importlib import import_module
import gi
gi.require_version('BlockDev', '3.0')
from gi.repository import BlockDev
assert gi.Repository.get_default().get_typelib_path('BlockDev') == '/usr/lib/girepository-1.0/BlockDev-3.0.typelib'
assert import_module('gi.overrides.BlockDev').__file__ == '/usr/lib/python3.14/site-packages/gi/overrides/BlockDev.py'
crypto = BlockDev.PluginSpec(name=BlockDev.Plugin.CRYPTO, so_name=None)
for cycle in range(2):
    assert BlockDev.reinit([crypto], True, None)
    assert BlockDev.get_available_plugin_names() == ['crypto']
    assert BlockDev.crypto_is_tech_avail(BlockDev.CryptoTech.LUKS, BlockDev.CryptoTechMode.QUERY)
    assert BlockDev.reinit([], True, None)
    assert BlockDev.get_available_plugin_names() == []
print('BlockDev 3 GI and two local crypto plugin load/query/unload cycles passed')
'''
    actual = subprocess.check_output(base + ['/usr/bin/python3', '-c', probe],
                                     env=env, text=True, timeout=20)
    assert actual.strip() == CONSUMER

linkage = subprocess.check_output(chroot + ['ldd', '/usr/lib/libbd_crypto.so.3'], env=env, text=True)
assert 'libcryptsetup.so.12 =>' in linkage and 'not found' not in linkage
assert subprocess.check_output(chroot + ['pkg-config', '--modversion', 'blockdev'],
                               env=env, text=True).strip() == '3.5.0'
space = os.statvfs(target)
assert space.f_bavail * space.f_frsize >= 16 * 1024**3
proof = {'consumer': actual, 'conffile': config, 'notices_verified': len(notices),
         'scope': 'Installed Libblockdev GI and crypto plugin lifecycle under UID101 and NNP, with private devices and network. No storage action or daemon.',
         'physical_machine_tested': False}
Path('/var/log/toddy/phase2/libblockdev-installed-consumer.json').write_text(json.dumps(proof, indent=2) + '\n')
PYTEST
