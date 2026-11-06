#!/usr/bin/env python3
"""Compare cached Tcl test files with frozen originals and two exact patches."""
import hashlib
import json
from pathlib import Path
import subprocess
import tarfile
import tempfile
from locked_inputs import locked_source

ROOT=Path(__file__).resolve().parents[2]
SOURCES=Path('/mnt/lfs/sources')
NATIVE=SOURCES/'db-5.3.28'

def digest(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def main():
    subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
    names=['db5.3_5.3.28+dfsg2.orig.tar.xz','db5.3_5.3.28+dfsg2-12.debian.tar.xz','db-5.3.28-test142-environment-1.patch']
    for name in names:
        if digest(SOURCES/name)!=locked_source(ROOT,name)['sha256']:
            raise SystemExit('Frozen test input mismatch: '+name)
    with tempfile.TemporaryDirectory(prefix='toddy-db-tcl-reference-') as directory:
        reference=Path(directory)
        expected=set()
        with tarfile.open(SOURCES/names[0]) as archive:
            for member in archive:
                prefix='db-5.3.28/test/tcl/'
                if not member.name.startswith(prefix) or not member.isfile():continue
                relative=Path(member.name).relative_to('db-5.3.28')
                path=reference/relative
                if not path.resolve().is_relative_to(reference):raise SystemExit('Unsafe frozen test path')
                path.parent.mkdir(parents=True,exist_ok=True)
                path.write_bytes(archive.extractfile(member).read());expected.add(relative)
        # Only this maintained patch changes Tcl tests. Apply exactly the frozen
        # patch to the independent reference; no native file is changed here.
        with tarfile.open(SOURCES/names[1]) as archive:
            patch=archive.extractfile('debian/patches/004-tclsleep.patch').read()
        subprocess.run(['patch','--batch','--fuzz=0','-p1','-d',str(reference)],input=patch,check=True)
        subprocess.run(['patch','--batch','--fuzz=0','-p1','-d',str(reference),'-i',str(SOURCES/names[2])],check=True)
        for relative in sorted(expected):
            native=NATIVE/relative
            if native.is_symlink() or not native.resolve().is_relative_to(NATIVE) or digest(native)!=digest(reference/relative):
                raise SystemExit('Cached Tcl test differs from frozen reference: '+str(relative))
        extra={p.relative_to(NATIVE) for p in (NATIVE/'test/tcl').rglob('*.tcl')}-expected
        if extra:raise SystemExit('Unexpected cached Tcl scripts: '+str(sorted(extra)))
        print(json.dumps({'verified_test_files':len(expected),'maintained_tcl_patch':'004-tclsleep.patch','fixture_patch':names[2],'native_files_changed':False}))

if __name__=='__main__':main()
