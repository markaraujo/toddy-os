"""Inspect/restore only the existing private browser filesystem and aliases."""
from pathlib import Path
import fcntl
import hashlib
import json
import os
import re
import stat
import subprocess
import sys

BASE=Path('/mnt/lfs/sources/phase2/work/firefox-1')
LOG=Path('/var/log/toddy/phase2')
UUID='082a2d97-fa79-4ee5-86e5-a179f768daec'
SERIAL='TODDY-B02-FIREFOX'
RECORD=LOG/'browser-mount-baseline-1.json'
ALIASES=[
    (BASE/'source/firefox-153.2.0',BASE/'source/firefox-153.2.0',True),
    (BASE/'tools/wasi-sdk-25.0-x86_64-linux',BASE/'tools/wasi-sdk-25.0-x86_64-linux',True),
    (BASE/'source/firefox-153.2.0',Path('/mnt/lfs/sources/phase2/inputs/firefox-153.2.0'),True),
    (BASE/'build/browser-1',Path('/mnt/lfs/sources/phase2/work/firefox-build-1'),False),
    (BASE/'source/nasm-3.02',Path('/mnt/lfs/sources/phase2/inputs/nasm-3.02'),True),
    (BASE/'build/nasm-1',Path('/mnt/lfs/sources/phase2/work/nasm-1'),False),
]


def mounted(p):
    return subprocess.run(['findmnt','--mountpoint',str(p)],capture_output=True).returncode==0


def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def device():
    devices=[p for p in Path('/sys/class/block').iterdir() if (p/'serial').exists() and (p/'serial').read_text().strip()==SERIAL]
    assert len(devices)==1
    p=Path('/dev')/devices[0].name
    assert not p.is_symlink() and stat.S_ISBLK(p.stat().st_mode)
    assert int((devices[0]/'size').read_text())*512==16*1024**3
    assert subprocess.check_output(['blkid','-s','UUID','-o','value',str(p)],text=True).strip()==UUID
    return p


def inspect(expected=None):
    d=device()
    assert subprocess.check_output(['findmnt','-n','-o','UUID','--mountpoint',str(BASE)],text=True).strip()==UUID
    rows=[]
    for src,dst,ro in ALIASES:
        assert not src.is_symlink() and not dst.is_symlink()
        assert src.is_dir() and dst.is_dir() and src.stat().st_ino==dst.stat().st_ino
        options=set(subprocess.check_output(['findmnt','-n','-o','OPTIONS','--mountpoint',str(dst)],text=True).strip().split(','))
        assert {'nosuid','nodev','ro' if ro else 'rw'}<=options
        rows.append({'source':str(src),'target':str(dst),'readonly':ro,'inode':src.stat().st_ino})
    if expected is not None:assert rows==expected['aliases'],'Unexpected role/inode change'
    compiler=json.loads((BASE/'build/browser-1/firefox-compile-result.json').read_text())
    assert compiler['state']=='compiled' and compiler['exit']==0
    artifacts={}
    for name in ['firefox','libxul.so']:
        work=BASE/'build/browser-1';obj=work/'obj'
        if (obj/'.toddy-retired.json').exists():
            receipt=json.loads(Path('/var/log/toddy/phase2/firefox-baseline-objects-custody-1.json').read_text())
            assert receipt['state']=='complete' and receipt['restored_exact'] and receipt['source_unchanged']
            marker=json.loads((obj/'.toddy-retired.json').read_text())
            assert marker['archive_sha256']==receipt['archive_sha256'] and marker['source_manifest_sha256']==receipt['manifest_sha256']
            p=work/'retained-baseline'/name
            assert not p.is_symlink() and p.is_file() and not p.stat().st_mode&0o222
            assert receipt['retained_artifacts'][name]=={'path':str(p),'sha256':compiler['artifacts'][name]}
        else:
            p=obj/'dist/bin'/name
            assert p.resolve().is_relative_to(obj)
        artifacts[name]=digest(p);assert artifacts[name]==compiler['artifacts'][name]
    assert json.loads((BASE/'build/nasm-1/result.json').read_text())['state']=='stage-qualified'
    result={'state':'inspected','uuid':UUID,'serial':SERIAL,'device':str(d),'aliases':rows,
            'compiler_artifacts':artifacts,'scope':'Existing filesystem/mounts and retained private compiler artifacts only; no rebuild or browser/native UI acceptance'}
    if expected is not None:assert artifacts==expected['compiler_artifacts']
    return result


def save(path,row):
    part=path.with_suffix('.part');assert not part.exists(),'Inspect partial receipt'
    with part.open('x') as f:
        json.dump(row,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
    part.replace(path)


def main():
    assert os.geteuid()==0
    subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
    lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
    if sys.argv[1:]==['--record']:
        assert not RECORD.exists(),'Inspect existing baseline, never replace'
        row=inspect();row.update(state='recorded',boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip())
        save(RECORD,row);print(json.dumps(row));return
    expected=json.loads(RECORD.read_text());assert expected['state']=='recorded' and expected['uuid']==UUID
    if sys.argv[1:]==['--inspect']:
        print(json.dumps(inspect(expected)));return
    name,=sys.argv[1:]
    print(json.dumps(restore(name,expected)))


def restore(name,expected):
    assert expected['state']=='recorded' and expected['uuid']==UUID
    assert re.fullmatch(r'[a-z][a-z0-9-]{1,63}',name)
    receipt=LOG/(name+'.json');assert not receipt.exists() and not receipt.with_suffix('.part').exists(),'Inspect actual partial mounts; never replay'
    assert not mounted(BASE) and BASE.is_dir() and not BASE.is_symlink() and not list(BASE.iterdir())
    d=device();row={'state':'restore-intended','uuid':UUID,'device':str(d),'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'bindings':[]}
    save(receipt,row)
    subprocess.run(['mount','-o','nosuid,nodev',str(d),str(BASE)],check=True)
    for src,dst,ro in ALIASES:
        assert src.is_dir() and not src.is_symlink() and not dst.is_symlink()
        assert not mounted(dst)
        if src!=dst:assert dst.is_dir() and not list(dst.iterdir())
        row['pending_bind']=str(dst);save(receipt,row)
        subprocess.run(['mount','--bind',str(src),str(dst)],check=True)
        subprocess.run(['mount','-o','remount,bind,nosuid,nodev,'+('ro' if ro else 'rw'),str(dst)],check=True)
        row['bindings'].append(str(dst));row.pop('pending_bind');save(receipt,row)
    row.update(state='complete',verification=inspect(expected));save(receipt,row);return row


if __name__=='__main__':main()
