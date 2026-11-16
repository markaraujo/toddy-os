"""UID101-only FAT32 consumer; creates one NEW regular sparse file, never a disk."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import struct
import subprocess

SIZE=128*1024**2


def inspect_boot(boot,size):
    if len(boot)!=512 or boot[510:512]!=b'\x55\xaa' or boot[82:90]!=b'FAT32   ' or boot[71:82]!=b'TODDYTEST  ':raise ValueError('Actual FAT32 BPB/label missing')
    sector=struct.unpack_from('<H',boot,11)[0];cluster=boot[13];reserved=struct.unpack_from('<H',boot,14)[0];fats=boot[16]
    sectors=struct.unpack_from('<I',boot,32)[0];fat_size=struct.unpack_from('<I',boot,36)[0]
    if sector!=512 or cluster==0 or cluster&(cluster-1) or reserved<2 or fats!=2 or sectors*sector!=size or not fat_size or struct.unpack_from('<H',boot,17)[0] or struct.unpack_from('<H',boot,22)[0]:raise ValueError('FAT32 geometry differs')
    clusters=(sectors-reserved-fats*fat_size)//cluster
    if not 65525<=clusters<0xffffff5:raise ValueError('Not a FAT32 cluster geometry')
    return {'bytes_per_sector':sector,'sectors_per_cluster':cluster,'sectors':sectors,'clusters':clusters,'label':'TODDYTEST'}


def probe(directory,tools):
    if os.getuid()!=101 or os.geteuid()!=101:raise ValueError('Fixed unprivileged native tester required')
    directory=Path(directory);tools=Path(tools)
    if str(tools) not in ('/stage/usr/sbin','/usr/sbin') or directory.resolve()!=directory or not directory.is_dir() or directory.stat().st_uid!=101 or directory.stat().st_mode&0o022:raise ValueError('Private canonical native file-test directory required')
    for name in ('mkfs.fat','fsck.fat','fatlabel'):
        path=tools/name
        if not path.is_file() or path.is_symlink():raise ValueError('Fixed regular native tool required')
    path=directory/'fat32-native-probe.img'
    fd=os.open(path,os.O_RDWR|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|os.O_CLOEXEC,0o600)
    try:
        before=os.fstat(fd)
        if not stat.S_ISREG(before.st_mode) or before.st_nlink!=1:raise ValueError('Regular private sparse file required')
        os.ftruncate(fd,SIZE)
        if os.fstat(fd).st_blocks*512>=1024**2:raise ValueError('Sparse-file support required')
        # The child receives ONLY this verified regular file descriptor. It can
        # never be redirected to a caller-provided disk path by a pathname race.
        operand='/proc/self/fd/'+str(fd)
        def run(name,*args):
            result=subprocess.run([str(tools/name),*args,operand],pass_fds=(fd,),capture_output=True,text=True,timeout=30)
            if result.returncode!=0:raise ValueError('Native regular-file '+name+' failed: '+str(result.returncode))
            return result.stdout
        run('mkfs.fat','--invariant','-F','32','-n','TODDYTEST')
        info=os.fstat(fd);boot=os.pread(fd,512,0);geometry=inspect_boot(boot,SIZE)
        if info.st_dev!=before.st_dev or info.st_ino!=before.st_ino or info.st_size!=SIZE or info.st_blocks*512>=16*1024**2:raise ValueError('Sparse regular-file identity changed')
        fsinfo=struct.unpack_from('<H',boot,48)[0];backup=struct.unpack_from('<H',boot,50)[0]
        data=os.pread(fd,512,fsinfo*512)
        if data[:4]!=b'RRaA' or data[484:488]!=b'rrAa' or data[508:512]!=b'\0\0\x55\xaa' or os.pread(fd,512,backup*512)!=boot:raise ValueError('FAT32 FSInfo/backup boot readback failed')
        def digest():
            os.lseek(fd,0,os.SEEK_SET)
            with os.fdopen(os.dup(fd),'rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
        checksum=digest();run('fsck.fat','-n','-v')
        if run('fatlabel').strip()!='TODDYTEST' or digest()!=checksum:raise ValueError('Read-only fsck/label readback changed image')
        return {'uid':101,'regular_file_only':True,'raw_or_loop_device_used':False,'logical_bytes':SIZE,'allocated_bytes':info.st_blocks*512,'image_sha256':checksum,'mkfs_exit':0,'fsck_exit':0,'fatlabel_exit':0,'readonly_check_preserved_bytes':True,'geometry':geometry}
    finally:os.close(fd)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--directory',required=True,type=Path);parser.add_argument('--tools',required=True,type=Path)
    args=parser.parse_args();print(json.dumps(probe(args.directory,args.tools),sort_keys=True))
