#!/usr/bin/env python3
"""Retire verified expanded source duplicates, retaining compressed Cargo caches."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import tarfile

from phase2_retire_source_copies import ROOT,sha,tree


def archive_tree(archive,root):
    result={}
    with tarfile.open(archive) as t:
        for m in t:
            parts=Path(m.name).parts
            assert parts and parts[0]==root and '..' not in parts and not Path(m.name).is_absolute()
            if m.isdir():continue
            key=str(Path(*parts[1:]));assert key not in result
            if m.issym():result[key]={'symlink':m.linkname}
            else:
                assert m.isfile()
                with t.extractfile(m) as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
                result[key]={'sha256':digest,'bytes':m.size}
    return result


def main():
    ledger=ROOT/'.local/phase2/expanded-source-custody.json'
    assert not ledger.exists(),'Reconcile prior state; never replay retirement'
    rows=json.loads((ROOT/'config/phase2/sources.lock.json').read_text())['components']
    record={'scope':'Expanded source-only duplicates; all compressed .crate/source archives, Cargo indexes, compiled artifacts, guest caches, logs and evidence retained',
            'state':'verifying','sources':[]}
    def save():
        part=ledger.with_suffix('.part');assert not part.exists()
        with part.open('x') as f:f.write(json.dumps(record,indent=2)+'\n');f.flush();os.fsync(f.fileno())
        part.replace(ledger)
    save()
    selected=[]
    for name,folder,root in [
        ('gtk','gtk','gtk-4.22.4'),('iso-codes','iso-codes','iso-codes-v4.20.1'),
        ('gdk-pixbuf','gdk-pixbuf','gdk-pixbuf-2.44.7'),('tiff','tiff','tiff-4.7.2'),
        ('xkeyboard-config','keyboard','xkeyboard-config-2.48'),('libxkbcommon','keyboard','libxkbcommon-1.13.2'),
        ('librsvg','librsvg','librsvg-2.62.3'),('libdrm','libdrm','libdrm-2.4.134'),
        ('libepoxy','libepoxy','libepoxy-1.5.10'),('libpciaccess','libpciaccess','libpciaccess-0.19'),('pyyaml','pyyaml','pyyaml-6.0.3')]:
        row=next(r for r in rows if r['name']==name);archive=ROOT/'.local/sources'/row['filename']
        assert sha(archive)==row['sha256'];selected.append((ROOT/'.local/phase2'/(folder+'-source-review-1')/root,archive,root,False))
    registry=ROOT/'.local/phase2/rust-vendor-1/home/registry'
    src=registry/'src';assert src.resolve()==src and not src.is_symlink()
    for index in sorted(src.iterdir()):
        assert index.is_dir() and not index.is_symlink() and index.name.startswith('index.crates.io-')
        for package in sorted(index.iterdir()):
            assert package.is_dir() and not package.is_symlink()
            archive=registry/'cache'/index.name/(package.name+'.crate');assert archive.is_file() and not archive.is_symlink()
            selected.append((package,archive,package.name,True))
    for path,archive,root,cargo in selected:
        assert path.resolve()==path and path.is_dir() and not path.is_symlink()
        expected=archive_tree(archive,root);actual=tree(path)
        if cargo:
            marker=path/'.cargo-ok';assert marker.read_bytes()==b'{"v":1}'
            assert actual.pop('.cargo-ok')=={'sha256':sha(marker),'bytes':7}
        assert actual==expected,str(path)+' changed/extra/missing source bytes; preserve everything'
        record['sources'].append({'path':str(path.relative_to(ROOT)),'archive':str(archive.relative_to(ROOT)),
            'archive_sha256':sha(archive),'payload_entries':len(actual),'payload_bytes':sum(r.get('bytes',0) for r in actual.values()),
            'manifest_sha256':hashlib.sha256(json.dumps(actual,sort_keys=True,separators=(',',':')).encode()).hexdigest(),
            'directory_inode':path.stat().st_ino,'cargo_marker_only':cargo,'state':'verified'})
    assert record['sources'];record['state']='verified';save()
    fs=os.statvfs(ROOT);record['host_available_before']=fs.f_bavail*fs.f_frsize
    for row in record['sources']:
        path=ROOT/row['path'];assert path.resolve()==path and not path.is_symlink() and path.stat().st_ino==row['directory_inode']
        assert sha(ROOT/row['archive'])==row['archive_sha256']
        row['state']='retiring';save();shutil.rmtree(path);assert not path.exists();row['state']='retired';save()
    fs=os.statvfs(ROOT);record['host_available_after']=fs.f_bavail*fs.f_frsize
    record['reclaimed_bytes']=record['host_available_after']-record['host_available_before'];record['state']='complete'
    record['recovery']='Review copies: extract retained frozen archive only if needed. Cargo re-expands retained exact .crate cache automatically without re-download. Never rerun retirement or delete compressed/compiled caches.'
    save();print(json.dumps({k:record[k] for k in ['state','host_available_before','host_available_after','reclaimed_bytes']}))


if __name__=='__main__':main()
