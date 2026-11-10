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
from qualify_libaio import CONSUMER, digest, qualify

entries = qualify(root)
chroot = ['chroot', str(target)]
env = {'PATH': '/usr/bin:/usr/sbin', 'LC_ALL': 'C.UTF-8',
       'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONNOUSERSITE': '1'}
status = subprocess.check_output(chroot + ['dpkg-query', '-W', '-f=${Status} ${Version}', 'libaio'], text=True)
assert status == 'install ok installed 0.3.113-1+toddy1'
assert not subprocess.check_output(chroot + ['dpkg', '--audit'], text=True).strip()
subprocess.run(chroot + ['apt-get', 'check'], check=True)
for path, row in entries.items():
    if 'sha256' in row:
        assert digest(target / path) == row['sha256']
    elif 'symlink' in row:
        assert (target / path).readlink() == Path(row['symlink'])
docs = target / 'usr/share/doc/libaio'
notices = json.loads((docs / 'source-notices/index.json').read_text())['sources'][0]['notices']
assert any(Path(row['path']).name == 'COPYING' for row in notices)
assert all(digest(docs / 'source-notices' / row['sha256']) == row['sha256'] for row in notices)

with tempfile.TemporaryDirectory(prefix='toddy-libaio-', dir=target / 'tmp') as directory:
    tmp = Path(directory)
    os.chown(tmp, 101, 101)
    virtual = '/tmp/' + tmp.name
    env['HOME'] = virtual
    shutil.copyfile(root / 'scripts/build/phase2/libaio-probe.c', tmp / 'probe.c')
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
            'toddy-libaio', 'python3', '-c', launch]
    subprocess.run(base + ['/usr/bin/cc', '-Wall', '-Wextra', '-Werror',
                           virtual + '/probe.c', '-laio', '-o', virtual + '/probe'],
                   env=env, check=True, timeout=30)
    actual = subprocess.check_output(base + [virtual + '/probe'], env=env, text=True, timeout=15)
    assert actual == CONSUMER
    linkage = subprocess.check_output(base + ['/usr/bin/ldd', virtual + '/probe'],
                                      env=env, text=True, timeout=10)
    assert 'libaio.so.1 =>' in linkage and 'not found' not in linkage

space = os.statvfs(target)
assert space.f_bavail * space.f_frsize >= 16 * 1024**3
proof = {'C_consumer': actual, 'notices_verified': len(notices),
         'scope': 'Installed shared LibAIO under UID101, NNP, private device and network namespaces. Real anonymous regular file AIO and two invalid-depth refusals.',
         'physical_machine_tested': False}
Path('/var/log/toddy/phase2/libaio-installed-consumer.json').write_text(json.dumps(proof, indent=2) + '\n')
PYTEST
