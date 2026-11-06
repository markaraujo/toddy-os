#!/usr/bin/env python3
"""Build and inspect an own disposable archive without installing a package."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
from package_backend import PackageBackend


def main():
    subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
    backend=PackageBackend()
    if not backend.native:raise SystemExit('Accepted source-built native Dpkg required')
    status=backend.target/'var/lib/dpkg/status'
    before=hashlib.file_digest(status.open('rb'),'sha256').hexdigest()
    with tempfile.TemporaryDirectory(prefix='backend-native-',dir=backend.target/'sources/stage') as staging, tempfile.TemporaryDirectory(prefix='toddy-backend-') as output:
        stage=Path(staging)
        (stage/'DEBIAN').mkdir()
        (stage/'usr/share/toddy-probe').mkdir(parents=True)
        (stage/'DEBIAN/control').write_text('Package: toddy-native-backend-probe\nVersion: 1\nArchitecture: all\nMaintainer: Toddy OS <noreply@example.invalid>\nDescription: disposable archive backend probe\n')
        (stage/'usr/share/toddy-probe/value').write_text('native-backend\n')
        archive=Path(output)/'probe.deb'
        backend.build(stage,archive)
        temporary=backend.workspace()/'backend-probe-inspection.deb'
        if temporary.exists() or temporary.is_symlink():raise SystemExit('Unexpected existing inspection input')
        shutil.copy2(archive,temporary)
        try:
            virtual='/sources/native-package-output/'+temporary.name
            name=backend.run('dpkg-deb','--field',virtual,'Package',capture_output=True,text=True).stdout.strip()
            listing=backend.run('dpkg-deb','--contents',virtual,capture_output=True,text=True).stdout
            if name!='toddy-native-backend-probe' or './usr/share/toddy-probe/value' not in listing:
                raise SystemExit('Native archive metadata/content verification failed')
        finally:temporary.unlink()
        if hashlib.file_digest(status.open('rb'),'sha256').hexdigest()!=before:
            raise SystemExit('Native package database changed during archive-only probe')
        print(json.dumps({'backend':backend.record,'archive_sha256':hashlib.file_digest(archive.open('rb'),'sha256').hexdigest(),
                          'package':name,'main_database_unchanged':True,'installed':False}))


if __name__=='__main__':main()
