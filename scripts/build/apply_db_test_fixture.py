#!/usr/bin/env python3
"""Apply only the two reviewed DB fixture corrections to verified source."""
import hashlib
import json
from pathlib import Path
import subprocess
from locked_inputs import locked_source

ROOT=Path(__file__).resolve().parents[2]
TARGET=Path('/mnt/lfs')
FIXTURES=(
    ('db-5.3.28-test142-environment-1.patch','test/tcl/test142.tcl'),
    ('db-5.3.28-repmgr007-async-diagnostic-1.patch','test/tcl/repmgr007.tcl'),
)

def digest(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def apply_fixture(root, sources, name, expected_file):
    row=locked_source(root,name);patch=sources/name
    if digest(patch)!=row['sha256']:raise SystemExit('DB fixture patch integrity mismatch')
    source=sources/'db-5.3.28'
    if row['fixture_file']!=expected_file:raise SystemExit('Unexpected fixture path')
    fixture=source/row['fixture_file']
    if fixture.is_symlink() or not fixture.resolve().is_relative_to(source):raise SystemExit('Fixture escapes source tree')
    current=digest(fixture)
    if current==row['fixture_postimage_sha256']:
        print('Exact reviewed DB fixture correction already present');return
    if current!=row['fixture_preimage_sha256']:raise SystemExit('Unexpected DB fixture preimage')
    subprocess.run(['patch','--batch','--forward','--fuzz=0','-p1','-d',str(source),'-i',str(patch)],check=True)
    if digest(fixture)!=row['fixture_postimage_sha256']:raise SystemExit('DB fixture postimage mismatch')
    print(json.dumps({'fixture':row['fixture_file'],'patch_sha256':row['sha256'],'postimage_sha256':digest(fixture),'runtime_source_changed':False}))

def main():
    subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
    for name,expected_file in FIXTURES:
        apply_fixture(ROOT,TARGET/'sources',name,expected_file)
if __name__=='__main__':main()
