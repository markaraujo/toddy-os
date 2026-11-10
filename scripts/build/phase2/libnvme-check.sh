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
from qualify_libnvme import digest, qualify

result, links = qualify(root)
chroot = ['chroot', str(target)]
env = {'PATH': '/usr/bin:/usr/sbin', 'LC_ALL': 'C.UTF-8',
       'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONNOUSERSITE': '1'}
status = subprocess.check_output(chroot + ['dpkg-query', '-W', '-f=${Status} ${Version}', 'libnvme'], text=True)
assert status == 'install ok installed 1.16.2-1+toddy1'
assert not subprocess.check_output(chroot + ['dpkg', '--audit'], text=True).strip()
subprocess.run(chroot + ['apt-get', 'check'], check=True)
for path, sha in result['stage_sha256'].items():
    assert digest(target / path) == sha
for path, destination in links.items():
    assert (target / path).readlink() == Path(destination)
docs = target / 'usr/share/doc/libnvme'
notices = json.loads((docs / 'source-notices/index.json').read_text())['sources'][0]['notices']
assert {Path(row['path']).name for row in notices} == {'COPYING', 'BSD-MIT', 'CC0'}
assert all(digest(docs / 'source-notices' / row['sha256']) == row['sha256'] for row in notices)

with tempfile.TemporaryDirectory(prefix='toddy-libnvme-', dir=target / 'tmp') as directory:
    tmp = Path(directory)
    os.chown(tmp, 101, 101)
    virtual = '/tmp/' + tmp.name
    env['HOME'] = virtual
    shutil.copyfile(root / 'scripts/build/phase2/libnvme-probe.c', tmp / 'probe.c')
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
            'toddy-libnvme', 'python3', '-c', launch]
    subprocess.run(base + ['/usr/bin/cc', '-Wall', '-Wextra', '-Werror', '-Wno-unused-parameter',
                           virtual + '/probe.c', '-lnvme-mi', '-lnvme', '-o', virtual + '/probe'],
                   env=env, check=True, timeout=30)
    actual = subprocess.check_output(base + [virtual + '/probe'], env=env, text=True, timeout=15)
    assert actual == result['consumer']

requirements = {'libnvme': ['libjson-c.so.5', 'libcrypto.so.4', 'libkeyutils.so.1'],
                'libnvme-mi': ['libdbus-1.so.3']}
for name, needed in requirements.items():
    libraries = subprocess.check_output(chroot + ['ldd', '/usr/lib/' + name + '.so.1'], env=env, text=True)
    assert 'not found' not in libraries and all(lib + ' =>' in libraries for lib in needed)
    assert subprocess.check_output(chroot + ['pkg-config', '--modversion', name], env=env, text=True).strip() == '1.16.2'
space = os.statvfs(target)
assert space.f_bavail * space.f_frsize >= 16 * 1024**3
proof = {'C_consumer': actual, 'stage_files': len(result['stage_sha256']), 'stage_links': len(links),
         'notices_verified': len(notices), 'runtime_links': requirements,
         'scope': 'UID101 with NNP, no effective capabilities, private devices and private network. Local UUID and MI object lifecycle only.',
         'physical_machine_tested': False}
Path('/var/log/toddy/phase2/libnvme-installed-consumer.json').write_text(json.dumps(proof, indent=2) + '\n')
PYTEST
