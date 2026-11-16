"""Export/retire one opaque historical H10 copy tar in the candidate only.

The host coordinator proves a durable compressed copy by complete decompression
before requesting retirement. No tar member is ever extracted or executed.
"""
import base64
import fcntl
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys

sys.dont_write_bytecode=True
ROOT=Path('/opt/toddy-build');TARGET=Path('/mnt/lfs')
EVIDENCE=TARGET/'sources/stage/h10-live-root-evidence'
ARTIFACT=EVIDENCE/'copy/selected-root.tar'
RECEIPT=Path('/var/log/toddy/phase2/h10-selected-tar-custody-1.json')
SIZE=3731302400;DEVICE=64788;INODE=8707439
TAR_SHA='84bbe95d1dbfe3b50a8284e95006b461c7eab6a3a1091e41bfe519a96fa7898d'
MTIME=1794055054388498491
IMAGE_MANIFEST_SHA='4693cfd359b5e0428b24bdaca53d06b561a9c39253dfb013d93f51a17e648398'
INPUT_MANIFEST_SHA='5f12e46d5fcceb6472e1b4d667c6bbfecbbf072403c3887553bd45fedfc36293'
ASSEMBLY_SHA='722a12e94a148bbb28a1d2b8febb3bf04595c7c15aa7057ab58548b78669e016'
COPY_REPORT_SHA='6d4bc9ccabe760104b06450bdadfbe4751a6cd07fdb1e7e6d6e73252a5e505ee'
HASH=__import__('re').compile('[0-9a-f]{64}\\Z')


def digest(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def encoded(value):return json.dumps(value,sort_keys=True,separators=(',',':')).encode()


def save(value):
    part=RECEIPT.with_suffix('.part')
    with part.open('x') as stream:
        os.fchmod(stream.fileno(),0o600);stream.write(encoded(value).decode()+'\n');stream.flush();os.fsync(stream.fileno())
    os.replace(part,RECEIPT)
    directory=os.open(RECEIPT.parent,os.O_DIRECTORY)
    try:os.fsync(directory)
    finally:os.close(directory)


def metadata(path):
    info=path.lstat()
    return {'mode':info.st_mode,'uid':info.st_uid,'gid':info.st_gid,'mtime_ns':info.st_mtime_ns,
        'xattrs':{key:base64.b64encode(os.getxattr(path,key,follow_symlinks=False)).decode()
                  for key in sorted(os.listxattr(path,follow_symlinks=False))}}


def snapshot():
    rows={}
    for path in [EVIDENCE,*sorted(EVIDENCE.rglob('*'))]:
        relative=path.relative_to(EVIDENCE).as_posix();info=path.lstat()
        if (path.resolve()!=path or info.st_dev!=DEVICE or info.st_uid or info.st_gid or
                not (stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode))):
            raise ValueError('Unexpected historical H10 evidence namespace')
        row=metadata(path)
        if stat.S_ISREG(info.st_mode):
            if info.st_nlink!=1:raise ValueError('Historical H10 evidence has external hardlinks')
            row.update(bytes=info.st_size,sha256=digest(path))
        rows[relative]=row
    if len(rows)!=27:raise ValueError('Historical H10 evidence entry count changed')
    return rows


