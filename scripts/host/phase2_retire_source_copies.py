#!/usr/bin/env python3
"""Retire only three authenticated, archive-identical host source duplicates."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import tarfile

ROOT=Path(__file__).resolve().parents[2]


def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def tree(path):
    result={}
    for p in path.rglob('*'):
        relative=str(p.relative_to(path))
        if p.is_symlink():result[relative]={'symlink':os.readlink(p)}
        elif p.is_file():result[relative]={'sha256':sha(p),'bytes':p.stat().st_size}
        else:assert p.is_dir()
    return result


def main():
    ledger=ROOT/'.local/phase2/host-source-copy-custody.json'
    assert not ledger.exists(),'Inspect prior receipt/postconditions, never repeat uncertain retirement'
    rows=json.loads((ROOT/'config/phase2/sources.lock.json').read_text())['components']
    selected=[('cargo-c-vendor','rust-vendor-1/cargo-c/vendor','vendor'),
              ('librsvg-vendor','rust-vendor-1/librsvg/vendor','vendor'),
              ('mesa','mesa-source-review-1/mesa-26.1.7','mesa-26.1.7')]
    record={'scope':'Host source duplicates only; complete corresponding archives, private Cargo cache, logs, all guest compiled tests and raw evidence retained',
            'state':'verifying','sources':[]}
    def save():
        part=ledger.with_suffix('.part');assert not part.exists()
        with part.open('x') as f:f.write(json.dumps(record,indent=2)+'\n');f.flush();os.fsync(f.fileno())
        part.replace(ledger)
    save()
    for name,relative,archive_root in selected:
        row=next(r for r in rows if r['name']==name)
        archive=ROOT/'.local/sources'/row['filename'];assert archive.is_file() and not archive.is_symlink()
        assert sha(archive)==row['sha256']
        path=ROOT/'.local/phase2'/relative;assert path.is_dir() and not path.is_symlink() and path.resolve()==path
        expected={}
        with tarfile.open(archive) as source:
            for m in source:
                parts=Path(m.name).parts;assert parts and parts[0]==archive_root and '..' not in parts and not Path(m.name).is_absolute()
                if m.isdir():continue
                key=str(Path(*parts[1:]));assert key not in expected
                if m.issym():expected[key]={'symlink':m.linkname}
                else:
                    assert m.isfile(),'Unexpected hardlink/special source entry'
                    with source.extractfile(m) as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
                    expected[key]={'sha256':digest,'bytes':m.size}
        actual=tree(path);assert actual==expected,'Changed/extra/missing source files; preserve for review'
        record['sources'].append({'name':name,'path':str(path.relative_to(ROOT)),
            'archive':str(archive.relative_to(ROOT)),'archive_sha256':row['sha256'],
            'payload_entries':len(actual),'payload_bytes':sum(r.get('bytes',0) for r in actual.values()),
            'manifest_sha256':hashlib.sha256(json.dumps(actual,sort_keys=True,separators=(',',':')).encode()).hexdigest(),
            'directory_inode':path.stat().st_ino,'state':'verified'})
        save()
    record['state']='verified';save()
    before=os.statvfs(ROOT);record['host_free_before']=before.f_bavail*before.f_frsize
    for row in record['sources']:
        path=ROOT/row['path'];assert not path.is_symlink() and path.resolve()==path and path.stat().st_ino==row['directory_inode']
        assert sha(ROOT/row['archive'])==row['archive_sha256']
        row['state']='retiring';save();shutil.rmtree(path);assert not path.exists()
        row['state']='retired';save()
    after=os.statvfs(ROOT);record['host_free_after']=after.f_bavail*after.f_frsize
    record['reclaimed_bytes']=record['host_free_after']-record['host_free_before']
    record['state']='complete';record['recovery']='Restore only the listed unchanged source archive/root if needed. Do not rerun retirement or Cargo acquisition. Existing private Cargo registry cache remains reusable.'
    save();print(json.dumps(record))


if __name__=='__main__':main()
