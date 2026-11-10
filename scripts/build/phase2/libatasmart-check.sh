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
from qualify_libatasmart import FIXTURES, INPUT, LIBRARY_ALIASES, digest, qualify

result = qualify(root)
chroot = ['chroot', str(target)]
env = {'PATH': '/usr/bin:/usr/sbin', 'LC_ALL': 'C.UTF-8',
       'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONNOUSERSITE': '1'}
status = subprocess.check_output(chroot + ['dpkg-query', '-W', '-f=${Status} ${Version}', 'libatasmart'], text=True)
assert status == 'install ok installed 0.19-1+toddy1'
assert not subprocess.check_output(chroot + ['dpkg', '--audit'], text=True).strip()
subprocess.run(chroot + ['apt-get', 'check'], check=True)
for path, sha in result['stage_sha256'].items():
    assert digest(target / path) == sha
for path in LIBRARY_ALIASES:
    assert (target / path).readlink() == Path('libatasmart.so.4.0.5')

docs = target / 'usr/share/doc/libatasmart'
index = json.loads((docs / 'source-notices/index.json').read_text())
notices = index['sources'][0]['notices']
assert len(notices) == 5 and all(digest(docs / 'source-notices' / n['sha256']) == n['sha256'] for n in notices)
assert digest(docs / 'LGPL-2.1.txt') == digest(root / 'LICENSES/third-party/LGPL-2.1.txt')
assert (docs / 'copyright').read_bytes().endswith((docs / 'LGPL-2.1.txt').read_bytes())
with tempfile.TemporaryDirectory(prefix='toddy-libatasmart-', dir=target / 'tmp') as directory:
    tmp = Path(directory)
    os.chown(tmp, 101, 101)
    virtual = '/tmp/' + tmp.name
    env['HOME'] = virtual
    shutil.copyfile(root / 'scripts/build/phase2/libatasmart-probe.c', tmp / 'probe.c')
    for name, sha in FIXTURES.items():
        path = tmp / name
        shutil.copyfile(INPUT / 'blob-examples' / name, path)
        assert digest(path) == sha
    first = next(iter(FIXTURES))
    (tmp / 'truncated').write_bytes((tmp / first).read_bytes()[:-1])

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
            'toddy-libatasmart', 'python3', '-c', launch]
    subprocess.run(base + ['/usr/bin/cc', '-Wall', '-Wextra', '-Werror', '-include', 'stddef.h',
                           virtual + '/probe.c', '-latasmart', '-o', virtual + '/probe'],
                   env=env, check=True, timeout=30)
    actual = subprocess.check_output(base + [virtual + '/probe', *[virtual + '/' + n for n in FIXTURES]],
                                     env=env, text=True, timeout=15)
    assert actual == result['consumer']
    cli = base + ['/usr/sbin/skdump', '--can-smart']
    bad = subprocess.run(cli + ['--load=' + virtual + '/truncated'], env=env,
                         capture_output=True, text=True, timeout=10)
    assert bad.returncode == 1 and bad.stdout == '' and 'Failed to set blob:' in bad.stderr
    assert subprocess.check_output(cli + ['--load=' + virtual + '/' + first],
                                   env=env, text=True, timeout=10) == 'YES\n'

libraries = subprocess.check_output(chroot + ['ldd', '/usr/lib/libatasmart.so.4'], env=env, text=True)
assert 'libudev.so.1 =>' in libraries and 'not found' not in libraries
assert subprocess.check_output(chroot + ['pkg-config', '--modversion', 'libatasmart'],
                               env=env, text=True).strip() == '0.19'
space = os.statvfs(target)
assert space.f_bavail * space.f_frsize >= 16 * 1024**3
proof = {'C_consumer': actual, 'CLI_refusal_exit': bad.returncode, 'CLI_recovery': 'YES',
         'stage_files': len(result['stage_sha256']), 'library_aliases': len(LIBRARY_ALIASES),
         'notices_verified': len(notices), 'full_LGPL_2_1_text': True, 'libudev_resolution': True,
         'scope': 'UID101 with no effective capabilities, NNP, private devices and private network. Bundled SMART blob parser only.',
         'physical_machine_tested': False}
Path('/var/log/toddy/phase2/libatasmart-installed-consumer.json').write_text(json.dumps(proof, indent=2) + '\n')
PYTEST
