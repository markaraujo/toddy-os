#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
PYTHONDONTWRITEBYTECODE=1 python3 - <<'PYTEST'
import json
import lzma
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

target = Path('/mnt/lfs')
root = Path('/opt/toddy-build')
sys.path.insert(0, str(root / 'scripts/build/phase2'))
from qualify_cryptsetup import CONSUMER, FIXTURE, digest, qualify

entries = qualify(root)
chroot = ['chroot', str(target)]
env = {'PATH': '/usr/bin:/usr/sbin', 'LC_ALL': 'C.UTF-8',
       'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONNOUSERSITE': '1'}
status = subprocess.check_output(chroot + ['dpkg-query', '-W', '-f=${Status} ${Version}', 'cryptsetup'], text=True)
assert status == 'install ok installed 2.8.7-1+toddy1'
assert not subprocess.check_output(chroot + ['dpkg', '--audit'], text=True).strip()
subprocess.run(chroot + ['apt-get', 'check'], check=True)
for path, row in entries.items():
    if 'sha256' in row:
        assert digest(target / path) == row['sha256']
    elif 'symlink' in row:
        assert (target / path).readlink() == Path(row['symlink'])
docs = target / 'usr/share/doc/cryptsetup'
notices = json.loads((docs / 'source-notices/index.json').read_text())['sources'][0]['notices']
assert any(Path(row['path']).name == 'COPYING' for row in notices)
assert all(digest(docs / 'source-notices' / row['sha256']) == row['sha256'] for row in notices)

with tempfile.TemporaryDirectory(prefix='toddy-cryptsetup-', dir=target / 'tmp') as directory:
    tmp = Path(directory)
    os.chown(tmp, 101, 101)
    virtual = '/tmp/' + tmp.name
    env['HOME'] = virtual
    shutil.copyfile(root / 'scripts/build/phase2/cryptsetup-probe.c', tmp / 'probe.c')
    valid, invalid = tmp / 'valid.img', tmp / 'bad.img'
    with lzma.open(FIXTURE) as source, valid.open('xb') as file:
        shutil.copyfileobj(source, file)
    with invalid.open('xb') as file:
        file.truncate(16 * 1024**2)
    for file in (valid, invalid):
        file.chmod(0o444)
    fixtures = {path: digest(path) for path in (valid, invalid)}
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
            'toddy-cryptsetup', 'python3', '-c', launch]
    subprocess.run(base + ['/usr/bin/cc', '-Wall', '-Wextra', '-Werror',
                           virtual + '/probe.c', '-lcryptsetup', '-o', virtual + '/probe'],
                   env=env, check=True, timeout=30)
    actual = subprocess.check_output(base + [virtual + '/probe', virtual + '/valid.img', virtual + '/bad.img'],
                                     env=env, text=True, timeout=15)
    assert actual == CONSUMER
    cli = base + ['/usr/sbin/cryptsetup']
    bad = subprocess.run(cli + ['isLuks', virtual + '/bad.img'], env=env, capture_output=True, timeout=10)
    assert bad.returncode == 1
    assert subprocess.check_output(cli + ['luksUUID', virtual + '/valid.img'], env=env, text=True,
                                   timeout=10).strip() == '12a3a118-7039-4575-a649-3f559d8d87ee'
    assert fixtures == {path: digest(path) for path in fixtures}
    linkage = subprocess.check_output(base + ['/usr/bin/ldd', virtual + '/probe'],
                                      env=env, text=True, timeout=10)
    assert 'libcryptsetup.so.12 =>' in linkage and 'not found' not in linkage

assert subprocess.check_output(chroot + ['pkg-config', '--modversion', 'libcryptsetup'],
                               env=env, text=True).strip() == '2.8.7'
space = os.statvfs(target)
assert space.f_bavail * space.f_frsize >= 16 * 1024**3
proof = {'C_consumer': actual, 'CLI_invalid_header_exit': bad.returncode, 'fixture_bytes_unchanged': True,
         'notices_verified': len(notices),
         'scope': 'Installed shared Cryptsetup under UID101 and NNP. Read-only regular-file LUKS2 metadata with private devices and network. No unlocking, mapping or device writes.',
         'physical_machine_tested': False}
Path('/var/log/toddy/phase2/cryptsetup-installed-consumer.json').write_text(json.dumps(proof, indent=2) + '\n')
PYTEST