def verify():
    for path,inode in ((EVIDENCE,8707431),(EVIDENCE/'copy',8707434),(ARTIFACT,INODE)):
        info=path.lstat()
        if path.resolve()!=path or info.st_dev!=DEVICE or info.st_ino!=inode or info.st_uid or info.st_gid:
            raise ValueError('Frozen candidate H10 cache identity changed')
    info=ARTIFACT.stat()
    if (info.st_mode!=stat.S_IFREG|0o644 or info.st_nlink!=1 or info.st_size!=SIZE or
            info.st_mtime_ns!=MTIME or info.st_blocks*512!=3731308544 or info.st_dev!=TARGET.stat().st_dev):
        raise ValueError('Frozen H10 tar metadata differs')
    mount=subprocess.check_output(['/usr/bin/findmnt','-rn','-o','TARGET','--target',str(ARTIFACT)],text=True).strip()
    if mount!=str(TARGET):raise ValueError('Historical H10 tar mount changed')
    mounts=subprocess.check_output(['/usr/bin/findmnt','-rn','-o','TARGET'],text=True).splitlines()
    if any(name==str(EVIDENCE) or name.startswith(str(EVIDENCE)+'/') for name in mounts):
        raise ValueError('Historical H10 evidence has a nested mount')
    if digest(EVIDENCE/'18-image-manifest.json')!=IMAGE_MANIFEST_SHA or digest(EVIDENCE/'copy/input-manifest.json')!=INPUT_MANIFEST_SHA:
        raise ValueError('Historical H10 selected/image manifest differs')
    if digest(EVIDENCE/'assembly.json')!=ASSEMBLY_SHA or digest(EVIDENCE/'copy/report.json')!=COPY_REPORT_SHA or digest(EVIDENCE/'02-copy-payload.json')!=COPY_REPORT_SHA:
        raise ValueError('Frozen H10 assembly/copy proof differs')
    report=json.loads((EVIDENCE/'copy/report.json').read_bytes())
    if report.get('exact_inventory_and_metadata') is not True or not HASH.fullmatch(report.get('archive_sha256','')) or report['archive_sha256']!=TAR_SHA or digest(ARTIFACT)!=TAR_SHA:
        raise ValueError('Historical H10 opaque tar differs from native copy proof')
    return report['archive_sha256']


def no_consumers():
    # Reuse the already reviewed file/loop consumer checks, then cover mappings.
    from retire_h11_readback_copy import no_consumers as existing
    existing(ARTIFACT)
    wanted=ARTIFACT.stat();dev=(os.major(wanted.st_dev),os.minor(wanted.st_dev))
    for process in Path('/proc').iterdir():
        if not process.name.isdigit():continue
        try:lines=(process/'maps').read_text().splitlines()
        except (FileNotFoundError,ProcessLookupError):continue
        for line in lines:
            fields=line.split(None,5)
            if len(fields)<5:raise ValueError('Unknown process mapping format')
            major,minor=(int(value,16) for value in fields[3].split(':'))
            if (major,minor)==dev and int(fields[4])==wanted.st_ino:
                raise ValueError('Historical H10 tar has a mapped consumer')


def boot_id():return Path('/proc/sys/kernel/random/boot_id').read_text().strip()


def export():
    if os.path.lexists(RECEIPT) or os.path.lexists(RECEIPT.with_suffix('.part')):
        raise ValueError('Preserve existing/uncertain H10 custody; no replay')
    sha=verify();no_consumers();before=snapshot()
    state={'version':1,'state':'export-intended','artifact':str(ARTIFACT),'bytes':SIZE,'sha256':sha,
        'device':DEVICE,'inode':INODE,'boot_id':boot_id(),'source_metadata':before['copy/selected-root.tar'],
        'evidence_before':before,'producer_sha256':digest(Path(__file__))}
    save(state)
    actual=hashlib.sha256();count=0
    with ARTIFACT.open('rb') as stream:
        while chunk:=stream.read(4*1024**2):
            count+=len(chunk);actual.update(chunk);sys.stdout.buffer.write(chunk)
    sys.stdout.buffer.flush()
    if count!=SIZE or actual.hexdigest()!=sha or verify()!=sha or snapshot()!=before:
        raise ValueError('Historical H10 source changed during export')
    state['state']='exported';save(state)


def read_receipt():
    info=RECEIPT.lstat()
    if (RECEIPT.resolve()!=RECEIPT or not stat.S_ISREG(info.st_mode) or info.st_uid or info.st_gid or
            info.st_nlink!=1 or stat.S_IMODE(info.st_mode)!=0o600 or info.st_size>256*1024):
        raise ValueError('Private root H10 custody receipt required')
    return json.loads(RECEIPT.read_bytes())


