#!/usr/bin/env python3
"""Compress stationary disposable test overlays byte-exact; never touch VM backings."""
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess

ROOT=Path(__file__).resolve().parents[2]


def digest(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def main():
    ledger=ROOT/'.local/phase2/native-test-overlay-custody.json'
    assert not ledger.exists(),'Reconcile prior custody; never replay'
    record={'scope':'Only three stopped disposable native test overlays; every source byte retained compressed, all native logs/reports, mutable builder/target and immutable foundation backings retained',
            'state':'verifying','overlays':[],'host_available_before':shutil.disk_usage(ROOT).free}
    def save():
        part=ledger.with_suffix('.part')
        with part.open('x') as f:f.write(json.dumps(record,indent=2)+'\n');f.flush();os.fsync(f.fileno())
        part.replace(ledger)
    save()
    for number in [1,2,3]:
        context=ROOT/'.local/phase2'/('native-bwrap-runtime-'+str(number))
        state=json.loads((context/'result.json').read_text())
        info=json.loads(subprocess.check_output(['docker','inspect',state['container_id']],text=True))[0]
        assert not info['State']['Running'] and info['State']['ExitCode']==0
        assert (info['Config'].get('Labels') or {}).get('toddy.boot-test')==state['run_id']
        source=context/'target.qcow2';compressed=source.with_suffix('.qcow2.gz');part=compressed.with_suffix('.gz.part')
        assert source.resolve()==source and not source.is_symlink()
        before=source.lstat();assert stat.S_ISREG(before.st_mode) and before.st_uid==os.geteuid() and before.st_nlink==1
        assert before.st_size<64*1024**2 and not compressed.exists() and not part.exists()
        with source.open('rb') as f:assert f.read(4)==b'QFI\xfb'
        original_sha=digest(source)
        row={'path':str(source.relative_to(ROOT)),'source_bytes':before.st_size,'source_sha256':original_sha,
             'source_inode':before.st_ino,'source_mtime_ns':before.st_mtime_ns,'source_allocated_bytes':before.st_blocks*512,
             'archive':str(compressed.relative_to(ROOT)),'state':'compressing','native_container_stopped':True}
        record['overlays'].append(row);save()
        with part.open('xb') as raw:
            os.fchmod(raw.fileno(),0o600)
            with gzip.GzipFile(fileobj=raw,mode='wb',filename='',mtime=0) as archive:
                with source.open('rb') as f:shutil.copyfileobj(f,archive)
            raw.flush();os.fsync(raw.fileno())
        check=hashlib.sha256();size=0
        with gzip.open(part,'rb') as f:
            while chunk:=f.read(1024*1024):check.update(chunk);size+=len(chunk)
        assert size==before.st_size and check.hexdigest()==original_sha
        after=source.lstat()
        assert (after.st_ino,after.st_size,after.st_mtime_ns)==(before.st_ino,before.st_size,before.st_mtime_ns)
        part.rename(compressed)
        row.update(state='verified',archive_sha256=digest(compressed),archive_bytes=compressed.stat().st_size,
                   archive_allocated_bytes=compressed.stat().st_blocks*512)
        save();source.unlink();assert not source.exists();row['state']='retired-raw-bytes-retained';save()
    record['state']='complete';record['host_available_after']=shutil.disk_usage(ROOT).free
    record['overlay_allocation_reclaimed_bytes']=sum(r['source_allocated_bytes']-r['archive_allocated_bytes'] for r in record['overlays'])
    record['recovery']='Verify compressed/archive and decompressed source SHA before restoring an absent exact path. These are disposable test deltas, not standalone checkpoints; never boot against a changed mutable parent or replay existing native contexts.'
    save();print(json.dumps({k:record[k] for k in ['state','host_available_before','host_available_after','overlay_allocation_reclaimed_bytes']}))


if __name__=='__main__':main()
