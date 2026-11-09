#!/usr/bin/env python3
"""Byte-exact reversible custody of explicit cold, unreferenced backup images."""
import base64
import fcntl
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import struct
import subprocess
import time

ROOT=Path(__file__).resolve().parents[2]
RESERVE=100*1024**3
CONTEXT=ROOT/'.local/phase2/cold-checkpoint-compression-1'
SELECTED=['h03-target.qcow2','h01-builder.qcow2','h03-builder.qcow2','h04-builder.qcow2','h05-builder.qcow2','h06-ready-builder.qcow2']


def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def identity(st):return {'device':st.st_dev,'inode':st.st_ino,'bytes':st.st_size,'mtime_ns':st.st_mtime_ns,'ctime_ns':st.st_ctime_ns,'mode':st.st_mode,'uid':st.st_uid,'gid':st.st_gid,'nlink':st.st_nlink}


def exclusive(fd):
    fcntl.fcntl(fd,fcntl.F_OFD_SETLK,struct.pack('hhqqi4x',fcntl.F_WRLCK,os.SEEK_SET,0,0,0))


def verify_gzip(path,expected,expected_bytes):
    h=hashlib.sha256();total=0
    with gzip.open(path,'rb') as f:
        while block:=f.read(8*1024**2):h.update(block);total+=len(block)
    assert total==expected_bytes and h.hexdigest()==expected,'Compressed backup does not restore exact original bytes'
    return {'restored_bytes':total,'restored_sha256':h.hexdigest()}


def referenced_backings():
    images=[]
    for namespace in ['.local/vm','.local/phase2']:
        names=subprocess.check_output(['rg','--files','--hidden','--no-ignore',str(ROOT/namespace)],text=True).splitlines()
        images += [Path(n) for n in names if Path(n).suffix in ['.qcow2','.img'] and Path(n).is_file() and not Path(n).is_symlink()]
    references=set();metadata=[]
    for p in images:
        d=json.loads(subprocess.check_output(['qemu-img','info','-U','--output=json',str(p)],text=True))
        if d.get('backing-filename'):references.add(Path(d['backing-filename']).name)
        metadata.append({'path':str(p.relative_to(ROOT)),'format':d['format'],'backing':d.get('backing-filename')})
    return references,metadata