def retire(proof):
    state=read_receipt()
    fields={'version','state','bytes','sha256','compressed_sha256','compressed_bytes','host_receipt_sha256'}
    if (not isinstance(proof,dict) or set(proof)!=fields or type(proof['version']) is not int or proof['version']!=1 or
            proof['state']!='complete-decompression-verified' or proof['bytes']!=SIZE or
            not all(isinstance(proof[key],str) and HASH.fullmatch(proof[key]) for key in ('sha256','compressed_sha256','host_receipt_sha256')) or
            type(proof['compressed_bytes']) is not int or not 0<proof['compressed_bytes']<=SIZE+16*1024**2):
        raise ValueError('Actual durable host decompression proof required')
    if (state.get('state')!='exported' or state.get('boot_id')!=boot_id() or
            state.get('producer_sha256')!=digest(Path(__file__)) or proof['sha256']!=state['sha256'] or
            verify()!=state['sha256'] or snapshot()!=state['evidence_before']):
        raise ValueError('Historical H10 retirement custody changed')
    no_consumers();state.update(state='retire-intended',host_proof=proof,available_before=free());save(state)
    # Recheck after the durable intent. No other pathname is removed.
    if verify()!=state['sha256'] or snapshot()!=state['evidence_before']:raise ValueError('Historical H10 source changed before unlink')
    no_consumers();parent_metadata=metadata(ARTIFACT.parent)
    ARTIFACT.unlink()
    os.utime(ARTIFACT.parent,ns=(ARTIFACT.parent.stat().st_atime_ns,parent_metadata['mtime_ns']),follow_symlinks=False)
    directory=os.open(ARTIFACT.parent,os.O_DIRECTORY)
    try:os.fsync(directory)
    finally:os.close(directory)
    after=snapshot_after_retirement()
    expected=dict(state['evidence_before']);del expected['copy/selected-root.tar']
    if after!=expected:raise ValueError('Other historical H10 evidence changed; preserve custody and inspect')
    state.update(state='complete',available_after=free(),retired_bytes=SIZE,
        recovery='Verify private host gzip SHA, fully decompress to the reviewed absent guest tar path and restore recorded metadata; never extract tar members or replay retirement.')
    state['measured_reclaimed_bytes']=state['available_after']-state['available_before'];save(state)
    return state


def snapshot_after_retirement():
    # Same inventory semantics with one fixed missing entry permitted.
    rows={}
    for path in [EVIDENCE,*sorted(EVIDENCE.rglob('*'))]:
        info=path.lstat()
        if path.resolve()!=path or info.st_dev!=DEVICE or info.st_uid or info.st_gid or not (stat.S_ISREG(info.st_mode) or stat.S_ISDIR(info.st_mode)):
            raise ValueError('Other H10 evidence namespace changed')
        row=metadata(path)
        if stat.S_ISREG(info.st_mode):
            if info.st_nlink!=1:raise ValueError('Other H10 evidence hardlinks changed')
            row.update(bytes=info.st_size,sha256=digest(path))
        rows[path.relative_to(EVIDENCE).as_posix()]=row
    return rows


def free():
    value=os.statvfs(TARGET);return value.f_bavail*value.f_frsize


def main():
    if os.getuid()!=0 or os.geteuid()!=0 or sys.argv[1:] not in (['export'],['receipt'],['retire']):
        raise ValueError('Fixed root H10 candidate custody command required')
    subprocess.run(['/usr/bin/bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
    with Path('/var/log/toddy/build/build.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if list(Path('/var/log/toddy/build').glob('*.running.json')) or Path('/var/log/toddy/build/input-sync.running').exists():
            raise ValueError('Preserve active native operation')
        if sys.argv[1]=='export':export()
        elif sys.argv[1]=='receipt':
            print(json.dumps(read_receipt(),sort_keys=True))
        else:
            data=sys.stdin.buffer.read(65537)
            if len(data)>65536:raise ValueError('H10 host proof size')
            print(json.dumps(retire(json.loads(data)),sort_keys=True))


if __name__=='__main__':main()
