"""Check the installed client bytes, owned ABI, notices and unprivileged API."""
import json
import os
from pathlib import Path
import subprocess
import tempfile

from qualify_samba_client import LOG, digest, qualify

TARGET = Path('/mnt/lfs')


def main():
    entries = qualify()
    chroot = ['chroot', str(TARGET)]
    status = subprocess.check_output(chroot + ['dpkg-query', '-W', '-f=${Status} ${Version}', 'samba-client'], text=True)
    assert status == 'install ok installed 4.24.6-1+toddy1'
    assert not subprocess.check_output(chroot + ['dpkg', '--audit'], text=True).strip()
    subprocess.run(chroot + ['apt-get', 'check'], check=True)
    for relative, row in entries.items():
        installed = TARGET / relative
        if 'sha256' in row:
            assert digest(installed) == row['sha256']
        if 'symlink' in row:
            assert installed.readlink() == Path(row['symlink'])
    notice_dir = TARGET / 'usr/share/doc/samba-client/source-notices'
    notices = json.loads((notice_dir / 'index.json').read_text())['sources'][0]['notices']
    assert len(notices) >= 17
    assert all(digest(notice_dir / row['sha256']) == row['sha256'] for row in notices)
    conffiles = subprocess.check_output(chroot + ['dpkg-query', '-W', '-f=${Conffiles}', 'samba-client'], text=True)
    assert {row.split()[0] for row in conffiles.splitlines() if row.strip()} == {'/etc/samba/smb.conf'}
    assert (TARGET / 'etc/samba/smb.conf').read_text() == '[global]\nclient min protocol = SMB2_02\n'
    env = {'PATH':'/usr/bin:/usr/sbin', 'LC_ALL':'C.UTF-8', 'PYTHONDONTWRITEBYTECODE':'1', 'PYTHONNOUSERSITE':'1'}
    wrapper = '''
set -euo pipefail
mount --make-rprivate /
ip link set dev lo up
mount -t tmpfs -o size=1m,nosuid,nodev tmpfs /mnt/lfs/dev
for name in null zero random urandom; do
 touch "/mnt/lfs/dev/$name"
 mount --bind "/dev/$name" "/mnt/lfs/dev/$name"
done
mount -t proc -o nosuid,nodev,noexec proc /mnt/lfs/proc
exec setpriv --no-new-privs chroot --userspec=101:101 /mnt/lfs python3 -c "$1"
'''
    consumer = '''
import ctypes, errno, json, os, subprocess
assert os.getuid() == os.geteuid() == 101
status = open('/proc/self/status').read()
assert 'CapEff:\\t0000000000000000' in status and 'NoNewPrivs:\\t1' in status
lib = ctypes.CDLL('libsmbclient.so.0', use_errno=True)
lib.smbc_version.restype = ctypes.c_char_p
assert lib.smbc_version() == b'4.24.6'
lib.smbc_new_context.restype = ctypes.c_void_p
lib.smbc_init_context.argtypes = [ctypes.c_void_p]
lib.smbc_init_context.restype = ctypes.c_void_p
lib.smbc_setConfiguration.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
lib.smbc_free_context.argtypes = [ctypes.c_void_p, ctypes.c_int]
ctypes.set_errno(0)
assert not lib.smbc_init_context(None) and ctypes.get_errno() == errno.EBADF
for index in range(2):
 context = lib.smbc_new_context()
 assert context
 assert lib.smbc_setConfiguration(context, b'/etc/samba/smb.conf') == 0
 assert lib.smbc_init_context(context) == context
 assert lib.smbc_free_context(context, 1) == 0
assert subprocess.check_output(['smbclient', '--version'], text=True).strip() == 'Version 4.24.6'
assert subprocess.check_output(['pkg-config', '--modversion', 'smbclient'], text=True).strip() == '0.8.1'
linkage = subprocess.check_output(['ldd', '/usr/bin/smbclient'], text=True)
assert 'not found' not in linkage and '/build/' not in linkage and '/src/' not in linkage
assert '/usr/lib/samba/' in linkage
print(json.dumps({'version':'4.24.6','uid':101,'null_context_refused':True,'context_lifecycles':2,'installed_linkage_resolved':True}))
'''
    with tempfile.TemporaryDirectory(prefix='toddy-samba-', dir=TARGET / 'tmp') as directory:
        os.chown(directory, 101, 101)
        env['HOME'] = '/tmp/' + Path(directory).name
        actual = subprocess.check_output(['unshare', '--mount', '--pid', '--fork', '--net', 'bash', '-c', wrapper,
                                          'toddy-samba-client', consumer], env=env, text=True, timeout=30)
    result = json.loads(actual)
    assert result['context_lifecycles'] == 2 and result['null_context_refused']
    space = os.statvfs(TARGET)
    assert space.f_bavail * space.f_frsize >= 16 * 1024**3
    result.update(notices_verified=len(notices), scope='Installed owned SDK and CLI under UID101, NNP and private loopback. Same payload as completed staged SMB exchange. GNOME and physical acceptance pending.')
    (LOG / 'samba-client-installed-consumer.json').write_text(json.dumps(result, indent=2) + '\n')


if __name__ == '__main__':
    main()
