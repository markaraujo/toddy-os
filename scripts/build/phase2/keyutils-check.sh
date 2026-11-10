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
from qualify_keyutils import CONFIG, digest, qualify

result, links, config = qualify(root)
chroot = ['chroot', str(target)]
env = {'PATH': '/usr/bin:/usr/sbin', 'LC_ALL': 'C.UTF-8',
       'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONNOUSERSITE': '1'}
status = subprocess.check_output(chroot + ['dpkg-query', '-W', '-f=${Status} ${Version}', 'keyutils'], text=True)
assert status == 'install ok installed 1.6.3-1+toddy1'
assert not subprocess.check_output(chroot + ['dpkg', '--audit'], text=True).strip()
subprocess.run(chroot + ['apt-get', 'check'], check=True)
for path, sha in result['stage_sha256'].items():
    if Path(path) != CONFIG:
        assert digest(target / path) == sha
links['usr/lib/libkeyutils.so'] = 'libkeyutils.so.1'
for path, destination in links.items():
    assert (target / path).readlink() == Path(destination)
assert (target / CONFIG).read_text() == config
docs = target / 'usr/share/doc/keyutils'
assert digest(docs / 'request-key.conf.upstream') == result['stage_sha256'][str(CONFIG)]
notice = json.loads((docs / 'source-notices/index.json').read_text())['sources'][0]['notices']
assert {'LICENCE.GPL', 'LICENCE.LGPL'} <= {Path(n['path']).name for n in notice}
assert all(digest(docs / 'source-notices' / n['sha256']) == n['sha256'] for n in notice)
conffiles = subprocess.check_output(chroot + ['dpkg-query', '-W', '-f=${Conffiles}', 'keyutils'], text=True)
assert any(line.split()[0] == '/etc/request-key.conf' for line in conffiles.splitlines() if line.strip())
assert (target / 'sbin').readlink() == Path('usr/sbin')
assert (target / 'bin').readlink() == Path('usr/bin')
assert os.access(target / 'usr/bin/keyctl', os.X_OK) and os.access(target / 'usr/sbin/key.dns_resolver', os.X_OK)

with tempfile.TemporaryDirectory(prefix='toddy-keyutils-', dir=target / 'tmp') as directory:
    tmp = Path(directory)
    os.chown(tmp, 101, 101)
    virtual = '/tmp/' + tmp.name
    env['HOME'] = virtual
    shutil.copyfile(root / 'scripts/build/phase2/keyutils-probe.c', tmp / 'probe.c')
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
            'toddy-keyutils', 'python3', '-c', launch]
    subprocess.run(base + ['/usr/bin/cc', '-Wall', '-Wextra', '-Werror',
                           virtual + '/probe.c', '-lkeyutils', '-o', virtual + '/probe'],
                   env=env, check=True, timeout=30)
    actual = subprocess.check_output(base + [virtual + '/probe'], env=env, text=True, timeout=15)
    assert actual == result['consumer']
    cli = subprocess.check_output(base + ['/usr/bin/keyctl', '--version'], env=env, text=True, timeout=10)
    assert cli == result['CLI']

libraries = subprocess.check_output(chroot + ['ldd', '/usr/bin/keyctl'], env=env, text=True)
assert 'libkeyutils.so.1 =>' in libraries and 'not found' not in libraries
assert subprocess.check_output(chroot + ['pkg-config', '--modversion', 'libkeyutils'],
                               env=env, text=True).strip() == '1.6.3'
space = os.statvfs(target)
assert space.f_bavail * space.f_frsize >= 16 * 1024**3
proof = {'C_consumer': actual, 'CLI': cli, 'stage_files': len(result['stage_sha256']),
         'stage_links': len(links), 'reviewed_conffile': True, 'demo_rules_omitted': 6,
         'original_configuration_retained': True, 'licenses_verified': True,
         'scope': 'UID101 with no effective capabilities, NNP, private devices and private network. Shared SDK and CLI version only.',
         'native_kernel_suite_pending': True, 'physical_machine_tested': False}
Path('/var/log/toddy/phase2/keyutils-installed-consumer.json').write_text(json.dumps(proof, indent=2) + '\n')
PYTEST
