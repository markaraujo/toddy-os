"""Route package operations through accepted native tools after bootstrap."""
import hashlib
import json
import os
import stat
from pathlib import Path
import shutil
import subprocess


class PackageBackend:
    def __init__(self, target=Path('/mnt/lfs'), records=Path('/var/log/toddy/build')):
        self.target = target
        marker = records/'h07-dpkg.success.json'
        self.native = marker.is_file()
        self.record = {'kind': 'builder-bootstrap-dpkg'}
        if self.native:
            accepted = json.loads(marker.read_text())
            if accepted.get('recipe_exit') != 0 or accepted.get('postcheck_exit') != 0:
                raise SystemExit('Native Dpkg acceptance record is invalid')
            executable = target/'usr/bin/dpkg'
            version = self.run('dpkg', '--version', capture_output=True, text=True).stdout.splitlines()[0]
            if '1.22.22' not in version:
                raise SystemExit('Unexpected native Dpkg version')
            self.record = {'kind': 'source-built-native-dpkg', 'version': version,
                           'executable_sha256': hashlib.file_digest(executable.open('rb'), 'sha256').hexdigest(),
                           'acceptance_sha256': hashlib.file_digest(marker.open('rb'), 'sha256').hexdigest()}

    def run(self, program, *arguments, **kwargs):
        command = [program, *arguments]
        if self.native:
            command = ['/usr/sbin/chroot', str(self.target), '/usr/bin/env', '-i',
                       'HOME=/root', 'PATH=/usr/bin:/usr/sbin', 'LC_ALL=C',
                       '/usr/bin/'+program, *arguments]
        return subprocess.run(command, check=True, **kwargs)

    def workspace(self):
        workspace = self.target/'sources/native-package-output'
        # Validate the directory itself before copying/extracting any archive.
        if workspace.is_symlink():
            raise SystemExit('Native workspace must be a root-owned private directory')
        workspace.mkdir(mode=0o700, exist_ok=True)
        current = workspace.lstat()
        if (not stat.S_ISDIR(current.st_mode) or current.st_uid != os.geteuid()
                or stat.S_IMODE(current.st_mode) != 0o700):
            raise SystemExit('Native workspace must be a root-owned private directory')
        return workspace

    def build(self, stage, archive):
        if not self.native:
            self.run('dpkg-deb', '--build', str(stage), str(archive))
            return
        workspace = self.workspace()
        output = workspace/archive.name
        if output.exists() or output.is_symlink():
            raise SystemExit('Preserve existing native package output before retry')
        self.run('dpkg-deb', '--build', '/'+str(stage.relative_to(self.target)),
                 '/'+str(output.relative_to(self.target)))
        shutil.copy2(output, archive)
        if hashlib.file_digest(output.open('rb'), 'sha256').hexdigest() != hashlib.file_digest(archive.open('rb'), 'sha256').hexdigest():
            raise SystemExit('Native package transfer hash mismatch')
        output.unlink()

    def install(self, archive):
        if not self.native:
            self.run('dpkg', '--root='+str(self.target), '--force-confold', '--force-confdef', '--install', str(archive))
            return
        workspace = self.workspace()
        temporary = workspace/archive.name
        if temporary.exists() or temporary.is_symlink():
            raise SystemExit('Preserve existing native package input before retry')
        shutil.copy2(archive, temporary)
        try:
            self.run('dpkg', '--force-confold', '--force-confdef', '--install', '/'+str(temporary.relative_to(self.target)))
        finally:
            temporary.unlink()
