"""Promote only the qualified Samba client through the native package backend."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

from package_copyright import write_copyright
from qualify_samba_client import WORK, digest, qualify
from verify_stage import inspect_stage

ROOT = Path('/opt/toddy-build')
TARGET = Path('/mnt/lfs')
ARCHIVE = 'samba-4.24.6.tar.gz'
DEPENDENCIES = ('glibc (>= 2.44-1+toddy1), popt (= 1.19-1+toddy1), readline (= 8.3-1+toddy1), '
                'libarchive (= 3.8.11-1+toddy1), gnutls (= 3.8.13-1+toddy1), libcap (= 2.78-1+toddy1), '
                'zlib (= 1.3.2-1+toddy1), e2fsprogs (= 1.47.4-1+toddy1), mitkrb (= 1.22.2-1+toddy1), '
                'icu (= 78.3-1+toddy1), systemd (>= 261.2-1+toddy3)')


def main():
    entries = qualify()
    archive = Path('/run/toddy-samba-client-1') / ARCHIVE
    row = next(r for r in json.loads((ROOT / 'config/phase2/sources.lock.json').read_text())['components'] if r['name'] == 'samba')
    assert digest(archive) == row['sha256']
    promoted = WORK / 'promotion-samba-client-1'
    destination = TARGET / 'sources/stage/phase2-samba-client'
    source_alias = TARGET / 'sources' / ARCHIVE
    assert all(not os.path.lexists(p) for p in (promoted, destination, source_alias))
    assert not Path('/var/cache/toddy/packages/samba-client_4.24.6-1+toddy1_amd64.deb').exists()
    fs = os.statvfs(TARGET)
    assert fs.f_bavail * fs.f_frsize >= 16 * 1024**3 + 28 * 1024**2
    shutil.copytree(WORK / 'stage-client-2', promoted, symlinks=True)
    assert inspect_stage(promoted)['entries'] == entries
    config = promoted / 'etc/samba/smb.conf'
    config.parent.mkdir(parents=True)
    config.write_text('[global]\nclient min protocol = SMB2_02\n')
    config.chmod(0o644)
    source_alias.touch(mode=0o644)
    subprocess.run(['mount', '--bind', str(archive), str(source_alias)], check=True)
    subprocess.run(['mount', '-o', 'remount,bind,ro,nosuid,nodev,noexec', str(source_alias)], check=True)
    assert digest(source_alias) == row['sha256']
    destination.mkdir(mode=0o755)
    subprocess.run(['mount', '--bind', str(promoted), str(destination)], check=True)
    write_copyright(destination, 'samba-client', [ARCHIVE])
    docs = destination / 'usr/share/doc/samba-client'
    (docs / 'README.Toddy').write_text('Samba 4.24.6 client library, CLI and complete linked runtime closure. '
        'Native C lifecycle and private authenticated SMB upload/download/delete, wrong-auth refusal, Stop and reconnect verified. '
        'The private test server is excluded from this package. GNOME integration remains pending.\n')
    subprocess.run([sys.executable, str(ROOT / 'scripts/build/stage_package.py'), 'samba-client',
                    '4.24.6-1+toddy1', str(destination), '--source', ARCHIVE,
                    '--recipe', 'scripts/build/phase2/samba-client-install.sh', '--depends', DEPENDENCIES,
                    '--conffile', '/etc/samba/smb.conf', '--install'], cwd=ROOT, check=True)


if __name__ == '__main__':
    main()