def save(value):
    part=CONTEXT/'result.json.part';assert not part.exists()
    with part.open('x') as f:json.dump(value,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
    part.replace(CONTEXT/'result.json')
    directory=os.open(CONTEXT,os.O_RDONLY|os.O_DIRECTORY)
    try:os.fsync(directory)
    finally:os.close(directory)


def main():
    assert os.geteuid()!=0 and ROOT.resolve()==ROOT
    cold=ROOT/'.local/vm/checkpoints';assert cold.resolve()==cold and not cold.is_symlink()
    assert not CONTEXT.exists(),'Inspect actual sources/archives/receipt before any continuation; never replay custody'
    assert shutil.disk_usage(ROOT).free>=RESERVE+256*1024**2
    lock=open(ROOT/'.local/phase2/cold-checkpoint-compression.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    references,metadata=referenced_backings();assert all(n not in references for n in SELECTED)
    CONTEXT.mkdir();(CONTEXT/'image-graph-before.json').write_text(json.dumps(metadata,indent=2)+'\n')
    state={'scope':'Reversible gzip representation of six explicit cold backup images only; no active/backing/master/live artifact or guest file deletion, no trim','producer_sha256':sha(Path(__file__)),'pid':os.getpid(),'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'proc_start_ticks':Path('/proc/self/stat').read_text().split()[21],'host_available_before':shutil.disk_usage(ROOT).free,'state':'running','images':[]};save(state)
    try:
        for name in SELECTED:
            if shutil.disk_usage(ROOT).free>=112*1024**3:break
            p=cold/name;archive=p.with_suffix(p.suffix+'.gz');part=archive.with_suffix(archive.suffix+'.part')
            assert p.resolve()==p and p.parent==cold and p.is_file() and not p.is_symlink() and not archive.exists() and not part.exists()
            st=p.stat();assert stat.S_ISREG(st.st_mode) and st.st_nlink==1 and st.st_uid==os.getuid()
            references,_=referenced_backings();assert name not in references,'Backing consumer appeared; preserve source'
            checked=subprocess.run(['qemu-img','check',str(p)],capture_output=True,text=True);assert checked.returncode==0,checked.stderr
            assert identity(p.stat())==identity(st),'Image changed during read-only structural check'
            fd=os.open(p,os.O_RDWR|os.O_NOFOLLOW);exclusive(fd)
            try:
                assert identity(os.fstat(fd))==identity(st)
                row={'source':str(p.relative_to(ROOT)),'archive':str(archive.relative_to(ROOT)),'identity':identity(st),'atime_ns':st.st_atime_ns,'xattrs':{n:base64.b64encode(os.getxattr(p,n)).decode() for n in os.listxattr(p)},'qemu_check_exit':0,'allocated_bytes':st.st_blocks*512,'state':'compressing','source_bytes_read':0};state['images'].append(row);save(state)
                digest=hashlib.sha256();budget=shutil.disk_usage(ROOT).free-RESERVE-128*1024**2
                with os.fdopen(os.open(part,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600),'wb') as raw:
                    class Bounded:
                        def write(self,data):
                            assert raw.tell()+len(data)<=budget,'Preserve partial archive/source; output budget reached'
                            assert shutil.disk_usage(ROOT).free>=RESERVE+len(data)+64*1024**2,'Real host reserve reached; preserve source'
                            return raw.write(data)
                        def flush(self):raw.flush()
                    with gzip.GzipFile(fileobj=Bounded(),mode='wb',filename='',mtime=0,compresslevel=6) as compressed:
                        last=0
                        while block:=os.read(fd,8*1024**2):
                            digest.update(block);compressed.write(block);row['source_bytes_read']+=len(block)
                            if row['source_bytes_read']-last>=64*1024**2:
                                row['compressed_bytes']=raw.tell();save(state);last=row['source_bytes_read']
                    raw.flush();os.fsync(raw.fileno())
                assert row['source_bytes_read']==st.st_size and identity(os.fstat(fd))==identity(st)
                row['source_sha256']=digest.hexdigest();row['roundtrip']=verify_gzip(part,row['source_sha256'],st.st_size)
                row['archive_sha256']=sha(part);row['archive_bytes']=part.stat().st_size
                assert row['archive_bytes']<row['allocated_bytes'],'No useful reclaimed capacity; preserve original'
                row['state']='archive-verified';save(state);part.rename(archive)
                row['archive_identity']=identity(archive.stat());row['state']='retiring';save(state)
                assert identity(p.stat())==identity(st) and identity(os.fstat(fd))==identity(st)
                assert sha(archive)==row['archive_sha256']
                references,_=referenced_backings();assert name not in references,'A new backing consumer appeared; source preserved'
                assert identity(p.stat())==identity(st)
                assert {n:base64.b64encode(os.getxattr(p,n)).decode() for n in os.listxattr(p)}==row['xattrs']
                p.unlink()
                directory=os.open(cold,os.O_RDONLY|os.O_DIRECTORY)
                try:os.fsync(directory)
                finally:os.close(directory)
                row.update(state='retired',host_available_after=shutil.disk_usage(ROOT).free);save(state)
                print(json.dumps({'source':name,'state':'retired','source_bytes':st.st_size,'archive_bytes':row['archive_bytes'],'host_available':row['host_available_after']}),flush=True)
            finally:os.close(fd)
        state.update(state='complete',host_available_after=shutil.disk_usage(ROOT).free);state['reclaimed_bytes']=state['host_available_after']-state['host_available_before'];state['recovery']='Verify archive SHA; restore gzip stream to a NEW .part at exact source path, verify raw SHA/size, restore recorded mode/uid/gid/xattrs/atime/mtime and fsync; rename only when original absent, then qemu-img check. Preserve archives. Never give compressed file to QEMU or overwrite an existing image.';save(state)
    except BaseException as error:
        state.update(state='failed-preserved',error={'type':type(error).__name__,'message':str(error)});save(state);raise

if __name__=='__main__':main()
