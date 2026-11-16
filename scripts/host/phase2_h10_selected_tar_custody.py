"""Durable private host gzip custody of one opaque H10 copy tar, then retire it.

No tar members are extracted. Complete decompression is streamed into SHA-256,
so root-owned/setuid payload never appears on an executable host filesystem.
"""
import fcntl
import gzip
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys

sys.dont_write_bytecode=True
import phase2_candidate_vm as candidate
import vm

ROOT=vm.ROOT
CONTEXT=ROOT/'.local/phase2/h10-selected-tar-custody-1'
GUEST='/opt/toddy-build/scripts/build/phase2/h10_selected_tar_custody.py'
SIZE=3731302400
CHUNK=4*1024**2


def digest(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def encoded(value):return json.dumps(value,sort_keys=True,separators=(',',':')).encode()


def fsync_directory(path):
    descriptor=os.open(path,os.O_DIRECTORY)
    try:os.fsync(descriptor)
    finally:os.close(descriptor)


def save(value):
    part=CONTEXT/'result.part';target=CONTEXT/'result.json'
    with part.open('x') as stream:
        os.fchmod(stream.fileno(),0o600);stream.write(encoded(value).decode()+'\n');stream.flush();os.fsync(stream.fileno())
    os.replace(part,target);fsync_directory(CONTEXT)


def command(action):
    if action not in ('export','receipt','retire'):raise ValueError('Unknown fixed H10 custody action')
    ssh=candidate.ssh()
    return [*ssh[:-1],'-o','ServerAliveInterval=15','-o','ServerAliveCountMax=2',ssh[-1],
        '/usr/bin/python3 '+GUEST+' '+action]


def stream_compress(source,destination,expected_bytes=SIZE):
    raw=hashlib.sha256();count=0
    with destination.open('xb') as output:
        os.fchmod(output.fileno(),0o600)
        with gzip.GzipFile(filename='',mode='wb',fileobj=output,compresslevel=1,mtime=0) as compressed:
            while chunk:=source.read(CHUNK):
                count+=len(chunk)
                if count>expected_bytes:raise ValueError('Opaque H10 tar exceeds frozen byte count')
                raw.update(chunk);compressed.write(chunk)
        output.flush();os.fsync(output.fileno())
    if count!=expected_bytes:raise ValueError('Opaque H10 tar stream incomplete')
    return {'bytes':count,'sha256':raw.hexdigest()}


def verify_decompression(archive,expected):
    info=archive.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_nlink!=1 or info.st_uid!=os.getuid() or stat.S_IMODE(info.st_mode)!=0o600:
        raise ValueError('Private host compressed archive custody')
    actual=hashlib.sha256();count=0
    with gzip.open(archive,'rb') as stream:
        while chunk:=stream.read(CHUNK):
            count+=len(chunk)
            if count>expected['bytes']:raise ValueError('Opaque H10 decompression exceeds original size')
            actual.update(chunk)
    if count!=expected['bytes'] or actual.hexdigest()!=expected['sha256']:
        raise ValueError('Complete H10 decompression differs from original tar stream')
    return {'version':1,'state':'complete-decompression-verified','bytes':count,
        'sha256':actual.hexdigest(),'compressed_sha256':digest(archive),'compressed_bytes':info.st_size}


def owned_guest(expected):
    observed=candidate.owned()
    if observed!=expected:raise ValueError('Candidate VM changed during custody')
    candidate.bases()


def guest_receipt():
    result=subprocess.run(command('receipt'),stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True,timeout=60)
    if len(result.stdout)>256*1024:raise ValueError('Guest H10 custody receipt size')
    return json.loads(result.stdout)


def main():
    if sys.argv[1:] or os.geteuid()==0 or ROOT.resolve()!=ROOT:
        raise ValueError('Fixed unprivileged host custody coordinator command required')
    os.umask(0o077)
    parent=CONTEXT.parent
    if parent.resolve()!=parent or not parent.is_dir() or parent.stat().st_uid!=os.getuid():
        raise ValueError('Private host custody parent required')
    # Share the existing boot-test lock: no second guest owner during custody.
    with (vm.VM/'native-boot-test.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if os.path.lexists(CONTEXT):raise ValueError('Preserve existing/uncertain host H10 custody; never replay')
        identity=candidate.owned();candidate.bases()
        reserve=json.loads((ROOT/'config/build-host.lock.json').read_bytes())['host_free_reserve_gib']*1024**3
        space=os.statvfs(parent)
        if space.f_bavail*space.f_frsize<reserve+SIZE+128*1024**2:
            raise ValueError('Host custody reserve plus uncompressed upper bound unavailable')
        CONTEXT.mkdir(mode=0o700);fsync_directory(parent)
        state={'version':1,'state':'export-intended','candidate_container_id':identity,
            'guest_helper_sha256':digest(ROOT/'scripts/build/phase2/h10_selected_tar_custody.py'),
            'host_producer_sha256':digest(Path(__file__)),
            'scope':'One opaque historical H10 selected-root.tar only; all evidence/logs/ISOs/backings and Phase2 caches retained'}
        save(state)
        partial=CONTEXT/'selected-root.tar.gz.part';archive=CONTEXT/'selected-root.tar.gz'
        with (CONTEXT/'export.log').open('xb') as log:
            process=subprocess.Popen(command('export'),stdout=subprocess.PIPE,stderr=log)
            try:
                expected=stream_compress(process.stdout,partial)
                code=process.wait(timeout=60)
                if code:raise ValueError('Guest H10 export failed; retain partial host custody')
            finally:
                process.stdout.close()
                if process.poll() is None:process.terminate();process.wait(timeout=30)
                log.flush();os.fsync(log.fileno())
        partial.replace(archive);fsync_directory(CONTEXT)
        owned_guest(identity);guest=guest_receipt()
        if (guest.get('state')!='exported' or guest.get('bytes')!=SIZE or guest.get('sha256')!=expected['sha256'] or
                guest.get('producer_sha256')!=state['guest_helper_sha256']):
            raise ValueError('Guest/host original H10 stream custody differs')
        with (CONTEXT/'guest-export.json').open('x') as stream:
            stream.write(encoded(guest).decode()+'\n');stream.flush();os.fsync(stream.fileno())
        proof=verify_decompression(archive,expected)
        state.update(state='complete-decompression-verified',host_archive=str(archive),
            host_proof=proof,guest_export_sha256=digest(CONTEXT/'guest-export.json'),
            recovery_metadata=guest['source_metadata'],archive_extraction_performed=False,
            root_payload_executed=False)
        save(state)
        # Retain the exact immutable bytes whose hash authorizes retirement;
        # later result-state updates must not erase this proof artifact.
        verified=CONTEXT/'host-verified.json'
        with verified.open('xb') as stream:
            os.fchmod(stream.fileno(),0o600);stream.write((CONTEXT/'result.json').read_bytes())
            stream.flush();os.fsync(stream.fileno())
        fsync_directory(CONTEXT)
        proof={**proof,'host_receipt_sha256':digest(verified)}
        if digest(archive)!=proof['compressed_sha256']:raise ValueError('Private host gzip changed before retirement')
        # Only after archive+receipt fsync and the full decompression proof.
        owned_guest(identity)
        result=subprocess.run(command('retire'),input=encoded(proof),stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,check=True,timeout=600)
        if len(result.stdout)>256*1024:raise ValueError('Guest retirement receipt size')
        retired=json.loads(result.stdout)
        if retired.get('state')!='complete' or retired.get('sha256')!=expected['sha256'] or retired.get('retired_bytes')!=SIZE:
            raise ValueError('Guest H10 retirement outcome requires reconciliation')
        owned_guest(identity)
        with (CONTEXT/'guest-retired.json').open('x') as stream:
            stream.write(encoded(retired).decode()+'\n');stream.flush();os.fsync(stream.fileno())
        state.update(state='complete',host_verified_sha256=digest(verified),guest_retirement_sha256=digest(CONTEXT/'guest-retired.json'),
            measured_guest_reclaimed_bytes=retired['measured_reclaimed_bytes'])
        save(state)
        print(json.dumps({'state':'complete','host_archive':str(archive),
            'compressed_sha256':proof['compressed_sha256'],
            'measured_guest_reclaimed_bytes':retired['measured_reclaimed_bytes']},sort_keys=True))


if __name__=='__main__':main()
