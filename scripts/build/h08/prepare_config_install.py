#!/usr/bin/env python3
"""Preserve only exact unowned bootstrap configuration before package ownership."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[3]
TARGET=Path('/mnt/lfs')


def digest(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def preserve_bootstrap(target,expected,package_paths,owners):
    # Prevalidate every replacement before preserving/removing any input.
    for virtual in package_paths:
        path=target/virtual.lstrip('/')
        if not path.exists() and not path.is_symlink():continue
        if (virtual not in expected or path.is_symlink() or not path.is_file()
                or not path.resolve().is_relative_to(target.resolve())):
            raise ValueError('Unexpected existing configuration needs review: '+virtual)
        if owners.get(virtual) or digest(path)!=expected[virtual]:
            raise ValueError('Owned or changed bootstrap configuration: '+virtual)
    for virtual in expected:
        if virtual not in package_paths:raise ValueError('Replacement omits bootstrap configuration')
        path=target/virtual.lstrip('/')
        if not path.is_file() or path.is_symlink() or digest(path)!=expected[virtual]:
            raise ValueError('Missing/changed bootstrap input: '+virtual)
    recovery=target/'sources/recovery'
    if recovery.is_symlink() or not recovery.resolve().is_relative_to(target.resolve()):
        raise ValueError('Recovery directory escapes target')
    recovery.mkdir(mode=0o700,parents=True,exist_ok=True)
    if recovery.stat().st_uid!=os.geteuid() or recovery.stat().st_mode & 0o022:
        raise ValueError('Recovery directory must be owned and not publicly writable')
    backup=Path(tempfile.mkdtemp(prefix='h08-bootstrap-config-',dir=recovery))
    for virtual,sha in expected.items():
        destination=backup/virtual.lstrip('/');destination.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(target/virtual.lstrip('/'),destination)
        if digest(destination)!=sha:raise ValueError('Configuration backup hash mismatch')
        with destination.open('rb') as stream:os.fsync(stream.fileno())
    manifest=backup/'manifest.json'
    with manifest.open('w') as stream:
        json.dump({'files':expected,'scope':'Unowned bootstrap configuration before native package install'},stream,indent=2)
        stream.write('\n');stream.flush()
        os.fsync(stream.fileno())
    for directory in sorted([p for p in backup.rglob('*') if p.is_dir()],key=lambda p:len(p.parts),reverse=True)+[backup,recovery,recovery.parent]:
        descriptor=os.open(directory,os.O_RDONLY|os.O_DIRECTORY)
        try:os.fsync(descriptor)
        finally:os.close(descriptor)
    for virtual,sha in expected.items():
        if digest(target/virtual.lstrip('/'))!=sha:raise ValueError('Bootstrap input changed during backup')
    for virtual in expected:(target/virtual.lstrip('/')).unlink()
    descriptor=os.open(target/'etc',os.O_RDONLY|os.O_DIRECTORY)
    try:os.fsync(descriptor)
    finally:os.close(descriptor)
    return backup


def main():
    from require_gate import require_gate
    require_gate(ROOT,Path('/var/log/toddy/build'))
    subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
    from stage_config import LINKS
    sys.path.insert(0,str(ROOT/'scripts/build'))
    from source_notices import retain_source_notices
    stage=TARGET/'sources/stage/toddy-base-config'
    if stage.is_symlink() or not stage.is_dir() or (stage/'DEBIAN').exists():
        raise SystemExit('A fresh complete configuration stage is required')
    retain_source_notices(ROOT,TARGET,stage,'toddy-base-config',[])
    expected=json.loads((ROOT/'config/h08-bootstrap-config.json').read_text())['files']
    owners={}
    for listing in (TARGET/'var/lib/dpkg/info').glob('*.list'):
        for virtual in listing.read_text().splitlines():owners.setdefault(virtual,set()).add(listing.stem)
    package_paths={'/'+str(path.relative_to(stage)) for path in stage.rglob('*') if path.is_file() or path.is_symlink()}
    package_paths|={'/'+path for path in LINKS}
    backup=preserve_bootstrap(TARGET,expected,package_paths,owners)
    print(json.dumps({'preserved':list(expected),'backup':str(backup),'installed':False}))

if __name__=='__main__':main()
