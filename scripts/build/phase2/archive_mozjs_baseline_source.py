"""Archive/restore-verify the inactive baseline Mozilla source before one controlled retirement."""
import fcntl
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from run_step import snapshot as installed_snapshot
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'h10'))
from copy_selected_root import snapshot,tree_names

SOURCE=Path('/mnt/lfs/sources/phase2/inputs/mozjs-tool-140.14.0')
CONTEXT=Path('/var/lib/toddy/phase2-custody/mozjs-baseline-source-1')
RECEIPT=Path('/var/log/toddy/phase2/mozjs-baseline-source-custody-1.json')
TAR_ENV={'PATH':'/usr/bin:/bin','LC_ALL':'C.UTF-8','HOME':'/root'}


def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def save(path,data):
    part=path.with_suffix(path.suffix+'.part');assert not part.exists()
    with part.open('x') as f:os.fchmod(f.fileno(),0o600);json.dump(data,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
    part.replace(path)
    fd=os.open(path.parent,os.O_RDONLY|os.O_DIRECTORY)
    try:os.fsync(fd)
    finally:os.close(fd)


def main():
    assert os.geteuid()==0 and socket.gethostname()=='toddy-builder'
    subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
    assert subprocess.check_output(['findmnt','-n','-o','SOURCE','/'],text=True).strip()=='/dev/vda1'
    assert subprocess.check_output(['lsblk','-dnro','SERIAL','/dev/vda'],text=True).strip()=='TODDY-BUILDER'
    lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
    assert not RECEIPT.exists() and not CONTEXT.exists(),'Reconcile actual existing archive/extraction/retirement; never replay'
    assert SOURCE.resolve()==SOURCE and SOURCE.is_dir() and not SOURCE.is_symlink() and not (SOURCE/'.toddy-retired.json').exists()
    mounts=[Path(p) for p in subprocess.check_output(['findmnt','-rn','-o','TARGET'],text=True).splitlines()]
    assert not any(p==SOURCE or p.is_relative_to(SOURCE) for p in mounts)
    version=subprocess.check_output(['/usr/bin/tar','--version'],env=TAR_ENV,text=True).splitlines()[0];assert version=='tar (GNU tar) 1.35'
    assert subprocess.check_output(['chroot','/mnt/lfs','dpkg-query','-W','-f=${Status} ${Version}','mozjs'],text=True)=='install ok installed 140.17.0-1+toddy1'
    assert subprocess.check_output(['chroot','/mnt/lfs','js140','-e','print(42)'],text=True).strip()=='42'
    prepared=json.loads((SOURCE/'toddy-prepared.json').read_text());assert prepared['sources'][0]['name']=='mozjs' and prepared['sources'][0]['version']=='140.14.0' and prepared['sources'][0]['sha256']=='28006bd454e703932e1ea804918165774a1e21478b18e551cd1b38111d664239'
    for row in prepared['sources']:
        assert sha(Path('/mnt/lfs/sources')/row['filename'])==row['sha256']
    assert shutil.disk_usage('/mnt/lfs').free>=16*1024**3
    CONTEXT.parent.mkdir(mode=0o700,parents=True,exist_ok=True);assert CONTEXT.parent.resolve()==CONTEXT.parent and CONTEXT.parent.stat().st_uid==0 and not CONTEXT.parent.stat().st_mode&0o022
    CONTEXT.mkdir(mode=0o700)
    state={'scope':'Inactive Mozilla140.14 baseline expanded source only. Full archive and actual tmpfs restoration compare bytes/metadata/hardlinks before retirement. Current140.17 source/compiler/tests/stages/owned runtime, baseline build/tests, all compressed archives retained. No OS recovery or desktop claim.','state':'snapshotting','pid':os.getpid(),'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'proc_start_ticks':Path('/proc/self/stat').read_text().split()[21],'producer_sha256':sha(Path(__file__)),'source':str(SOURCE),'source_inode':SOURCE.stat().st_ino,'source_uid':SOURCE.stat().st_uid,'source_gid':SOURCE.stat().st_gid,'source_mode':SOURCE.stat().st_mode,'before_target_free':shutil.disk_usage('/mnt/lfs').free,'before_builder_free':shutil.disk_usage('/').free,'tar':{'version':version,'sha256':sha(Path('/usr/bin/tar'))}}
    save(RECEIPT,state)
    try:
        before=installed_snapshot();save(CONTEXT/'installed-before.json',before)
        expected=snapshot(SOURCE,tree_names(SOURCE));save(CONTEXT/'source-manifest.json',expected)
        unique={}
        for n,r in expected['entries'].items():
            if 'sha256' in r:
                st=(SOURCE/n).stat();unique[(st.st_dev,st.st_ino)]=st.st_size
        logical=sum(unique.values());assert logical<5*1024**3 and shutil.disk_usage('/').free>=2*1024**3
        archive=CONTEXT/'work.tar.gz';state.update(state='archiving',entries=len(expected['entries']),hardlink_groups=len(expected['hardlink_groups']),unique_regular_bytes=logical,archive=str(archive));save(RECEIPT,state)
        command=['/usr/bin/tar','--create','--file=-','--format=pax','--acls','--xattrs','--xattrs-include=*','--numeric-owner','--sparse','--directory='+str(SOURCE),'.']
        with (CONTEXT/'create.log').open('xb') as errors:
            process=subprocess.Popen(command,env=TAR_ENV,stdout=subprocess.PIPE,stderr=errors)
            try:
                with archive.open('xb') as raw:
                    os.fchmod(raw.fileno(),0o600)
                    class Bounded:
                        def write(self,data):
                            assert raw.tell()+len(data)<=1024**3,'Archive budget reached; preserve original and partial artifact'
                            assert shutil.disk_usage('/').free>=1024**3+len(data),'Preserve restoration capacity'
                            return raw.write(data)
                        def flush(self):raw.flush()
                    with gzip.GzipFile(fileobj=Bounded(),mode='wb',filename='',mtime=0,compresslevel=6) as packed:
                        while block:=process.stdout.read(8*1024**2):packed.write(block)
                    raw.flush();os.fsync(raw.fileno())
                code=process.wait();state['archive_create_exit']=code;assert code==0,'Original source/archive changed or tar failed'
            finally:
                process.stdout.close()
                if process.poll() is None:process.terminate();process.wait()
        assert snapshot(SOURCE,tree_names(SOURCE))==expected,'Source cache changed during archive creation'
        state.update(state='extracting',archive_sha256=sha(archive),archive_bytes=archive.stat().st_size);save(RECEIPT,state)
        memory=CONTEXT/'restore-memory';memory.mkdir(mode=0o700)
        available=int(next(line.split()[1] for line in Path('/proc/meminfo').read_text().splitlines() if line.startswith('MemAvailable:')))*1024
        assert available>=logical+4*1024**3,'Preserve guest memory; original source remains'
        state.update(state='mounting-restore-memory',memory=str(memory));save(RECEIPT,state)
        subprocess.run(['mount','-t','tmpfs','-o','size=6G,noswap,nosuid,nodev,noexec,mode=0700','tmpfs',str(memory)],check=True)
        assert subprocess.check_output(['findmnt','-n','-o','FSTYPE','--mountpoint',str(memory)],text=True).strip()=='tmpfs'
        restored=memory/'restored';restored.mkdir(mode=0o700)
        with (CONTEXT/'extract.log').open('xb') as log:
            r=subprocess.run(['/usr/bin/tar','--extract','--gzip','--file='+str(archive),'--directory='+str(restored),'--acls','--xattrs','--xattrs-include=*','--numeric-owner','--same-owner','--same-permissions','--delay-directory-restore'],env=TAR_ENV,stdout=log,stderr=subprocess.STDOUT)
        state['archive_extract_exit']=r.returncode;assert r.returncode==0
        actual=snapshot(restored,tree_names(restored));save(CONTEXT/'restored-manifest.json',actual)
        assert actual==expected,'Actual recovery bytes/metadata/hardlinks differ; preserve original'
        assert snapshot(SOURCE,tree_names(SOURCE))==expected and SOURCE.stat().st_ino==state['source_inode']
        assert sha(archive)==state['archive_sha256']
        state.update(state='restore-verified',source_unchanged=True,restored_exact=True,manifest_sha256=sha(CONTEXT/'source-manifest.json'));save(RECEIPT,state)
        # Both copies were fully compared; retire source children while retaining
        # a clear marker at the exact work path. Never touch installed SDK paths.
        state['state']='retiring-inactive-baseline-source';save(RECEIPT,state)
        for p in list(SOURCE.iterdir()):
            if p.is_dir() and not p.is_symlink():shutil.rmtree(p)
            else:p.unlink()
        (SOURCE/'.toddy-retired.json').write_text(json.dumps({'receipt':str(RECEIPT),'archive':str(archive),'archive_sha256':state['archive_sha256'],'source_manifest_sha256':state['manifest_sha256']},indent=2)+'\n')
        assert {p.name for p in SOURCE.iterdir()}=={'.toddy-retired.json'}
        assert installed_snapshot()==before,'Installed root changed; preserve recovery artifact and diagnose'
        state.update(state='retired-verified-cache',installed_root_changed_paths=0,after_target_free=shutil.disk_usage('/mnt/lfs').free);save(RECEIPT,state)
        shutil.rmtree(restored);assert not restored.exists() and sha(archive)==state['archive_sha256']
        subprocess.run(['umount',str(memory)],check=True);memory.rmdir()
        state.update(state='complete',after_builder_free=shutil.disk_usage('/').free);state['reclaimed_target_bytes']=state['after_target_free']-state['before_target_free'];state['recovery']='Verify archive/source-manifest SHA. Restore to a NEW private directory using recorded GNU tar PAX ACL/xattr/owner/permission flags; compare full snapshot and hardlink groups with source-manifest. To restore original work, first reconcile sole .toddy-retired marker/receipt, never overwrite an existing/unknown work tree. Keep archive/manifests/logs; current source/build/installed Mozilla remain available without rebuilding.';save(RECEIPT,state);print(json.dumps({k:state[k] for k in ['state','entries','hardlink_groups','archive_bytes','reclaimed_target_bytes','installed_root_changed_paths']}),flush=True)
    except BaseException as error:
        state.update(state='failed-preserved',error={'type':type(error).__name__,'message':str(error)});save(RECEIPT,state);raise

if __name__=='__main__':main()
