"""Verify the exact private SDK/NASM payload before exposing browser tools."""
from pathlib import Path
import hashlib
import json
import os
import subprocess

BASE=Path('/mnt/lfs/sources/phase2/work/firefox-1')
SDK=BASE/'tools/wasi-sdk-25.0-x86_64-linux'
NASM=Path('/mnt/lfs/sources/phase2/work/nasm-1/stage')


def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def verify():
    r=json.loads(Path('/var/log/toddy/phase2/browser-tools-input-1.json').read_text())
    assert r['state']=='prepared' and r['sdk_directory']==str(SDK)
    assert subprocess.check_output(['findmnt','-n','-o','UUID','--mountpoint',str(BASE)],text=True).strip()==r['volume_uuid']
    assert {'ro','nosuid','nodev'}<=set(subprocess.check_output(['findmnt','-n','-o','OPTIONS','--mountpoint',str(SDK)],text=True).strip().split(','))
    inventory=BASE/'tools/sdk-inventory.json';assert digest(inventory)==r['inventory_sha256']
    expected=json.loads(inventory.read_text());actual={}
    for p in SDK.rglob('*'):
        name=str(p.relative_to(SDK))
        if p.is_symlink():actual[name]={'link':os.readlink(p)}
        elif p.is_file():actual[name]={'sha256':digest(p),'mode':p.stat().st_mode&0o777}
        else:assert p.is_dir()
    assert actual==expected,'SDK changed'
    result=json.loads((NASM.parent/'result.json').read_text())
    assert result['state']=='stage-qualified' and result['source_version']=='3.02'
    for name,sha in result['stage_files'].items():
        assert not Path(name).is_absolute() and '..' not in Path(name).parts
        p=NASM/name;assert p.resolve().is_relative_to(NASM.resolve()) and not p.is_symlink() and digest(p)==sha
    assert not (NASM/'usr/bin/nasm').is_symlink()
    print(json.dumps({'state':'verified','sdk_entries':len(actual),'nasm_files':len(result['stage_files'])}))


if __name__=='__main__':verify()
